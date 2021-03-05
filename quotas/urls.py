from django.urls import include
from django.urls import path
from django.urls import re_path
from rest_framework import routers

from quotas import views

api_router = routers.DefaultRouter()
api_router.register(r"quota_order_numbers", views.QuotaOrderNumberViewset)
api_router.register(r"quota_order_number_origins", views.QuotaOrderNumberOriginViewset)
api_router.register(
    r"quota_order_number_origin_exclusions",
    views.QuotaOrderNumberOriginExclusionViewset,
)
api_router.register(r"quota_definitions", views.QuotaDefinitionViewset)
api_router.register(r"quota_associations", views.QuotaAssociationViewset)
api_router.register(r"quota_suspensions", views.QuotaSuspensionViewset)
api_router.register(r"quota_blocking_periods", views.QuotaBlockingViewset)
api_router.register(r"quota_events", views.QuotaEventViewset)

ui_patterns = [
    path(
        "",
        views.QuotaList.as_view(),
        name="quota-ui-list",
    ),
    re_path(
        r"^(?P<sid>\d*)$",
        views.QuotaDetail.as_view(),
        name="quota-ui-detail",
    ),
]
urlpatterns = [
    path("quotas/", include(ui_patterns)),
    path("api/", include(api_router.urls)),
]
