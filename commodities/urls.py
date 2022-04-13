from django.urls import include
from django.urls import path
from rest_framework import routers

from commodities import views

api_router = routers.DefaultRouter()
api_router.register(
    r"goods_nomenclature",
    views.GoodsNomenclatureViewset,
    basename="goodsnomenclature",
)

urlpatterns = [
    path("api/", include(api_router.urls)),
    path(
        "commodities/import/",
        views.CommodityImportView.as_view(),
        name="commodities-import",
    ),
    path(
        "commodities/import/success/",
        views.CommodityImportSuccessView.as_view(),
        name="commodities-import-success",
    ),
]
