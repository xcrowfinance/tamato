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
        f"current/review/",
        ui_views.ReviewMeasuresWorkbasketView.as_view(),
        name="review-workbasket",
    ),
    path(
        f"current/violations/",
        ui_views.WorkBasketViolations.as_view(),
        name="workbasket-ui-violations",
    ),
    path(
        f"current/delete-changes/",
        ui_views.WorkBasketDeleteChanges.as_view(),
        name="workbasket-ui-delete-changes",
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
        f"current/delete-changes-done/",
        ui_views.WorkBasketDeleteChangesDone.as_view(),
        name="workbasket-ui-delete-changes-done",
    ),
    path(
        f"<pk>/changes/",
        ui_views.WorkBasketChanges.as_view(),
        name="workbasket-ui-changes",
    ),
    path(
        f"<wb_pk>/violations/<pk>/",
        ui_views.WorkBasketViolationDetail.as_view(),
        name="workbasket-ui-violation-detail",
    ),
]

urlpatterns = [
    path("workbaskets/", include(ui_patterns)),
    path("api/", include(api_router.urls)),
]
