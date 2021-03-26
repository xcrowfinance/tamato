from django.urls import include
from django.urls import path
from django.urls import re_path
from rest_framework import routers

from footnotes import views
from footnotes.validators import FOOTNOTE_ID_PATTERN
from footnotes.validators import FOOTNOTE_TYPE_ID_PATTERN

api_router = routers.DefaultRouter()
api_router.register(r"footnotes", views.FootnoteViewSet)
api_router.register(r"footnote_types", views.FootnoteTypeViewSet)

detail = fr"(?P<footnote_type__footnote_type_id>{FOOTNOTE_TYPE_ID_PATTERN})(?P<footnote_id>{FOOTNOTE_ID_PATTERN})"
description_detail = fr"(?P<described_footnote__footnote_type__footnote_type_id>{FOOTNOTE_TYPE_ID_PATTERN})(?P<described_footnote__footnote_id>{FOOTNOTE_ID_PATTERN})/"

ui_patterns = [
    path(
        "",
        views.FootnoteList.as_view(),
        name="footnote-ui-list",
    ),
    re_path(
        fr"{detail}/$",
        views.FootnoteDetail.as_view(),
        name="footnote-ui-detail",
    ),
    re_path(
        fr"{detail}/edit/$",
        views.FootnoteUpdate.as_view(),
        name="footnote-ui-edit",
    ),
    re_path(
        fr"{detail}/confirm-update/$",
        views.FootnoteConfirmUpdate.as_view(),
        name="footnote-ui-confirm-update",
    ),
    re_path(
        (
            description_detail
            + r"description/(?P<description_period_sid>[0-9]{1,8})/edit/$"
        ),
        views.FootnoteDescriptionUpdate.as_view(),
        name="footnote-ui-description-edit",
    ),
    re_path(
        (
            description_detail
            + r"description/(?P<description_period_sid>[0-9]{1,8})/confirm-update/$"
        ),
        views.FootnoteDescriptionConfirmUpdate.as_view(),
        name="footnote-ui-description-confirm-update",
    ),
    path("api/", include(api_router.urls)),
]

urlpatterns = [
    path("footnotes/", include(ui_patterns)),
    path("api/", include(api_router.urls)),
]
