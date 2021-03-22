from typing import Optional
from typing import Type

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db import models
from rest_framework import permissions
from rest_framework import viewsets

from additional_codes.filters import AdditionalCodeFilter
from additional_codes.filters import AdditionalCodeFilterBackend
from additional_codes.forms import AdditionalCodeForm
from additional_codes.models import AdditionalCode
from additional_codes.models import AdditionalCodeType
from additional_codes.serializers import AdditionalCodeSerializer
from additional_codes.serializers import AdditionalCodeTypeSerializer
from common.models import TrackedModel
from common.views import TamatoListView
from common.views import TrackedModelDetailMixin
from common.views import TrackedModelDetailView
from workbaskets.models import WorkBasket
from workbaskets.views.generic import DraftUpdateView


class AdditionalCodeViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows additional codes to be viewed."""

    queryset = (
        AdditionalCode.objects.latest_approved()
        .select_related("type")
        .prefetch_related("descriptions")
    )
    serializer_class = AdditionalCodeSerializer
    filter_backends = [AdditionalCodeFilterBackend]
    search_fields = [
        "type__sid",
        "code",
        "sid",
        "descriptions__description",
    ]


class AdditionalCodeTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows additional code types to be viewed."""

    queryset = AdditionalCodeType.objects.latest_approved()
    serializer_class = AdditionalCodeTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


class AdditionalCodeMixin:
    model: Type[TrackedModel] = AdditionalCode

    def get_queryset(self):
        workbasket = WorkBasket.current(self.request)
        tx = None
        if workbasket:
            tx = workbasket.transactions.order_by("order").last()

        return AdditionalCode.objects.approved_up_to_transaction(tx).select_related(
            "type",
        )


class AdditionalCodeList(AdditionalCodeMixin, TamatoListView):
    """UI endpoint for viewing and filtering Additional Codes."""

    template_name = "additional_codes/list.jinja"
    filterset_class = AdditionalCodeFilter
    search_fields = [
        "type__sid",
        "code",
        "sid",
        "descriptions__description",
    ]


class AdditionalCodeDetail(AdditionalCodeMixin, TrackedModelDetailView):
    template_name = "additional_codes/detail.jinja"


class AdditionalCodeUpdate(
    PermissionRequiredMixin,
    AdditionalCodeMixin,
    TrackedModelDetailMixin,
    DraftUpdateView,
):
    form_class = AdditionalCodeForm
    permission_required = "common.change_trackedmodel"

    def get_object(self, queryset: Optional[models.QuerySet] = None) -> models.Model:
        obj = super().get_object(queryset)

        if self.request.method == "POST":
            obj = obj.new_draft(
                WorkBasket.current(self.request),
                save=False,
            )

        return obj


class AdditionalCodeConfirmUpdate(AdditionalCodeMixin, TrackedModelDetailView):
    template_name = "common/confirm_update.jinja"
