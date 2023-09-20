import logging
from typing import Type

import boto3
from botocore.client import Config
from celery.result import AsyncResult
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import ProtectedError
from django.db.transaction import atomic
from django.http import Http404
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import UpdateView
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import FormMixin
from django.views.generic.edit import FormView
from django.views.generic.list import ListView

from checks.models import TrackedModelCheck
from common.filters import TamatoFilter
from common.models import TrackedModel
from common.pagination import build_pagination_list
from common.views import SortingMixin
from common.views import TamatoListView
from common.views import WithPaginationListView
from exporter.models import Upload
from importer.goods_report import GoodsReporter
from importer.goods_report import GoodsReportLine
from measures.filters import MeasureFilter
from measures.models import Measure
from notifications.models import Notification
from notifications.models import NotificationTypeChoices
from workbaskets import forms
from workbaskets.models import DataRow
from workbaskets.models import DataUpload
from workbaskets.models import WorkBasket
from workbaskets.session_store import SessionStore
from workbaskets.tasks import call_check_workbasket_sync
from workbaskets.validators import WorkflowStatus
from workbaskets.views.decorators import require_current_workbasket
from workbaskets.views.mixins import WithCurrentWorkBasket

logger = logging.getLogger(__name__)


class WorkBasketFilter(TamatoFilter):
    search_fields = (
        "id",
        "author",
        "reason",
        "title",
    )
    clear_url = reverse_lazy("workbaskets:workbasket-ui-list-all")

    class Meta:
        model = WorkBasket
        fields = ["search", "status"]


class WorkBasketConfirmCreate(DetailView):
    template_name = "workbaskets/confirm_create.jinja"
    model = WorkBasket
    queryset = WorkBasket.objects.all()


class WorkBasketCreate(PermissionRequiredMixin, CreateView):
    """UI endpoint for creating workbaskets."""

    permission_required = "workbaskets.add_workbasket"
    template_name = "workbaskets/create.jinja"
    form_class = forms.WorkbasketCreateForm

    def form_valid(self, form):
        if not self.request.user.is_authenticated:
            return redirect(reverse("login"))
        user = get_user_model().objects.get(username=self.request.user.username)
        self.object = form.save(commit=False)
        self.object.author = user
        self.object.save()
        self.object.save_to_session(self.request.session)
        return redirect(
            reverse(
                "workbaskets:workbasket-ui-confirm-create",
                kwargs={"pk": self.object.pk},
            ),
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class WorkBasketUpdate(PermissionRequiredMixin, UpdateView):
    """UI endpoint for updating a workbasket's title and description."""

    permission_required = "workbaskets.add_workbasket"
    template_name = "workbaskets/edit-details.jinja"
    form_class = forms.WorkbasketUpdateForm
    model = WorkBasket

    def get_success_url(self):
        return reverse(
            "workbaskets:workbasket-ui-confirm-update",
            kwargs={"pk": self.object.pk},
        )


class WorkBasketConfirmUpdate(DetailView):
    template_name = "workbaskets/confirm_update.jinja"
    model = WorkBasket


class SelectWorkbasketView(PermissionRequiredMixin, WithPaginationListView):
    """UI endpoint for viewing and filtering workbaskets."""

    filterset_class = WorkBasketFilter
    template_name = "workbaskets/select-workbasket.jinja"
    permission_required = "workbaskets.change_workbasket"

    def get_queryset(self):
        return (
            WorkBasket.objects.exclude(status=WorkflowStatus.PUBLISHED)
            .exclude(status=WorkflowStatus.ARCHIVED)
            .exclude(status=WorkflowStatus.QUEUED)
            .exclude_importing_imports()
            .exclude_failed_imports()
            .order_by("-updated_at")
        )

    def post(self, request, *args, **kwargs):
        workbasket_pk = request.POST.get("workbasket")
        workbasket_tab = request.POST.get("workbasket-tab")

        workbasket_tab_map = {
            "view-summary": {
                "path_name": "workbaskets:current-workbasket",
            },
            "add-edit-items": {
                "path_name": "workbaskets:edit-workbasket",
            },
            "view-violations": {
                "path_name": "workbaskets:workbasket-ui-violations",
            },
            "review-measures": {
                "path_name": "workbaskets:review-workbasket",
            },
            "review-goods": {
                "path_name": "workbaskets:workbasket-ui-review-goods",
            },
        }

        workbasket = WorkBasket.objects.get(pk=workbasket_pk) if workbasket_pk else None

        if workbasket:
            if workbasket.status == WorkflowStatus.ERRORED:
                workbasket.restore()
                workbasket.save()

            workbasket.save_to_session(request.session)

            if workbasket_tab:
                view = workbasket_tab_map[workbasket_tab]
                return redirect(reverse(view["path_name"]))
            else:
                return redirect(reverse("workbaskets:current-workbasket"))

        return redirect(reverse("workbaskets:workbasket-ui-list"))


class WorkBasketDeleteChanges(PermissionRequiredMixin, ListView):
    """UI for user review of WorkBasket item deletion."""

    template_name = "workbaskets/delete_changes.jinja"
    permission_required = "workbaskets.change_workbasket"

    @property
    def workbasket(self) -> WorkBasket:
        return WorkBasket.current(self.request)

    def _session_store(self, workbasket):
        """Get the current user's SessionStore for the WorkBasket that they're
        deleting, containing ids of the items that have been selected for
        deletion."""

        return SessionStore(
            self.request,
            f"WORKBASKET_SELECTIONS_{workbasket.pk}",
        )

    def get_queryset(self):
        """Get TrackedModelQuerySet of instances that are candidates for
        deletion."""

        store = self._session_store(self.workbasket)
        pks = [
            forms.SelectableObjectsForm.object_id_from_field_name(k)
            for k in store.data.keys()
        ]
        return self.workbasket.tracked_models.filter(pk__in=pks)

    def post(self, request, *args, **kwargs):
        if request.POST.get("action", None) != "delete":
            # The user has cancelled out of the deletion process.
            return redirect("workbaskets:current-workbasket")

        # By reverse ordering on record_code + subrecord_code we're able to
        # delete child entities first, avoiding protected foreign key
        # violations.
        object_list = self.get_queryset().record_ordering().reverse()

        for obj in object_list:
            # Unlike situations where TrackedModels are superceded and are
            # subject to UpdateType.DELETE, WorkBasket item deletion really
            # should remove rows from the DB.
            try:
                obj.delete()
            except ProtectedError:
                # TODO Capture deletion failure and present back to UI.
                # UI component(s) design in the backlog for this: TP-1148.
                pass

        # Removing TrackedModel instances from the workbasket may result in
        # empty Transaction instances, so remove those from the workbasket too.
        self.workbasket.purge_empty_transactions()

        session_store = self._session_store(self.workbasket)
        session_store.clear()

        redirect_url = reverse(
            "workbaskets:workbasket-ui-delete-changes-done",
        )
        return redirect(redirect_url)


class WorkBasketDeleteChangesDone(TemplateView):
    template_name = "workbaskets/delete_changes_confirm.jinja"


def download_envelope(request):
    """
    Creates s3 resource using AWS environment variables.

    Tries to get filename from most recent s3 upload. If no upload exists,
    returns 404.

    Generates presigned url from s3 client using bucket and file names.

    Returns `HttpResponseRedirect` with presigned url passed as only argument.
    """
    s3 = boto3.resource(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
    )

    try:
        last_added = (
            settings.HMRC_STORAGE_DIRECTORY
            + Upload.objects.latest("created_date").filename
        )
    except Upload.DoesNotExist as err:
        raise Http404("No uploaded envelope available for download")

    url = s3.meta.client.generate_presigned_url(
        ClientMethod="get_object",
        ExpiresIn=3600,
        Params={
            "Bucket": settings.HMRC_STORAGE_BUCKET_NAME,
            "Key": last_added,
        },
    )

    return HttpResponseRedirect(url)


@method_decorator(require_current_workbasket, name="dispatch")
class ReviewMeasuresWorkbasketView(PermissionRequiredMixin, TamatoListView):
    model: Type[TrackedModel] = Measure
    paginate_by = 30

    @property
    def workbasket(self) -> WorkBasket:
        return WorkBasket.current(self.request)

    def get_queryset(self):
        return Measure.objects.filter(
            transaction__workbasket=self.workbasket,
        ).order_by("sid")

    template_name = "workbaskets/review-workbasket.jinja"
    permission_required = "workbaskets.change_workbasket"
    filterset_class = MeasureFilter


@method_decorator(require_current_workbasket, name="dispatch")
class WorkbasketReviewGoodsView(WithCurrentWorkBasket, TemplateView):
    """UI endpoint for reviewing goods changes in a workbasket."""

    template_name = "workbaskets/review-goods.jinja"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # Default values should there be no ImportBatch instance associated with
        # the workbasket.
        context["column_headings"] = [
            description
            for description in GoodsReportLine.COLUMN_DESCRIPTIONS
            if description != "Containing transaction ID"
            and description != "Containing message ID"
        ]
        context["report_lines"] = []
        context["import_batch_pk"] = None

        # Get actual values from the ImportBatch instance if one is associated
        # with the workbasket.
        try:
            import_batch = self.workbasket.importbatch
        except ObjectDoesNotExist:
            import_batch = None

        if import_batch and import_batch.taric_file:
            reporter = GoodsReporter(import_batch.taric_file)
            goods_report = reporter.create_report()

            context["report_lines"] = [
                [
                    line.update_type.title(),
                    line.record_name.title(),
                    line.goods_nomenclature_item_id,
                    line.suffix,
                    line.validity_start_date,
                    line.validity_end_date,
                    line.comments,
                ]
                for line in goods_report.report_lines
            ]
            context["import_batch_pk"] = import_batch.pk

            # notifications only relevant to a goods import
            context["unsent_notification"] = (
                import_batch.goods_import
                and not Notification.objects.filter(
                    notified_object_pk=import_batch.pk,
                    notification_type=NotificationTypeChoices.GOODS_REPORT,
                ).exists()
            )

        return context


@method_decorator(require_current_workbasket, name="dispatch")
class EditWorkbasketView(PermissionRequiredMixin, TemplateView):
    template_name = "workbaskets/edit-workbasket.jinja"
    permission_required = "workbaskets.change_workbasket"


@method_decorator(require_current_workbasket, name="dispatch")
class CurrentWorkBasket(FormView):
    template_name = "workbaskets/summary-workbasket.jinja"
    form_class = forms.SelectableObjectsForm

    # Form action mappings to URL names.
    action_success_url_names = {
        "submit-for-packaging": "publishing:packaged-workbasket-queue-ui-create",
        "run-business-rules": "workbaskets:current-workbasket",
        "terminate-rule-check": "workbaskets:current-workbasket",
        "remove-selected": "workbaskets:workbasket-ui-delete-changes",
        "remove-all": "workbaskets:workbasket-ui-delete-changes",
        "page-prev": "workbaskets:current-workbasket",
        "page-next": "workbaskets:current-workbasket",
        "compare-data": "workbaskets:current-workbasket",
    }

    @property
    def workbasket(self) -> WorkBasket:
        return WorkBasket.current(self.request)

    @property
    def paginator(self):
        return Paginator(self.workbasket.tracked_models, per_page=50)

    @property
    def latest_upload(self):
        return Upload.objects.order_by("created_date").last()

    @property
    def uploaded_envelope_dates(self):
        """Gets a list of all transactions from the `latest_approved_workbasket`
        in the order they were updated and returns a dict with the first and
        last transactions as values for "start" and "end" keys respectively."""
        if self.latest_upload:
            transactions = self.latest_upload.envelope.transactions.order_by(
                "updated_at",
            )
            return {
                "start": transactions.first().updated_at,
                "end": transactions.last().updated_at,
            }
        return None

    def _append_url_page_param(self, url, form_action):
        """Based upon 'form_action', append a 'page' URL parameter to the given
        url param and return the result."""
        page = self.paginator.get_page(self.request.GET.get("page", 1))
        page_number = 1
        if form_action == "page-prev":
            page_number = page.previous_page_number()
        elif form_action == "page-next":
            page_number = page.next_page_number()
        return f"{url}?page={page_number}"

    @atomic
    def run_business_rules(self):
        """Remove old checks, start new checks via a Celery task and save the
        newly created task's ID on the workbasket."""
        workbasket = self.workbasket
        workbasket.delete_checks()
        task = call_check_workbasket_sync.apply_async(
            (workbasket.pk,),
            countdown=1,
        )
        logger.info(
            f"Started rule check against workbasket.id={workbasket.pk} "
            f"on task.id={task.id}",
        )
        workbasket.rule_check_task_id = task.id
        workbasket.save()

    def get_success_url(self):
        form_action = self.request.POST.get("form-action")
        if form_action == "run-business-rules":
            self.run_business_rules()
        elif form_action == "terminate-rule-check":
            self.workbasket.terminate_rule_check()
        try:
            return self._append_url_page_param(
                reverse(
                    self.action_success_url_names[form_action],
                ),
                form_action,
            )
        except KeyError:
            return reverse("home")

    def get_initial(self):
        store = SessionStore(
            self.request,
            f"WORKBASKET_SELECTIONS_{self.workbasket.pk}",
        )
        return store.data.copy()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        page = self.paginator.get_page(self.request.GET.get("page", 1))
        kwargs["objects"] = page.object_list
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = self.paginator.get_page(self.request.GET.get("page", 1))
        user_can_delete_workbasket = (
            self.request.user.is_superuser
            or self.request.user.has_perm("workbaskets.delete_workbasket")
        )
        # set to true if there is an associated goods import batch with an unsent notification
        try:
            import_batch = self.workbasket.importbatch
            unsent_notifcation = (
                import_batch
                and import_batch.goods_import
                and not Notification.objects.filter(
                    notified_object_pk=import_batch.pk,
                    notification_type=NotificationTypeChoices.GOODS_REPORT,
                ).exists()
            )
        except ObjectDoesNotExist:
            unsent_notifcation = False
        context.update(
            {
                "workbasket": self.workbasket,
                "page_obj": page,
                "uploaded_envelope_dates": self.uploaded_envelope_dates,
                "rule_check_in_progress": False,
                "user_can_delete_workbasket": user_can_delete_workbasket,
                "unsent_notification": unsent_notifcation,
            },
        )
        if self.workbasket.rule_check_task_id:
            result = AsyncResult(self.workbasket.rule_check_task_id)
            if result.status != "SUCCESS":
                context.update({"rule_check_in_progress": True})
            else:
                self.workbasket.save_to_session(self.request.session)

            num_completed, total = self.workbasket.rule_check_progress()
            context.update(
                {
                    "rule_check_progress": f"Completed {num_completed} out of {total} checks",
                },
            )

        return context

    def form_valid(self, form):
        store = SessionStore(
            self.request,
            f"WORKBASKET_SELECTIONS_{self.workbasket.pk}",
        )
        form_action = self.request.POST.get("form-action")
        store.remove_items(form.cleaned_data)
        if form_action == "remove-all":
            object_list = {
                self.form_class.field_name_for_object(obj): True
                for obj in self.workbasket.tracked_models
            }
            store.add_items(object_list)
        else:
            to_add = {key: value for key, value in form.cleaned_data.items() if value}
            store.add_items(to_add)
        return super().form_valid(form)


class WorkBasketList(PermissionRequiredMixin, WithPaginationListView):
    """UI endpoint for viewing and filtering workbaskets."""

    template_name = "workbaskets/list.jinja"
    permission_required = "workbaskets.change_workbasket"
    filterset_class = WorkBasketFilter
    search_fields = [
        "title",
        "reason",
    ]

    def get_queryset(self):
        return WorkBasket.objects.order_by("-updated_at")


class WorkBasketChanges(PermissionRequiredMixin, DetailView):
    """UI endpoint for viewing a specified workbasket."""

    model = WorkBasket
    template_name = "workbaskets/detail.jinja"
    permission_required = "workbaskets.change_workbasket"
    paginate_by = 50

    def get_context_data(self, **kwargs):
        """
        Although this is a detail view of a WorkBasket instance, it provides a
        view of its contained items (TrackedModel instances) as a paged list.

        A paginator and related objects are therefore added to page context.
        """
        items = self.get_object().tracked_models.all()
        paginator = Paginator(items, WorkBasketChanges.paginate_by)
        try:
            page_number = int(self.request.GET.get("page", 1))
        except ValueError:
            page_number = 1
        page_obj = paginator.get_page(page_number)
        context = super().get_context_data(**kwargs)
        context["paginator"] = paginator
        context["page_obj"] = page_obj
        context["is_paginated"] = True
        context["object_list"] = items
        context["page_links"] = build_pagination_list(
            page_number,
            page_obj.paginator.num_pages,
        )

        return context


class WorkBasketViolations(SortingMixin, WithPaginationListView):
    """UI endpoint for viewing a specified workbasket's business rule
    violations."""

    model = TrackedModelCheck
    template_name = "workbaskets/violations.jinja"
    paginate_by = 50
    sort_by_fields = ["model", "date", "check_name"]
    custom_sorting = {
        "date": "transaction_check__transaction__created_at",
        "model": "model__polymorphic_ctype",
    }

    @property
    def workbasket(self) -> WorkBasket:
        return WorkBasket.current(self.request)

    def get_context_data(self, **kwargs):
        return super().get_context_data(workbasket=self.workbasket, **kwargs)

    def get_queryset(self):
        self.queryset = TrackedModelCheck.objects.filter(
            transaction_check__transaction__workbasket=self.workbasket,
            successful=False,
        )
        return super().get_queryset()


class WorkBasketViolationDetail(DetailView):
    """UI endpoint for viewing a specified workbasket's business rule
    violations."""

    model = TrackedModelCheck
    template_name = "workbaskets/violation_detail.jinja"

    @property
    def workbasket(self) -> WorkBasket:
        return WorkBasket.current(self.request)

    def get_context_data(self, **kwargs):
        return super().get_context_data(workbasket=self.workbasket, **kwargs)

    def override_violation(self):
        """
        Override the `TrackedModelCheck` instance for this rules check
        violation, setting its `successful` value to True.

        If there are no other failing `TrackedModelCheck` instances on the
        associated `TransactionCheck` instance, then also set its `successful`
        value to True.
        """
        model_check = self.get_object()
        model_check.successful = True
        model_check.save()

        transaction_check = model_check.transaction_check
        # Only clear the associated transcation check if model_check
        # was the last and only other failing model check.
        other_model_checks = transaction_check.model_checks.filter(successful=False)
        if not other_model_checks:
            transaction_check.successful = True
            transaction_check.save()

    def post(self, request, *args, **kwargs):
        if request.POST.get("action", None) == "delete" and request.user.is_superuser:
            self.override_violation()

        return redirect("workbaskets:workbasket-ui-violations")


class WorkBasketDelete(PermissionRequiredMixin, FormMixin, DeleteView):
    """
    UI to confirm (or cancel) workbasket deletion.

    Rather than using the current workbasket to identify the target workbasket
    for deletion, it is identified by its primary key as a URL captured param.
    This reduces the chances of deleting the wrong workbasket.
    """

    form_class = forms.WorkbasketDeleteForm
    model = WorkBasket
    permission_required = "workbaskets.delete_workbasket"
    template_name = "workbaskets/delete_workbasket.jinja"

    def get_success_url(self) -> str:
        return reverse(
            "workbaskets:workbasket-ui-delete-done",
            kwargs={"deleted_pk": self.kwargs["pk"]},
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_object()
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object.delete()
        return redirect(self.get_success_url())


class WorkBasketDeleteDone(TemplateView):
    """
    UI presented after successfully deleting a workbasket.

    The deleted workbasket's primary key is identified via the `deleted_pk`
    captured param, distinguishing it from the typical `pk` identifier - since
    the object has been deleted and the PK therefore no longer exists.
    """

    template_name = "workbaskets/delete_workbasket_done.jinja"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["deleted_pk"] = self.kwargs["deleted_pk"]
        return context_data


class WorkBasketCompare(WithCurrentWorkBasket, FormView):
    success_url = reverse_lazy("workbaskets:workbasket-ui-compare")
    template_name = "workbaskets/compare.jinja"
    form_class = forms.WorkbasketCompareForm

    @property
    def workbasket_measures(self):
        return self.workbasket.measures.all()

    @property
    def data_upload(self):
        try:
            return DataUpload.objects.get(workbasket=self.workbasket)
        except DataUpload.DoesNotExist:
            return None

    def form_valid(self, form):
        try:
            existing = DataUpload.objects.get(workbasket=self.workbasket)
            existing.raw_data = form.cleaned_data["raw_data"]
            existing.rows.all().delete()
            for row in form.cleaned_data["data"]:
                DataRow.objects.create(
                    valid_between=row.valid_between,
                    duty_sentence=row.duty_sentence,
                    commodity=row.commodity,
                    data_upload=existing,
                )
            existing.save()
        except DataUpload.DoesNotExist:
            data_upload = DataUpload.objects.create(
                raw_data=form.cleaned_data["raw_data"],
                workbasket=self.workbasket,
            )
            for row in form.cleaned_data["data"]:
                DataRow.objects.create(
                    valid_between=row.valid_between,
                    duty_sentence=row.duty_sentence,
                    commodity=row.commodity,
                    data_upload=data_upload,
                )
        return super().form_valid(form)

    @property
    def matching_measures(self):
        measures = []
        if self.data_upload:
            for row in self.data_upload.rows.all():
                matches = self.workbasket_measures.filter(
                    valid_between=row.valid_between,
                    goods_nomenclature__item_id=row.commodity,
                )
                duty_matches = [
                    measure
                    for measure in matches
                    if measure.duty_sentence == row.duty_sentence
                ]
                measures += duty_matches
        return measures

    def get_context_data(self, *args, **kwargs):
        return super().get_context_data(
            workbasket=self.workbasket,
            data_upload=self.data_upload,
            matching_measures=self.matching_measures,
            *args,
            **kwargs,
        )
