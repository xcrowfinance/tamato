from unittest.mock import patch

import pytest

from common.tests import factories
from measures import forms
from measures.forms import MeasureForm

pytestmark = pytest.mark.django_db


@patch("measures.models.Measure.diff_components")
def test_diff_components_not_called(
    diff_components,
    measure_form,
    duty_sentence_parser,
):
    measure_form.save(commit=False)

    assert diff_components.called == False


@patch("measures.models.Measure.diff_components")
def test_diff_components_called(diff_components, measure_form, duty_sentence_parser):
    measure_form.data.update(duty_sentence="6.000%")
    measure_form.save(commit=False)

    assert diff_components.called == True


def test_error_raised_if_no_duty_sentence(session_with_workbasket):
    measure = factories.MeasureFactory.create()

    with pytest.raises(
        AttributeError,
        match="Measure instance is missing `duty_sentence` attribute. Try calling `with_duty_sentence` queryset method",
    ):
        MeasureForm(data={}, instance=measure, request=session_with_workbasket)


def test_measure_forms_details_valid_data(measure_type, regulation):
    data = {
        "measure_type": measure_type.pk,
        "generating_regulation": regulation.pk,
        "order_number": None,
        "start_date_0": 2,
        "start_date_1": 4,
        "start_date_2": 2021,
    }
    form = forms.MeasureDetailsForm(data, prefix="")
    assert form.is_valid()


def test_measure_forms_details_invalid_data():
    data = {
        "measure_type": "foo",
        "generating_regulation": "bar",
        "order_number": None,
        "start_date_0": 2,
        "start_date_1": 4,
        "start_date_2": 2021,
    }
    form = forms.MeasureDetailsForm(data, prefix="")
    error_string = [
        "Select a valid choice. That choice is not one of the available choices.",
    ]
    assert form.errors["measure_type"] == error_string
    assert form.errors["generating_regulation"] == error_string
    assert not form.is_valid()


def test_measure_forms_details_invalid_date_range(measure_type, regulation):
    data = {
        "measure_type": measure_type.pk,
        "generating_regulation": regulation.pk,
        "order_number": None,
        "start_date_0": 1,
        "start_date_1": 1,
        "start_date_2": 2000,
    }
    form = forms.MeasureDetailsForm(data, prefix="")
    # In the real wizard view the prefix will be populated with the name of the form. It's left blank here to make the mock form data simpler
    assert not form.is_valid()
    assert (
        form.errors["__all__"][0]
        == "The date range of the measure can't be outside that of the measure type: [2020-01-01, None) does not contain [2000-01-01, None)"
    )


def test_measure_forms_additional_code_valid_data(additional_code):
    data = {
        "additional_code": additional_code.pk,
    }
    form = forms.MeasureAdditionalCodeForm(data, prefix="")
    assert form.is_valid()


def test_measure_forms_additional_code_invalid_data():
    data = {
        "additional_code": "foo",
    }
    form = forms.MeasureAdditionalCodeForm(data, prefix="")
    assert form.errors["additional_code"] == [
        "Select a valid choice. That choice is not one of the available choices.",
    ]
    assert not form.is_valid()


@pytest.mark.parametrize(
    "duties,is_valid",
    [("33 GBP/100kg", True), ("some invalid duty expression", False)],
)
def test_measure_forms_duties_form(duties, is_valid, duty_sentence_parser, date_ranges):
    commodity = factories.GoodsNomenclatureFactory.create()
    data = {
        "duties": duties,
        "commodity": commodity,
    }
    initial_data = {"measure_start_date": date_ranges.normal}
    form = forms.MeasureCommodityAndDutiesForm(data, prefix="", initial=initial_data)
    assert form.is_valid() == is_valid


def test_measure_forms_conditions_form_valid_data():
    condition_code = factories.MeasureConditionCodeFactory.create()
    action = factories.MeasureActionFactory.create()
    data = {
        "condition_code": condition_code.pk,
        "duty_amount": 1.000,
        "action": action.pk,
    }
    form = forms.MeasureConditionsForm(data, prefix="")

    assert form.is_valid()


def test_measure_forms_conditions_form_invalid_data():
    action = factories.MeasureActionFactory.create()
    data = {
        "duty_amount": 1.000,
        "action": action.pk,
    }
    form = forms.MeasureConditionsForm(data, prefix="")

    assert not form.is_valid()
    assert form.errors["condition_code"][0] == "This field is required."
