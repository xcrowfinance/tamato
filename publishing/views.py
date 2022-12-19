from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.transaction import atomic
from django.shortcuts import redirect
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.views.generic import ListView
from django_fsm import TransitionNotAllowed

from common.views import WithPaginationListMixin
from publishing.forms import LoadingReportForm
from publishing.models import PackagedWorkBasket
from publishing.models import PackagedWorkBasketInvalidQueueOperation
from publishing.models import ProcessingState


class PackagedWorkbasketQueueView(
    PermissionRequiredMixin,
    WithPaginationListMixin,
    ListView,
):
    """UI view used to manage (ordering, pausing, removal) packaged
    workbaskets."""

    model = PackagedWorkBasket
    permission_required = "common.add_trackedmodel"

    def get_template_names(self):
        return ["publishing/packaged_workbasket_queue.jinja"]

    def get_queryset(self):
        """Return all items that are awaiting processing or are actively being
        processed, as displayed on this view."""
        return PackagedWorkBasket.objects.filter(
            processing_state__in=ProcessingState.queued_states(),
        )

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(object_list=object_list, **kwargs)
        data["currently_processing"] = PackagedWorkBasket.objects.currently_processing()
        return data

    def post(self, request, *args, **kwargs):
        """Manage POST requests, which can be to either pause/commence CDS
        processing or move a PackagedWorkBasket instance to the top of the
        packaging queue."""

        post = request.POST

        if post.get("promote_position"):
            url = self._promote_position(request, post.get("promote_position"))
        elif post.get("demote_position"):
            url = self._demote_position(request, post.get("demote_position"))
        elif post.get("promote_to_top_position"):
            url = self._promote_to_top_position(
                request,
                post.get("promote_to_top_position"),
            )
        elif post.get("remove_from_queue"):
            url = self._remove_from_queue(request, post.get("remove_from_queue"))
        else:
            # Handle invalid post content by redisplaying the page.
            url = request.build_absolute_uri()

        return redirect(url)

    # Queue item position management.

    def _promote_position(self, request, pk):
        try:
            packaged_work_basket = PackagedWorkBasket.objects.get(pk=pk)
            packaged_work_basket.promote_position()
        except (
            PackagedWorkBasket.DoesNotExist,
            PackagedWorkBasketInvalidQueueOperation,
        ):
            # Nothing to do in the case of these exceptions.
            pass
        return request.build_absolute_uri()

    def _demote_position(self, request, pk):
        try:
            packaged_work_basket = PackagedWorkBasket.objects.get(pk=pk)
            packaged_work_basket.demote_position()
        except (
            PackagedWorkBasket.DoesNotExist,
            PackagedWorkBasketInvalidQueueOperation,
        ):
            # Nothing to do in the case of these exceptions.
            pass
        return request.build_absolute_uri()

    def _promote_to_top_position(self, request, pk):
        try:
            packaged_work_basket = PackagedWorkBasket.objects.get(pk=pk)
            packaged_work_basket.promote_to_top_position()
        except (
            PackagedWorkBasket.DoesNotExist,
            PackagedWorkBasketInvalidQueueOperation,
        ):
            # Nothing to do in the case of these exceptions.
            pass
        return request.build_absolute_uri()

    def _remove_from_queue(self, request, pk):
        try:
            packaged_work_basket = PackagedWorkBasket.objects.get(pk=pk)
            packaged_work_basket.abandon()
            return reverse(
                "workbaskets:workbasket-ui-changes",
                kwargs={"pk": packaged_work_basket.workbasket.pk},
            )
        except (
            PackagedWorkBasket.DoesNotExist,
            PackagedWorkBasketInvalidQueueOperation,
            TransitionNotAllowed,
        ):
            # Nothing to do in the case of these exceptions.
            return request.build_absolute_uri()


class EnvelopeQueueView(
    PermissionRequiredMixin,
    WithPaginationListMixin,
    ListView,
):
    """UI view used to download and manage envelope processing."""

    model = PackagedWorkBasket
    permission_required = ""  # TODO: select permissions.

    def get_template_names(self):
        return ["publishing/envelope_queue.jinja"]

    def get_queryset(self):
        """Return all items that are awaiting processing or are actively being
        processed, as displayed on this view."""
        return PackagedWorkBasket.objects.all_queued()

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(object_list=object_list, **kwargs)
        data["currently_processing"] = PackagedWorkBasket.objects.currently_processing()
        return data

    def post(self, request, *args, **kwargs):
        """Manage POST requests, including download, accept and reject
        envelopes."""

        post = request.POST

        if post.get("process_envelope"):
            url = self._process_envelope(request, post.get("process_envelope"))
        else:
            # Handle invalid post content by redisplaying the page.
            url = request.build_absolute_uri()

        return redirect(url)

    def _process_envelope(self, request, pk):
        packaged_work_basket = PackagedWorkBasket.objects.get(pk=pk)
        packaged_work_basket.begin_processing()
        """TODO:
        * Make the download file available either:
            - Open in a separate tab.
            - Download as the second step after setting to CURRENTLY_PROCESSING.
        """
        return request.build_absolute_uri()


class CompleteEnvelopeProcessingView(PermissionRequiredMixin, CreateView):
    """Generic UI view used to confirm envelope processing."""

    permission_required = "workbaskets.change_workbasket"
    template_name = "publishing/complete-envelope-processing.jinja"
    form_class = LoadingReportForm
    success_url = reverse_lazy("publishing:envelope-queue-ui-list")

    @atomic
    def form_valid(self, form):
        """Create a LoadingReport instance, associated it wth the
        PackagedWorkBasket and transition that PackagedWorkBasket instance to
        the next, completed processing state (either succeeded or failed)."""

        packaged_work_basket = PackagedWorkBasket.objects.get(
            pk=self.kwargs["pk"],
        )
        self.object = form.save()
        packaged_work_basket.loading_report = self.object
        packaged_work_basket.save()
        self.transition_packaged_work_basket(packaged_work_basket)

        return redirect(self.get_success_url())

    def transition_packaged_work_basket(self, packaged_work_basket):
        raise NotImplementedError()


class AcceptEnvelopeView(CompleteEnvelopeProcessingView):
    """UI view used to accept an envelope as having been processed by HMRC
    systems (CDS, etc)."""

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(object_list=object_list, **kwargs)
        data["accept_reject"] = "accept"
        return data

    def transition_packaged_work_basket(self, packaged_work_basket):
        return packaged_work_basket.processing_succeeded()


class RejectEnvelopeView(CompleteEnvelopeProcessingView):
    """UI view used to reject an envelope as having failed to be processed by
    HMRC systems (CDS, etc)."""

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(object_list=object_list, **kwargs)
        data["accept_reject"] = "reject"
        return data

    def transition_packaged_work_basket(self, packaged_work_basket):
        return packaged_work_basket.processing_failed()
