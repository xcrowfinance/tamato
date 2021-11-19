import pytest

from certificates.models import Certificate
from certificates.views import CertificatesList
from common.tests.util import assert_model_view_renders
from common.tests.util import get_class_based_view_urls_matching_url
from common.tests.util import view_is_subclass
from common.tests.util import view_urlpattern_ids
from common.views import TamatoListView
from common.views import TrackedModelDetailMixin


@pytest.mark.parametrize(
    ("view", "url_pattern"),
    get_class_based_view_urls_matching_url(
        "certificates/",
        view_is_subclass(TrackedModelDetailMixin),
    ),
    ids=view_urlpattern_ids,
)
def test_certificate_detail_views(view, url_pattern, valid_user_client):
    """Verify that certificate detail views are under the url certificates/ and
    don't return an error."""
    model_overrides = {"certificates.views.CertificateCreateDescription": Certificate}

    assert_model_view_renders(view, url_pattern, valid_user_client, model_overrides)


@pytest.mark.parametrize(
    ("view", "url_pattern"),
    get_class_based_view_urls_matching_url(
        "certificates/",
        view_is_subclass(TamatoListView),
        assert_contains_view_classes=[CertificatesList],
    ),
    ids=view_urlpattern_ids,
)
def test_certificate_list_view(view, url_pattern, valid_user_client):
    """Verify that certificate list view is under the url certificates/ and
    doesn't return an error."""
    assert_model_view_renders(view, url_pattern, valid_user_client)
