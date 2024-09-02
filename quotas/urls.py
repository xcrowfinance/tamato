from django.urls import include
from django.urls import path
from rest_framework import routers

from common.paths import get_ui_paths
from quotas import views

api_router = routers.DefaultRouter()
api_router.register(
    r"quota_order_numbers",
    views.QuotaOrderNumberViewset,
    basename="quotaordernumber",
)
api_router.register(
    r"quota_order_number_origins",
    views.QuotaOrderNumberOriginViewset,
)
api_router.register(
    r"quota_order_number_origin_exclusions",
    views.QuotaOrderNumberOriginExclusionViewset,
)
api_router.register(
    r"quota_definitions",
    views.QuotaDefinitionViewset,
)
api_router.register(
    r"quota_associations",
    views.QuotaAssociationViewset,
)
api_router.register(
    r"quota_suspensions",
    views.QuotaSuspensionViewset,
)
api_router.register(
    r"quota_blocking_periods",
    views.QuotaBlockingViewset,
)
api_router.register(
    r"quota_events",
    views.QuotaEventViewset,
)

ui_patterns = get_ui_paths(views, "<sid:sid>")

urlpatterns = [
    path("quotas/", include(ui_patterns)),
    path(
        f"quotas/create/",
        views.QuotaCreate.as_view(),
        name="quota-ui-create",
    ),
    path(
        f"quotas/<sid>/confirm-create/",
        views.QuotaConfirmCreate.as_view(),
        name="quota-ui-confirm-create",
    ),
    path(
        f"quotas/<sid>/quota_definitions/",
        views.QuotaDefinitionList.as_view(),
        name="quota_definition-ui-list",
    ),
    path(
        f"quotas/<sid>/quota_definitions/create/",
        views.QuotaDefinitionCreate.as_view(),
        name="quota_definition-ui-create",
    ),
    path(
        f"quota_definitions/<sid>/confirm-create/",
        views.QuotaDefinitionConfirmCreate.as_view(),
        name="quota_definition-ui-confirm-create",
    ),
    path(
        f"quota_definitions/<sid>/confirm-delete/",
        views.QuotaDefinitionConfirmDelete.as_view(),
        name="quota_definition-ui-confirm-delete",
    ),
    path(
        f"quota_order_number_origins/<sid>/edit/",
        views.QuotaOrderNumberOriginUpdate.as_view(),
        name="quota_order_number_origin-ui-edit",
    ),
    path(
        f"quota_order_number_origins/<sid>/edit-create/",
        views.QuotaOrderNumberOriginUpdate.as_view(),
        name="quota_order_number_origin-ui-edit-create",
    ),
    path(
        f"quotas/<sid>/quota_order_number_origins/create/",
        views.QuotaOrderNumberOriginCreate.as_view(),
        name="quota_order_number_origin-ui-create",
    ),
    path(
        f"quota_order_number_origins/<sid>/confirm-create/",
        views.QuotaOrderNumberOriginConfirmCreate.as_view(),
        name="quota_order_number_origin-ui-confirm-create",
    ),
    path(
        f"quota_definitions/<sid>/edit/",
        views.QuotaDefinitionUpdate.as_view(),
        name="quota_definition-ui-edit",
    ),
    path(
        f"quota_definitions/<sid>/edit-update/",
        views.QuotaDefinitionUpdate.as_view(),
        name="quota_definition-ui-edit-update",
    ),
    path(
        f"quota_definitions/<sid>/delete/",
        views.QuotaDefinitionDelete.as_view(),
        name="quota_definition-ui-delete",
    ),
    path(
        f"quota_definitions/<sid>/confirm-update/",
        views.QuotaDefinitionConfirmUpdate.as_view(),
        name="quota_definition-ui-confirm-update",
    ),
    path(
        f"quota_definitions/<sid>/quota_associations/",
        views.QuotaAssociationView.as_view(),
        name="quota_association-ui-view",
    ),
    path(
        f"quota_order_number_origins/<sid>/edit/",
        views.QuotaOrderNumberOriginUpdate.as_view(),
        name="quota_order_number_origin-ui-edit-update",
    ),
    path(
        f"quota_order_number_origins/<sid>/confirm-update/",
        views.QuotaOrderNumberOriginConfirmUpdate.as_view(),
        name="quota_order_number_origin-ui-confirm-update",
    ),
    path(
        f"quotas/<sid>/blocking-or-suspension-periods/create/",
        views.QuotaSuspensionOrBlockingCreate.as_view(),
        name="quota_suspension_or_blocking-ui-create",
    ),
    path(
        f"quotas/suspension-periods/<sid>/confirm-create/",
        views.QuotaSuspensionConfirmCreate.as_view(),
        name="quota_suspension-ui-confirm-create",
    ),
    path(
        f"quotas/blocking-periods/<sid>/confirm-create/",
        views.QuotaBlockingConfirmCreate.as_view(),
        name="quota_blocking-ui-confirm-create",
    ),
    path("api/", include(api_router.urls)),
]
