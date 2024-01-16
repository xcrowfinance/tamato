from django.urls import include
from django.urls import path
from rest_framework import routers

from workbaskets.views import api as api_views
from workbaskets.views import ui as ui_views

app_name = "workbaskets"

api_router = routers.DefaultRouter()
api_router.register(r"workbaskets", api_views.WorkBasketViewSet)

ui_patterns = [
    path(
        "",
        ui_views.SelectWorkbasketView.as_view(),
        name="workbasket-ui-list",
    ),
    path(
        "create/",
        ui_views.WorkBasketCreate.as_view(),
        name="workbasket-ui-create",
    ),
    path(
        f"<pk>/edit-details/",
        ui_views.WorkBasketUpdate.as_view(),
        name="workbasket-ui-update",
    ),
    path(
        "list-all/",
        ui_views.WorkBasketList.as_view(),
        name="workbasket-ui-list-all",
    ),
    path(
        "download/",
        ui_views.download_envelope,
        name="workbasket-download",
    ),
    path(
        f"current/",
        ui_views.CurrentWorkBasket.as_view(),
        name="current-workbasket",
    ),
    path(
        f"current/edit/",
        ui_views.EditWorkbasketView.as_view(),
        name="edit-workbasket",
    ),
    path(
        f"current/checks/",
        ui_views.WorkBasketChecksView.as_view(),
        name="workbasket-checks",
    ),
    path(
        f"<pk>/review-additional-codes/",
        ui_views.WorkBasketReviewAdditionalCodesView.as_view(),
        name="workbasket-ui-review-additional-codes",
    ),
    path(
        f"<pk>/review-certificates/",
        ui_views.WorkBasketReviewCertificatesView.as_view(),
        name="workbasket-ui-review-certificates",
    ),
    path(
        f"<pk>/review-goods/",
        ui_views.WorkbasketReviewGoodsView.as_view(),
        name="workbasket-ui-review-goods",
    ),
    path(
        f"<pk>/review-footnotes/",
        ui_views.WorkBasketReviewFootnotesView.as_view(),
        name="workbasket-ui-review-footnotes",
    ),
    path(
        f"<pk>/review-geographical-areas/",
        ui_views.WorkBasketReviewGeoAreasView.as_view(),
        name="workbasket-ui-review-geo-areas",
    ),
    path(
        f"<pk>/review-geographical-memberships/",
        ui_views.WorkBasketReviewGeoMembershipsView.as_view(),
        name="workbasket-ui-review-geo-memberships",
    ),
    path(
        f"<pk>/review-measures/",
        ui_views.WorkBasketReviewMeasuresView.as_view(),
        name="workbasket-ui-review-measures",
    ),
    path(
        f"<pk>/review-quotas/",
        ui_views.WorkBasketReviewQuotasView.as_view(),
        name="workbasket-ui-review-quotas",
    ),
    path(
        f"<pk>/review-quota-definitions/",
        ui_views.WorkBasketReviewQuotaDefinitionsView.as_view(),
        name="workbasket-ui-review-quota-definitions",
    ),
    path(
        f"<pk>/review-regulations/",
        ui_views.WorkBasketReviewRegulationsView.as_view(),
        name="workbasket-ui-review-regulations",
    ),
    path(
        f"current/violations/",
        ui_views.WorkBasketViolations.as_view(),
        name="workbasket-ui-violations",
    ),
    path(
        f"<pk>/confirm-create/",
        ui_views.WorkBasketConfirmCreate.as_view(),
        name="workbasket-ui-confirm-create",
    ),
    path(
        f"<pk>/confirm-update/",
        ui_views.WorkBasketConfirmUpdate.as_view(),
        name="workbasket-ui-confirm-update",
    ),
    path(
        f"compare/",
        ui_views.WorkBasketCompare.as_view(),
        name="workbasket-check-ui-compare",
    ),
    path(
        f"<pk>/",
        ui_views.WorkBasketDetailView.as_view(),
        name="workbasket-ui-detail",
    ),
    path(
        f"<pk>/changes/",
        ui_views.WorkBasketChangesView.as_view(),
        name="workbasket-ui-changes",
    ),
    path(
        f"<pk>/changes/delete/",
        ui_views.WorkBasketChangesDelete.as_view(),
        name="workbasket-ui-changes-delete",
    ),
    path(
        f"<pk>/changes/confirm-delete/",
        ui_views.WorkBasketChangesConfirmDelete.as_view(),
        name="workbasket-ui-changes-confirm-delete",
    ),
    path(
        f"<pk>/transaction-order/",
        ui_views.WorkBasketTransactionOrderView.as_view(),
        name="workbasket-ui-transaction-order",
    ),
    path(
        f"<wb_pk>/violations/<pk>/",
        ui_views.WorkBasketViolationDetail.as_view(),
        name="workbasket-ui-violation-detail",
    ),
    path(
        f"<pk>/delete/",
        ui_views.WorkBasketDelete.as_view(),
        name="workbasket-ui-delete",
    ),
    path(
        f"<deleted_pk>/delete-done/",
        ui_views.WorkBasketDeleteDone.as_view(),
        name="workbasket-ui-delete-done",
    ),
]

urlpatterns = [
    path("workbaskets/", include(ui_patterns)),
    path("api/", include(api_router.urls)),
]
