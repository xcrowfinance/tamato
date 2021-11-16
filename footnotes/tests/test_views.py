import pytest
from django.core.exceptions import ValidationError

from common.tests import factories
from common.tests.util import assert_model_view
from common.tests.util import get_detail_class_based_view_urls_matching_url
from common.tests.util import raises_if
from common.tests.util import view_urlpattern_ids
from footnotes.models import Footnote

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("new_data", "expected_valid"),
    (
        ({}, True),
        ({"start_date_0": lambda d: d + 1}, True),
        ({"start_date_0": lambda d: d - 1}, False),
        ({"start_date_1": lambda m: m + 1}, True),
        ({"start_date_2": lambda y: y + 1}, True),
    ),
)
def test_footnote_update(new_data, expected_valid, use_update_form):
    with raises_if(ValidationError, not expected_valid):
        use_update_form(factories.FootnoteFactory(), new_data)


@pytest.mark.parametrize(
    ("new_data", "expected_valid"),
    (
        ({}, True),
        # conditional to avoid false errors at end of month etc.
        ({"validity_start_0": lambda d: d + 1 if d < 28 else 1}, True),
        ({"validity_start_0": lambda d: d - 1 if d > 1 else 28}, True),
        ({"validity_start_1": lambda m: m + 1 if m < 12 else 1}, True),
        ({"validity_start_2": lambda y: y + 1}, True),
        ({"description": lambda d: d + "AAA"}, True),
        ({"description": lambda d: ""}, False),
    ),
)
def test_footnote_description_update(new_data, expected_valid, use_update_form):
    with raises_if(ValidationError, not expected_valid):
        use_update_form(factories.FootnoteDescriptionFactory(), new_data)


@pytest.mark.parametrize(
    ("new_data", "workbasket_valid"),
    (
        ({}, True),
        ({"description": lambda d: d + "AAA"}, True),
        ({"validity_start_0": lambda d: d + 1}, False),
    ),
)
def test_footnote_business_rule_application(
    new_data,
    workbasket_valid,
    use_update_form,
):
    description = use_update_form(factories.FootnoteDescriptionFactory(), new_data)
    with raises_if(ValidationError, not workbasket_valid):
        description.transaction.workbasket.clean()


@pytest.mark.parametrize(
    ("view", "url_pattern"),
    get_detail_class_based_view_urls_matching_url("footnotes/"),
    ids=view_urlpattern_ids,
)
def test_footnote_detail_views(view, url_pattern, valid_user_client):
    """Verify that measure detail views are under the url footnotes/ and don't
    return an error."""
    model_overrides = {"footnotes.views.FootnoteCreateDescription": Footnote}

    assert_model_view(view, url_pattern, valid_user_client, model_overrides)
