from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import UpdateView

from commodities.models import GoodsNomenclature
from quotas.models import QuotaOrderNumber
from reference_documents.forms.reference_document_version_forms import (
    ReferenceDocumentVersionDeleteForm,
)
from reference_documents.forms.reference_document_version_forms import (
    ReferenceDocumentVersionsCreateUpdateForm,
)
from reference_documents.models import AlignmentReportCheck, AlignmentReport, PreferentialQuotaSuspension
from reference_documents.models import PreferentialQuotaOrderNumber
from reference_documents.models import ReferenceDocument
from reference_documents.models import ReferenceDocumentVersion
from reference_documents.models import ReferenceDocumentVersionStatus
from reference_documents.tasks import run_alignment_check


class ReferenceDocumentVersionContext:
    def __init__(self, reference_document_version: ReferenceDocumentVersion, user):
        self.reference_document_version = reference_document_version
        self.user = user

    def alignment_report(self):
        return self.reference_document_version.alignment_reports.last()

    @staticmethod
    def get_tap_order_number(
            ref_doc_quota_order_number: PreferentialQuotaOrderNumber,
    ):
        if (
                ref_doc_quota_order_number.reference_document_version.entry_into_force_date
                is not None
        ):
            contains_date = (
                ref_doc_quota_order_number.reference_document_version.entry_into_force_date
            )
        else:
            contains_date = (
                ref_doc_quota_order_number.reference_document_version.published_date
            )

        quota_order_number = QuotaOrderNumber.objects.latest_approved().filter(
            order_number=ref_doc_quota_order_number.quota_order_number,
            valid_between__contains=contains_date,
        )

        if len(quota_order_number) == 0:
            return None

        return quota_order_number.first()

    @staticmethod
    def get_tap_comm_code(
            ref_doc_version: ReferenceDocumentVersion,
            comm_code: str,
    ):
        if ref_doc_version.entry_into_force_date is not None:
            contains_date = ref_doc_version.entry_into_force_date
        else:
            contains_date = ref_doc_version.published_date

        goods = GoodsNomenclature.objects.latest_approved().filter(
            item_id=comm_code,
            valid_between__contains=contains_date,
            suffix=80,
        )

        if len(goods) == 0:
            return None

        return goods.first()

    def duties_headers(self):
        return [
            {"text": "Comm Code"},
            {"text": "Duty Rate"},
            {"text": "Validity"},
            {"text": "Actions"},
        ]

    def quotas_headers(self):
        return [
            {"text": "Comm Code"},
            {"text": "Rate"},
            {"text": "Volume"},
            {"text": "Validity"},
            {"text": "Actions"},
        ]

    def suspension_headers(self):
        return [
            {"text": "Comm Code"},
            {"text": "Validity"},
            {"text": "Quota Validity"},
            {"text": "Actions"},
        ]

    def templated_quotas_headers(self):
        return [
            {"text": "Comm Code"},
            {"text": "Rate"},
            {"text": "Volume"},
            {"text": "Validity"},
        ]

    def duties_row_data(self):
        rows = []
        for (
                preferential_rate
        ) in self.reference_document_version.preferential_rates.order_by(
            "commodity_code",
        ):
            comm_code = ReferenceDocumentVersionContext.get_tap_comm_code(
                preferential_rate.reference_document_version,
                preferential_rate.commodity_code,
            )

            if comm_code:
                comm_code_link = f'<a class="govuk-link" href="{comm_code.get_url()}">{comm_code.item_id}</a>'
            else:
                comm_code_link = f"{preferential_rate.commodity_code}"

            actions = "<span></span>"

            if self.reference_document_version.editable():
                if self.user.has_perm("reference_documents.change_preferentialrate"):
                    actions += f"<a href='{reverse('reference_documents:preferential_rates_edit', args=[preferential_rate.pk])}'>Edit</a>"
                if self.user.has_perm("reference_documents.delete_preferentialrate"):
                    actions += f" | <a href='{reverse('reference_documents:preferential_rates_delete', args=[preferential_rate.pk])}'>Delete</a>"

            rows.append(
                [
                    {
                        "html": comm_code_link,
                    },
                    {
                        "text": preferential_rate.duty_rate,
                    },
                    {
                        "text": preferential_rate.valid_between,
                    },
                    {
                        "html": actions,
                    },
                ],
            )
        return rows

    def quotas_data_orders_and_rows(self):
        data = {}
        for (
                ref_doc_order_number
        ) in self.reference_document_version.preferential_quota_order_numbers.order_by(
            "quota_order_number",
        ):
            tap_quota_order_number = (
                ReferenceDocumentVersionContext.get_tap_order_number(
                    ref_doc_order_number,
                )
            )

            data[ref_doc_order_number.quota_order_number] = {
                "data_rows": [],
                "suspension_data_rows": [],
                "templated_data": {},
                "templated_suspension_data": {},
                "quota_order_number": tap_quota_order_number,
                "ref_doc_order_number": ref_doc_order_number,
                "quota_order_number_text": ref_doc_order_number.quota_order_number,
            }

            # Add the rows from the order number
            self.order_number_rows(data, ref_doc_order_number)
            self.order_number_suspension_rows(data, ref_doc_order_number)
            self.templated_order_number_rows(data, ref_doc_order_number)

        return data

    def get_quota_row(self, commodity_code: str, volume, measurement, duty_rate, valid_between, quota=None):

        comm_code = ReferenceDocumentVersionContext.get_tap_comm_code(
            self.reference_document_version,
            commodity_code,
        )
        if comm_code:
            comm_code_link = f'<a class="govuk-link" href="{comm_code.get_url()}">{comm_code.structure_code}</a>'
        else:
            comm_code_link = f"{commodity_code}"

        actions = "<span></span>"

        if self.reference_document_version.editable():
            if quota:
                if self.user.has_perm("reference_documents.change_preferentialquotaordernumber"):
                    actions += f"<a href='{reverse('reference_documents:preferential_quotas_edit', args=[quota.pk])}'>Edit</a>"
                if self.user.has_perm("reference_documents.delete_preferentialquotaordernumber"):
                    actions += f" | <a href='{reverse('reference_documents:preferential_quotas_delete', args=[quota.pk, quota.preferential_quota_order_number.reference_document_version.pk])}'>Delete</a>"

        row_to_add = [
            {
                "html": comm_code_link,
            },
            {
                "text": duty_rate,
            },
            {
                "text": f"{volume} {measurement}",
            },
            {
                "text": valid_between,
            },
            {
                "html": actions,
            },
        ]

        return row_to_add

    def get_suspension_row(self, quota, suspension, templated=False):

        commodity_code = quota.commodity_code

        comm_code = ReferenceDocumentVersionContext.get_tap_comm_code(
            self.reference_document_version,
            commodity_code,
        )
        if comm_code:
            comm_code_link = f'<a class="govuk-link" href="{comm_code.get_url()}">{comm_code.structure_code}</a>'
        else:
            comm_code_link = f"{commodity_code}"

        actions = "<span></span>"

        if self.reference_document_version.editable():
            if not templated:
                if self.user.has_perm("reference_documents.change_preferentialquotasuspension"):
                    actions += f"<a href='{reverse('reference_documents:preferential-quotas-suspension-edit', args=[suspension.pk])}'>Edit</a>"
                if self.user.has_perm("reference_documents.delete_preferentialquotasuspension"):
                    actions += f" | <a href='{reverse('reference_documents:preferential-quota-suspension-delete', args=[suspension.pk, quota.preferential_quota_order_number.reference_document_version.pk])}'>Delete</a>"

        # {"text": "Comm Code"},
        # {"text": "Validity"},
        # {"text": "Quota Validity"},
        # {"text": "Actions"},

        row_to_add = [
            {
                "html": comm_code_link,
            },
            {
                "text": suspension.valid_between,
            },
            {
                "text": quota.valid_between,
            },
            {
                "html": actions,
            },
        ]

        return row_to_add

    def order_number_rows(self, data, ref_doc_order_number):
        # Add Data Rows
        for quota in ref_doc_order_number.preferential_quotas.order_by(
                "commodity_code",
        ):
            row_to_add = self.get_quota_row(quota.commodity_code, quota.volume, quota.measurement, quota.quota_duty_rate, quota.valid_between, quota)

            data[ref_doc_order_number.quota_order_number]["data_rows"].append(
                row_to_add,
            )

    def order_number_suspension_rows(self, data, ref_doc_order_number):
        for suspension in PreferentialQuotaSuspension.objects.all().filter(
                preferential_quota__preferential_quota_order_number__quota_order_number=ref_doc_order_number
        ).order_by(
                "preferential_quota__commodity_code",
        ):
            row_to_add = self.get_suspension_row(
                suspension.preferential_quota,
                suspension,
                False
            )

            data[ref_doc_order_number.quota_order_number]["suspension_data_rows"].append(
                row_to_add,
            )

    def templated_order_number_rows(self, data, ref_doc_order_number):
        # Add templated data rows

        for quota_template in ref_doc_order_number.preferential_quota_templates.order_by("commodity_code"):

            data_to_add = {
                'data_rows': [],
                'preferential_quota_template': quota_template
            }

            if quota_template.commodity_code not in data[ref_doc_order_number.quota_order_number]["templated_data"].keys():
                data[ref_doc_order_number.quota_order_number]["templated_data"][quota_template.commodity_code] = []

            for quota in quota_template.dynamic_preferential_quotas():
                row_to_add = self.get_quota_row(quota.commodity_code, quota.volume, quota.measurement, quota.quota_duty_rate, quota.valid_between)

                data_to_add['data_rows'].append(
                    row_to_add
                )

            data[ref_doc_order_number.quota_order_number]["templated_data"][quota_template.commodity_code].append(data_to_add)


class ReferenceDocumentVersionDetails(PermissionRequiredMixin, DetailView):
    template_name = "reference_documents/reference_document_versions/details.jinja"
    permission_required = "reference_documents.view_referencedocumentversion"
    model = ReferenceDocumentVersion

    def get_context_data(self, *args, **kwargs):
        context = super(ReferenceDocumentVersionDetails, self).get_context_data(
            *args,
            **kwargs,
        )

        # title
        context["ref_doc_title"] = (
            f"Reference document for {context['object'].reference_document.get_area_name_by_area_id()}"
        )

        context_data = ReferenceDocumentVersionContext(context["object"], self.request.user)
        context["reference_document_version_duties_headers"] = (
            context_data.duties_headers()
        )
        context["reference_document_version_quotas_headers"] = (
            context_data.quotas_headers()
        )
        context["reference_document_version_suspension_headers"] = (
            context_data.suspension_headers()
        )
        context["reference_document_version_duties"] = context_data.duties_row_data()
        context["reference_document_version_quotas"] = context_data.quotas_data_orders_and_rows()
        context["reference_document_version_quotas"] = context_data.quotas_data_orders_and_rows()

        return context


class ReferenceDocumentVersionCreate(PermissionRequiredMixin, CreateView):
    template_name = "reference_documents/reference_document_versions/create.jinja"
    permission_required = "reference_documents.add_referencedocumentversion"
    form_class = ReferenceDocumentVersionsCreateUpdateForm

    def get_initial(self):
        initial = super().get_initial()
        initial["reference_document"] = ReferenceDocument.objects.all().get(
            pk=self.kwargs["pk"],
        )
        return initial

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["reference_document"] = ReferenceDocument.objects.all().get(
            pk=self.kwargs["pk"],
        )
        return context_data

    def get_success_url(self):
        return reverse(
            "reference_documents:version-confirm-create",
            kwargs={"pk": self.object.pk},
        )


class ReferenceDocumentVersionEdit(PermissionRequiredMixin, UpdateView):
    model = ReferenceDocumentVersion
    permission_required = "reference_documents.change_referencedocumentversion"
    template_name = "reference_documents/reference_document_versions/edit.jinja"
    form_class = ReferenceDocumentVersionsCreateUpdateForm

    def get_success_url(self):
        return reverse(
            "reference_documents:version-confirm-update",
            kwargs={"pk": self.object.pk},
        )


class ReferenceDocumentVersionDelete(PermissionRequiredMixin, DeleteView):
    form_class = ReferenceDocumentVersionDeleteForm
    model = ReferenceDocumentVersion
    permission_required = "reference_documents.delete_referencedocumentversion"
    template_name = "reference_documents/reference_document_versions/delete.jinja"

    def get_success_url(self) -> str:
        return reverse(
            "reference_documents:version-confirm-delete",
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
            self.request.session["deleted_version"] = {
                "ref_doc_pk": f"{self.object.reference_document.pk}",
                "area_id": f"{self.object.reference_document.area_id}",
                "version": f"{self.object.version}",
            }
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object.delete()
        return redirect(self.get_success_url())


class ReferenceDocumentVersionConfirmCreate(DetailView):
    template_name = (
        "reference_documents/reference_document_versions/confirm_create.jinja"
    )
    model = ReferenceDocumentVersion


class ReferenceDocumentVersionConfirmUpdate(DetailView):
    template_name = (
        "reference_documents/reference_document_versions/confirm_update.jinja"
    )
    model = ReferenceDocumentVersion


class ReferenceDocumentVersionConfirmDelete(TemplateView):
    template_name = (
        "reference_documents/reference_document_versions/confirm_delete.jinja"
    )

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["deleted_pk"] = self.kwargs["deleted_pk"]
        return context_data


class ReferenceDocumentVersionChangeStateToInReview(
    PermissionRequiredMixin,
    DetailView,
):
    template_name = "reference_documents/reference_document_versions/confirm_state_to_in_review.jinja"
    model = ReferenceDocumentVersion
    permission_required = "reference_documents.change_referencedocumentversion"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Update state
        # self.object.in_review()

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["ref_doc_pk"] = self.kwargs["ref_doc_pk"]
        return context_data

    def get(self, request, *args, **kwargs):
        rdv = ReferenceDocumentVersion.objects.all().get(pk=self.kwargs["pk"])
        rdv.in_review()
        rdv.save(force_save=True)
        return super().get(request, *args, **kwargs)


class ReferenceDocumentVersionChangeStateToPublished(
    PermissionRequiredMixin,
    DetailView,
):
    template_name = "reference_documents/reference_document_versions/confirm_state_to_published.jinja"
    model = ReferenceDocumentVersion
    permission_required = "reference_documents.change_referencedocumentversion"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Update state
        # self.object.in_review()

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["ref_doc_pk"] = self.kwargs["ref_doc_pk"]
        return context_data

    def get(self, request, *args, **kwargs):
        rdv = ReferenceDocumentVersion.objects.all().get(pk=self.kwargs["pk"])
        rdv.published()
        rdv.save(force_save=True)
        return super().get(request, *args, **kwargs)


class ReferenceDocumentVersionChangeStateToEditable(
    PermissionRequiredMixin,
    DetailView,
):
    template_name = "reference_documents/reference_document_versions/confirm_state_to_editable.jinja"
    model = ReferenceDocumentVersion
    permission_required = "reference_documents.change_referencedocumentversion"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Update state
        # self.object.in_review()

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["ref_doc_pk"] = self.kwargs["ref_doc_pk"]
        return context_data

    def get(self, request, *args, **kwargs):
        rdv = ReferenceDocumentVersion.objects.all().get(pk=self.kwargs["pk"])
        if rdv.status == ReferenceDocumentVersionStatus.PUBLISHED:
            if request.user.is_superuser:
                rdv.editing_from_published()
                rdv.save(force_save=True)
            else:
                raise PermissionDenied()
        elif rdv.status == ReferenceDocumentVersionStatus.IN_REVIEW:
            rdv.editing_from_in_review()
            rdv.save(force_save=True)

        return super().get(request, *args, **kwargs)


class ReferenceDocumentVersionAlignmentCheck(DetailView):
    template_name = "reference_documents/reference_document_versions/checks.jinja"
    model = ReferenceDocumentVersion
    permission_required = "reference_documents.view_alignmentreportcheck"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        last_alignment_report = self.object.alignment_reports.all().last()
        if last_alignment_report:
            context["last_run"] = last_alignment_report.created_at
        else:
            context["last_run"] = None
        return context

    def post(self, request, *args, **kwargs):
        if request.user.has_perm("reference_documents.add_alignmentreportcheck"):
            # Queue alignment check to background worker
            run_alignment_check.delay(self.kwargs['pk'])

            return redirect('reference_documents:alignment-check-queued', pk=self.kwargs['pk'])
        else:
            return HttpResponseForbidden()


class ReferenceDocumentVersionAlignmentCheckQueued(DetailView):
    template_name = "reference_documents/reference_document_versions/check_queued.jinja"
    model = ReferenceDocumentVersion


class ReferenceDocumentVersionCheckResults(ListView):
    model = AlignmentReportCheck
    template_name = (
        "reference_documents/reference_document_versions/check_results.jinja"
    )
    context_object_name = "checks"

    @property
    def reference_document_version(self) -> ReferenceDocumentVersion:
        return ReferenceDocumentVersion.objects.all().get(pk=self.kwargs["pk"])

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["reference_document_version"] = self.reference_document_version
        return context

    def get_queryset(self):
        alignment_checks = AlignmentReportCheck.objects.all().filter(
            alignment_report__reference_document_version=self.reference_document_version,
        )
        queryset = {
            "preferential_rates": alignment_checks.filter(
                preferential_rate__isnull=False,
            ),
            "preferential_quotas": alignment_checks.filter(
                preferential_quota__isnull=False,
            ),
            "quota_order_numbers": alignment_checks.filter(
                preferential_quota_order_number__isnull=False,
            ),
        }
        return queryset
