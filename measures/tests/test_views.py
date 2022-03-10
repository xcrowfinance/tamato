import unittest
from decimal import Decimal
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from django.urls import reverse

from common.models.transactions import Transaction
from common.tests import factories
from common.tests.util import assert_model_view_renders
from common.tests.util import get_class_based_view_urls_matching_url
from common.tests.util import raises_if
from common.tests.util import view_is_subclass
from common.tests.util import view_urlpattern_ids
from common.views import TamatoListView
from common.views import TrackedModelDetailMixin
from measures.models import Measure
from measures.models import MeasureCondition
from measures.models import MeasureConditionCode
from measures.validators import validate_duties
from measures.views import MeasureCreateWizard
from measures.views import MeasureFootnotesUpdate
from measures.views import MeasureList

pytestmark = pytest.mark.django_db


def test_measure_footnotes_update_get_delete_key():
    footnote_key = "form-0-footnote"
    expected = "form-0-DELETE"
    delete_key = MeasureFootnotesUpdate().get_delete_key(footnote_key)

    assert delete_key == expected


def test_measure_footnotes_update_post_remove(client, valid_user):
    measure = factories.MeasureFactory.create()
    footnote = factories.FootnoteAssociationMeasureFactory.create(
        footnoted_measure=measure,
    ).associated_footnote
    url = reverse("measure-ui-edit-footnotes", kwargs={"sid": measure.sid})
    post_data = {"remove": footnote.pk}
    client.force_login(valid_user)
    session = client.session
    session.update({f"instance_footnotes_{measure.sid}": [footnote.pk]})
    session.save()

    client.post(url, data=post_data)

    assert client.session[f"instance_footnotes_{measure.sid}"] == []


def test_measure_footnotes_update_post_without_remove(client, valid_user):
    measure = factories.MeasureFactory.create()
    footnote_1 = factories.FootnoteAssociationMeasureFactory.create(
        footnoted_measure=measure,
    ).associated_footnote
    footnote_2 = factories.FootnoteAssociationMeasureFactory.create(
        footnoted_measure=measure,
    ).associated_footnote
    url = reverse("measure-ui-edit-footnotes", kwargs={"sid": measure.sid})
    post_data = {"form-1-footnote": footnote_1.pk, "form-2-footnote": footnote_2.pk}
    client.force_login(valid_user)

    client.post(url, data=post_data)

    assert client.session[f"formset_initial_{measure.sid}"] == [
        {"footnote": str(footnote_1.pk)},
        {"footnote": str(footnote_2.pk)},
    ]


def test_measure_footnotes_update_post_without_remove_ignores_delete_keys(
    client,
    valid_user,
):
    measure = factories.MeasureFactory.create()
    footnote_1 = factories.FootnoteAssociationMeasureFactory.create(
        footnoted_measure=measure,
    ).associated_footnote
    footnote_2 = factories.FootnoteAssociationMeasureFactory.create(
        footnoted_measure=measure,
    ).associated_footnote
    url = reverse("measure-ui-edit-footnotes", kwargs={"sid": measure.sid})
    post_data = {
        "form-1-footnote": footnote_1.pk,
        "form-2-footnote": footnote_2.pk,
        "form-2-DELETE": "",
    }
    client.force_login(valid_user)

    client.post(url, data=post_data)

    assert client.session[f"formset_initial_{measure.sid}"] == [
        {"footnote": str(footnote_1.pk)},
    ]


def test_measure_delete(use_delete_form):
    use_delete_form(factories.MeasureFactory())


@pytest.mark.parametrize(
    ("view", "url_pattern"),
    get_class_based_view_urls_matching_url(
        "measures/",
        view_is_subclass(TrackedModelDetailMixin),
    ),
    ids=view_urlpattern_ids,
)
def test_measure_detail_views(view, url_pattern, valid_user_client):
    """Verify that measure detail views are under the url measures/ and don't
    return an error."""
    assert_model_view_renders(view, url_pattern, valid_user_client)


def test_measure_detail_conditions(client, valid_user):
    measure = factories.MeasureFactory.create()
    condition_code = factories.MeasureConditionCodeFactory.create()
    certificate_condition = factories.MeasureConditionWithCertificateFactory.create(
        dependent_measure=measure,
        condition_code=condition_code,
        component_sequence_number=1,
    )
    amount_condition = factories.MeasureConditionFactory.create(
        dependent_measure=measure,
        duty_amount=1000.000,
        condition_code=condition_code,
        component_sequence_number=2,
    )
    url = reverse("measure-ui-detail", kwargs={"sid": measure.sid}) + "#conditions"
    client.force_login(valid_user)
    response = client.get(url)
    page = BeautifulSoup(
        response.content.decode(response.charset),
        features="lxml",
    )

    assert (
        page.find("h3").text == f"{condition_code.code}: {condition_code.description}"
    )

    rows = page.find("table").findChildren(["th", "tr"])
    # ignore everything above the first condition row
    first_row = rows[4]
    cells = first_row.findChildren(["td"])
    certificate = certificate_condition.required_certificate

    assert (
        cells[0].text
        == f"{certificate.code}:\n        {certificate.get_description().description}"
    )
    assert cells[1].text == certificate_condition.action.description
    assert cells[2].text == "-"

    second_row = rows[5]
    cells = second_row.findChildren(["td"])

    assert (
        cells[0].text
        == f"\n    1000.000\n        {amount_condition.monetary_unit.code}"
    )
    assert len(rows) == 6


@pytest.mark.parametrize(
    ("view", "url_pattern"),
    get_class_based_view_urls_matching_url(
        "measures/",
        view_is_subclass(TamatoListView),
        assert_contains_view_classes=[MeasureList],
    ),
    ids=view_urlpattern_ids,
)
def test_measure_list_view(view, url_pattern, valid_user_client):
    """Verify that measure list view is under the url measures/ and doesn't
    return an error."""
    assert_model_view_renders(view, url_pattern, valid_user_client)


@pytest.mark.parametrize(
    ("duties", "error_expected"),
    [
        ("33 GBP/100kg", False),
        ("33 GBP/100kge", True),
    ],
)
def test_duties_validator(
    duties,
    error_expected,
    date_ranges,
    duty_sentence_parser,
):
    # duty_sentence_parser populates data needed by the DutySentenceParser
    # removing it will cause the test to fail.
    with raises_if(ValidationError, error_expected):
        validate_duties(duties, date_ranges.normal)


@pytest.mark.parametrize(
    ("update_data"),
    [
        {},
        {"duty_sentence": "10.000%"},
    ],
)
def test_measure_update_duty_sentence(
    update_data,
    client,
    valid_user,
    measure_form,
    duty_sentence_parser,
):
    """
    A placeholder test until we find a way of making use_update_form compatible
    with MeasureForm.

    Generates minimal post_data from instance and verifies that the edit
    endpoint redirects successfully. Checks that latest Measure instance has the
    correct components, if duty_sentence in data.
    """
    post_data = measure_form.data
    # Remove keys with null value to avoid TypeError
    post_data = {k: v for k, v in post_data.items() if v is not None}
    post_data.update(update_data)
    post_data["update_type"] = 1
    url = reverse("measure-ui-edit", args=(measure_form.instance.sid,))
    client.force_login(valid_user)
    response = client.post(url, data=post_data)

    assert response.status_code == 302

    if update_data:
        tx = Transaction.objects.last()
        measure = Measure.objects.approved_up_to_transaction(tx).get(
            sid=measure_form.instance.sid,
        )
        components = measure.components.approved_up_to_transaction(tx).filter(
            component_measure__sid=measure_form.instance.sid,
        )

        assert components.exists()
        assert components.count() == 1
        assert components.first().duty_amount == 10.000


# https://uktrade.atlassian.net/browse/TP2000-144
@patch("measures.forms.MeasureForm.save")
def test_measure_form_save_called_on_measure_update(
    save,
    client,
    valid_user,
    measure_form,
):
    """Until work is done to make `TrackedModel` call new_version in save() we
    need to check that MeasureUpdate view explicitly calls
    MeasureForm.save(commit=False)"""
    post_data = measure_form.data
    post_data = {k: v for k, v in post_data.items() if v is not None}
    post_data["update_type"] = 1
    url = reverse("measure-ui-edit", args=(measure_form.instance.sid,))
    client.force_login(valid_user)
    client.post(url, data=post_data)

    save.assert_called_with(commit=False)


@pytest.mark.django_db
def test_measure_form_wizard_start(valid_user_client):
    url = reverse("measure-ui-create", kwargs={"step": "start"})
    response = valid_user_client.get(url)
    assert response.status_code == 200


@unittest.mock.patch("measures.parsers.DutySentenceParser")
def test_measure_form_wizard_finish(
    mock_duty_sentence_parser,
    valid_user_client,
    measure_type,
    regulation,
    duty_sentence_parser,
):
    commodity1 = factories.GoodsNomenclatureFactory.create()
    commodity2 = factories.GoodsNomenclatureFactory.create()

    mock_duty_sentence_parser.return_value = duty_sentence_parser

    wizard_data = [
        {
            "data": {"measure_create_wizard-current_step": "start"},
            "next_step": "measure_details",
        },
        {
            "data": {
                "measure_create_wizard-current_step": "measure_details",
                "measure_details-measure_type": measure_type.pk,
                "measure_details-generating_regulation": regulation.pk,
                "measure_details-start_date_0": 2,
                "measure_details-start_date_1": 4,
                "measure_details-start_date_2": 2021,
            },
            "next_step": "commodities",
        },
        {
            "data": {
                "measure_create_wizard-current_step": "commodities",
                "commodities-0-commodity": commodity1.pk,
                "commodities-0-duties": "33 GBP/100kg",
                "commodities-1-commodity": commodity2.pk,
                "commodities-1-duties": "40 GBP/1kg",
            },
            "next_step": "additional_code",
        },
        {
            "data": {"measure_create_wizard-current_step": "additional_code"},
            "next_step": "conditions",
        },
        {
            "data": {"measure_create_wizard-current_step": "conditions"},
            "next_step": "footnotes",
        },
        {
            "data": {"measure_create_wizard-current_step": "footnotes"},
            "next_step": "summary",
        },
        {
            "data": {"measure_create_wizard-current_step": "summary"},
            "next_step": "complete",
        },
    ]
    for step_data in wizard_data:
        url = reverse(
            "measure-ui-create",
            kwargs={"step": step_data["data"]["measure_create_wizard-current_step"]},
        )
        response = valid_user_client.post(url, step_data["data"])

        assert response.status_code == 302
        assert response.url == reverse(
            "measure-ui-create", kwargs={"step": step_data["next_step"]}
        )


@unittest.mock.patch("workbaskets.models.WorkBasket.current")
def test_measure_form_wizard_create_measures(
    mock_workbasket,
    mock_request,
    duty_sentence_parser,
    date_ranges,
    additional_code,
    measure_type,
    regulation,
    commodity1,
    commodity2,
):
    mock_workbasket.return_value = factories.WorkBasketFactory.create()

    commodity3 = factories.GoodsNomenclatureFactory.create()
    footnote1 = factories.FootnoteFactory.create()
    footnote2 = factories.FootnoteFactory.create()
    geo_area = factories.GeographicalAreaFactory.create()
    condition_code1 = factories.MeasureConditionCodeFactory()
    condition_code2 = factories.MeasureConditionCodeFactory()
    condition_code3 = factories.MeasureConditionCodeFactory()
    action1 = factories.MeasureActionFactory()
    action2 = factories.MeasureActionFactory()
    action3 = factories.MeasureActionFactory()

    form_data = {
        "measure_type": measure_type,
        "generating_regulation": regulation,
        "geographical_area": geo_area,
        "order_number": None,
        "valid_between": date_ranges.normal,
        "formset-commodities": [
            {"commodity": commodity1, "duties": "33 GBP/100kg", "DELETE": False},
            {"commodity": commodity2, "duties": "40 GBP/100kg", "DELETE": False},
            {"commodity": commodity3, "duties": "2 GBP/100kg", "DELETE": True},
        ],
        "additional_code": None,
        "formset-conditions": [
            {
                "condition_code": condition_code1,
                "duty_amount": 4.000,
                "required_certificate": None,
                "action": action1,
                "DELETE": False,
            },
            {
                "condition_code": condition_code2,
                "duty_amount": None,
                "required_certificate": None,
                "action": action2,
                "DELETE": False,
            },
            {
                "condition_code": condition_code3,
                "duty_amount": None,
                "required_certificate": None,
                "action": action3,
                "DELETE": True,
            },
        ],
        "formset-footnotes": [
            {"footnote": footnote1, "DELETE": False},
            {"footnote": footnote2, "DELETE": True},
        ],
    }

    wizard = MeasureCreateWizard(request=mock_request)

    measures = wizard.create_measures(form_data)

    assert len(measures) == 2

    assert Measure.objects.get(goods_nomenclature=commodity1)
    assert Measure.objects.get(goods_nomenclature=commodity2)
    with pytest.raises(Measure.DoesNotExist):
        Measure.objects.get(goods_nomenclature=commodity3)

    assert Measure.objects.get(
        goods_nomenclature=commodity1
    ).components.get().duty_amount == Decimal("33.000")
    assert Measure.objects.get(
        goods_nomenclature=commodity2
    ).components.get().duty_amount == Decimal("40.000")

    assert measures[0].footnotes.get() == footnote1
    assert measures[1].footnotes.get() == footnote1

    assert len(measures[0].footnotes.all()) == 1
    assert len(measures[1].footnotes.all()) == 1

    assert len(measures[0].conditions.all()) == 2
    assert len(measures[1].conditions.all()) == 2

    created_conditions = MeasureCondition.objects.filter(
        dependent_measure__in=[m.id for m in measures]
    )

    created_condition_codes = MeasureConditionCode.objects.filter(
        conditions__in=[c.id for c in created_conditions]
    )

    assert condition_code1 in created_condition_codes
    assert condition_code2 in created_condition_codes
    assert condition_code3 not in created_condition_codes
