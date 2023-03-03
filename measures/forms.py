import datetime
import logging

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import HTML
from crispy_forms_gds.layout import Button
from crispy_forms_gds.layout import Div
from crispy_forms_gds.layout import Field
from crispy_forms_gds.layout import Fieldset
from crispy_forms_gds.layout import Fluid
from crispy_forms_gds.layout import Layout
from crispy_forms_gds.layout import Size
from crispy_forms_gds.layout import Submit
from django import forms
from django.core.exceptions import ValidationError
from django.db.models import TextChoices
from django.template import loader
from django.urls import reverse

from additional_codes.models import AdditionalCode
from certificates.models import Certificate
from commodities.models import GoodsNomenclature
from common.fields import AutoCompleteField
from common.forms import BindNestedFormMixin
from common.forms import DateInputFieldFixed
from common.forms import FormSet
from common.forms import RadioNested
from common.forms import ValidityPeriodForm
from common.forms import delete_form_for
from common.forms import formset_factory
from common.util import validity_range_contains_range
from common.validators import UpdateType
from footnotes.models import Footnote
from geo_areas.models import GeographicalArea
from geo_areas.validators import AreaCode
from measures import models
from measures.constants import MeasureEditSteps
from measures.parsers import DutySentenceParser
from measures.patterns import MeasureCreationPattern
from measures.util import diff_components
from measures.validators import validate_duties
from quotas.models import QuotaOrderNumber
from regulations.models import Regulation
from workbaskets.models import WorkBasket

logger = logging.getLogger(__name__)


ERGA_OMNES_EXCLUSIONS_PREFIX = "erga_omnes_exclusions"
ERGA_OMNES_EXCLUSIONS_FORMSET_PREFIX = (
    f"{ERGA_OMNES_EXCLUSIONS_PREFIX}_formset"  # /PS-IGNORE
)
GROUP_EXCLUSIONS_PREFIX = "geo_group_exclusions"
GROUP_EXCLUSIONS_FORMSET_PREFIX = f"{GROUP_EXCLUSIONS_PREFIX}_formset"

GEO_GROUP_PREFIX = "geographical_area_group"
GEO_GROUP_FORMSET_PREFIX = f"{GEO_GROUP_PREFIX}_formset"

COUNTRY_REGION_PREFIX = "country_region"
COUNTRY_REGION_FORMSET_PREFIX = f"{COUNTRY_REGION_PREFIX}_formset"


class GeoAreaType(TextChoices):
    ERGA_OMNES = "ERGA_OMNES", "All countries (erga omnes)"
    GROUP = "GROUP", "A group of countries"
    COUNTRY = "COUNTRY", "Specific countries or regions"


SUBFORM_PREFIX_MAPPING = {
    GeoAreaType.GROUP: GEO_GROUP_PREFIX,
    GeoAreaType.COUNTRY: COUNTRY_REGION_FORMSET_PREFIX,
}

EXCLUSIONS_FORMSET_PREFIX_MAPPING = {
    GeoAreaType.ERGA_OMNES: ERGA_OMNES_EXCLUSIONS_FORMSET_PREFIX,
    GeoAreaType.GROUP: GROUP_EXCLUSIONS_FORMSET_PREFIX,
    GeoAreaType.COUNTRY: None,
}

FIELD_NAME_MAPPING = {
    GeoAreaType.ERGA_OMNES: "erga_omnes_exclusion",
    GeoAreaType.GROUP: "geo_group_exclusion",
}


class GeoGroupForm(forms.Form):
    prefix = GEO_GROUP_PREFIX

    geographical_area_group = forms.ModelChoiceField(
        label="",
        queryset=None,  # populated in __init__
        error_messages={"required": "A country group is required."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["geographical_area_group"].queryset = (
            GeographicalArea.objects.current()
            .with_latest_description()
            .filter(area_code=AreaCode.GROUP)
            .as_at_today()
            .order_by("description")
        )
        # descriptions__description" should make this implicitly distinct()
        self.fields[
            "geographical_area_group"
        ].label_from_instance = lambda obj: f"{obj.area_id} - {obj.description}"

        if self.initial.get("geo_area") == GeoAreaType.GROUP.value:
            self.initial["geographical_area_group"] = self.initial["geographical_area"]


class ErgaOmnesExclusionsForm(forms.Form):
    prefix = ERGA_OMNES_EXCLUSIONS_PREFIX

    erga_omnes_exclusion = forms.ModelChoiceField(
        label="",
        queryset=GeographicalArea.objects.all(),
        help_text="Select a country to be excluded:",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["erga_omnes_exclusion"].queryset = (
            GeographicalArea.objects.current()
            .with_latest_description()
            .as_at_today()
            .order_by("description")
        )
        self.fields[
            "erga_omnes_exclusion"
        ].label_from_instance = lambda obj: f"{obj.area_id} - {obj.description}"


class GeoGroupExclusionsForm(forms.Form):
    prefix = GROUP_EXCLUSIONS_PREFIX

    geo_group_exclusion = forms.ModelChoiceField(
        label="",
        queryset=GeographicalArea.objects.all(),
        help_text="Select a country to be excluded:",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["geo_group_exclusion"].queryset = (
            GeographicalArea.objects.current()
            .with_latest_description()
            .as_at_today()
            .order_by("description")
        )
        self.fields[
            "geo_group_exclusion"
        ].label_from_instance = lambda obj: f"{obj.area_id} - {obj.description}"


GeoGroupFormSet = formset_factory(
    GeoGroupForm,
    prefix=GEO_GROUP_FORMSET_PREFIX,
    formset=FormSet,
    min_num=1,
    max_num=2,
    extra=1,
    validate_min=True,
    validate_max=True,
)

ErgaOmnesExclusionsFormSet = formset_factory(
    ErgaOmnesExclusionsForm,
    prefix=ERGA_OMNES_EXCLUSIONS_FORMSET_PREFIX,
    formset=FormSet,
    min_num=0,
    max_num=10,
    extra=1,
    validate_min=True,
    validate_max=True,
)

GeoGroupExclusionsFormSet = formset_factory(
    GeoGroupExclusionsForm,
    prefix=GROUP_EXCLUSIONS_FORMSET_PREFIX,
    formset=FormSet,
    min_num=0,
    max_num=10,
    extra=1,
    validate_min=True,
    validate_max=True,
)


class CountryRegionForm(forms.Form):
    prefix = COUNTRY_REGION_PREFIX

    geographical_area_country_or_region = forms.ModelChoiceField(
        queryset=GeographicalArea.objects.exclude(
            area_code=AreaCode.GROUP,
            descriptions__description__isnull=True,
        ),
        error_messages={"required": "A country or region is required."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["geographical_area_country_or_region"].queryset = (
            GeographicalArea.objects.current()
            .with_latest_description()
            .exclude(area_code=AreaCode.GROUP)
            .as_at_today()
            .order_by("description")
        )

        self.fields[
            "geographical_area_country_or_region"
        ].label_from_instance = lambda obj: f"{obj.area_id} - {obj.description}"

        if self.initial.get("geo_area") == GeoAreaType.COUNTRY.value:
            self.initial["geographical_area_country_or_region"] = self.initial[
                "geographical_area"
            ]


CountryRegionFormSet = formset_factory(
    CountryRegionForm,
    prefix=COUNTRY_REGION_FORMSET_PREFIX,
    formset=FormSet,
    min_num=1,
    max_num=2,
    extra=1,
    validate_min=True,
    validate_max=True,
)


class MeasureConditionComponentDuty(Field):
    template = "components/measure_condition_component_duty/template.jinja"


class MeasureValidityForm(ValidityPeriodForm):
    """A form for working with `start_date` and `end_date` logic where the
    `valid_between` field does not already exist on the form."""

    class Meta:
        model = models.Measure
        fields = [
            "valid_between",
        ]


class MeasureConditionsFormMixin(forms.ModelForm):
    class Meta:
        model = models.MeasureCondition
        fields = [
            "condition_code",
            "duty_amount",
            "monetary_unit",
            "condition_measurement",
            "required_certificate",
            "action",
            "applicable_duty",
            "condition_sid",
        ]

    condition_code = forms.ModelChoiceField(
        label="",
        queryset=models.MeasureConditionCode.objects.latest_approved(),
        empty_label="-- Please select a condition code --",
    )
    # This field used to be called duty_amount, but forms.ModelForm expects a decimal value when it sees that duty_amount is a DecimalField on the MeasureCondition model.
    # reference_price expects a non-compound duty string (e.g. "11 GBP / 100 kg".
    # Using DutySentenceParser we validate this string and get the decimal value to pass to the model field, duty_amount)
    reference_price = forms.CharField(
        label="Reference price or quantity",
        required=False,
    )
    required_certificate = AutoCompleteField(
        label="Certificate, licence or document",
        queryset=Certificate.objects.current(),
        required=False,
    )
    action = forms.ModelChoiceField(
        label="Action code",
        queryset=models.MeasureAction.objects.latest_approved(),
        empty_label="-- Please select an action code --",
    )
    applicable_duty = forms.CharField(
        label="Duty",
        required=False,
    )
    condition_sid = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Fieldset(
                Div(
                    Field(
                        "condition_code",
                        template="components/measure_condition_code/template.jinja",
                    ),
                    "condition_sid",
                ),
                Div(
                    Field("reference_price", css_class="govuk-input"),
                    "required_certificate",
                    css_class="govuk-radios__conditional",
                ),
                Field(
                    "action",
                    template="components/measure_condition_action_code/template.jinja",
                ),
                Div(
                    MeasureConditionComponentDuty("applicable_duty"),
                ),
                Field("DELETE", template="includes/common/formset-delete-button.jinja")
                if not self.prefix.endswith("__prefix__")
                else None,
                legend="Condition code",
                legend_size=Size.SMALL,
                data_field="condition_code",
            ),
        )

    def conditions_clean(self, cleaned_data, measure_start_date):
        """
        We get the reference_price from cleaned_data and the measure_start_date
        from the form's initial data.

        If both are present, we call validate_duties with measure_start_date.
        Then, if reference_price is provided, we use DutySentenceParser with
        measure_start_date, if present, or the current_date, to check that we
        are dealing with a simple duty (i.e. only one component). We then update
        cleaned_data with key-value pairs created from this single, unsaved
        component.
        """
        price = cleaned_data.get("reference_price")

        if price and measure_start_date is not None:
            validate_duties(price, measure_start_date)

        if price:
            parser = DutySentenceParser.get(measure_start_date)
            components = parser.parse(price)
            if len(components) > 1:
                raise ValidationError(
                    "A MeasureCondition cannot be created with a compound reference price (e.g. 3.5% + 11 GBP / 100 kg)",
                )
            cleaned_data["duty_amount"] = components[0].duty_amount
            cleaned_data["monetary_unit"] = components[0].monetary_unit
            cleaned_data["condition_measurement"] = components[0].component_measurement

        # The JS autocomplete does not allow for clearing unnecessary certificates
        # In case of a user changing data, the information is cleared here.
        condition_code = cleaned_data.get("condition_code")
        if condition_code and not condition_code.accepts_certificate:
            cleaned_data["required_certificate"] = None

        return cleaned_data


class MeasureConditionsForm(MeasureConditionsFormMixin):
    def get_start_date(self, data):
        """Validates that the day, month, and year start_date fields are present
        in data and then returns the start_date datetime object."""
        validity_form = MeasureValidityForm(data=data)
        validity_form.is_valid()

        return validity_form.cleaned_data["valid_between"].lower

    def clean_applicable_duty(self):
        """
        Gets applicable_duty from cleaned data.

        We get start date from other data in the measure edit form. Uses
        `DutySentenceParser` to check that applicable_duty is a valid duty
        string.
        """
        applicable_duty = self.cleaned_data["applicable_duty"]

        if applicable_duty and self.get_start_date(self.data) is not None:
            validate_duties(applicable_duty, self.get_start_date(self.data))

        return applicable_duty

    def clean(self):
        """
        We get the reference_price from cleaned_data and the measure_start_date
        from the form's initial data.

        If both are present, we call validate_duties with measure_start_date.
        Then, if reference_price is provided, we use DutySentenceParser with
        measure_start_date, if present, or the current_date, to check that we
        are dealing with a simple duty (i.e. only one component). We then update
        cleaned_data with key-value pairs created from this single, unsaved
        component.
        """
        cleaned_data = super().clean()
        measure_start_date = self.get_start_date(self.data)

        return self.conditions_clean(cleaned_data, measure_start_date)


class MeasureConditionsFormSet(FormSet):
    prefix = "measure-conditions-formset"
    form = MeasureConditionsForm


class MeasureConditionsWizardStepForm(MeasureConditionsFormMixin):
    # override methods that use form kwargs
    def __init__(self, *args, **kwargs):
        self.measure_start_date = kwargs.pop("measure_start_date")
        super().__init__(*args, **kwargs)

    def clean_applicable_duty(self):
        """
        Gets applicable_duty from cleaned data.

        We expect `measure_start_date` to be passed in. Uses
        `DutySentenceParser` to check that applicable_duty is a valid duty
        string.
        """
        applicable_duty = self.cleaned_data["applicable_duty"]

        if applicable_duty and self.measure_start_date is not None:
            validate_duties(applicable_duty, self.measure_start_date)

        return applicable_duty

    def clean(self):
        """
        We get the reference_price from cleaned_data and the measure_start_date
        from form kwargs.

        If reference_price is provided, we use DutySentenceParser with
        measure_start_date to check that we are dealing with a simple duty (i.e.
        only one component). We then update cleaned_data with key-value pairs
        created from this single, unsaved component.
        """
        cleaned_data = super().clean()

        return self.conditions_clean(cleaned_data, self.measure_start_date)


class MeasureConditionsWizardStepFormSet(FormSet):
    form = MeasureConditionsWizardStepForm


class MeasureForm(ValidityPeriodForm, BindNestedFormMixin, forms.ModelForm):
    class Meta:
        model = models.Measure
        fields = (
            "valid_between",
            "measure_type",
            "generating_regulation",
            "goods_nomenclature",
            "additional_code",
            "order_number",
        )

    measure_type = AutoCompleteField(
        label="Measure type",
        help_text="Select the regulation which provides the legal basis for the measure.",
        queryset=models.MeasureType.objects.all(),
    )
    generating_regulation = AutoCompleteField(
        label="Regulation ID",
        help_text="Select the regulation which provides the legal basis for the measure.",
        queryset=Regulation.objects.all(),
    )
    goods_nomenclature = AutoCompleteField(
        label="Code and description",
        help_text="Select the 10 digit commodity code to which the measure applies.",
        queryset=GoodsNomenclature.objects.all(),
        required=False,
        attrs={"min_length": 3},
    )
    duty_sentence = forms.CharField(
        label="Duties",
        widget=forms.TextInput,
        required=False,
    )
    additional_code = AutoCompleteField(
        label="Code and description",
        help_text=(
            "Search for an additional code by typing in the code's number or a keyword. "
            "A dropdown list will appear after a few seconds. You can then select the correct code from the dropdown list."
        ),
        queryset=AdditionalCode.objects.all(),
        required=False,
    )
    order_number = AutoCompleteField(
        label="Order number",
        help_text="Enter the quota order number if a quota measure type has been selected. Leave this field blank if the measure is not a quota.",
        queryset=QuotaOrderNumber.objects.all(),
        required=False,
    )
    geo_area = RadioNested(
        label="Geographical area",
        choices=GeoAreaType.choices,
        nested_forms={
            GeoAreaType.ERGA_OMNES.value: [ErgaOmnesExclusionsFormSet],
            GeoAreaType.GROUP.value: [GeoGroupForm, GeoGroupExclusionsFormSet],
            GeoAreaType.COUNTRY.value: [CountryRegionForm],
        },
        error_messages={"required": "A Geographical area must be selected"},
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        tx = WorkBasket.get_current_transaction(self.request)

        self.initial["duty_sentence"] = self.instance.duty_sentence
        self.request.session[
            f"instance_duty_sentence_{self.instance.sid}"
        ] = self.instance.duty_sentence

        if self.instance.geographical_area.is_all_countries():
            self.initial["geo_area"] = GeoAreaType.ERGA_OMNES.value

        elif self.instance.geographical_area.is_group():
            self.initial["geo_area"] = GeoAreaType.GROUP.value

        else:
            self.initial["geo_area"] = GeoAreaType.COUNTRY.value

        # If no footnote keys are stored in the session for a measure,
        # store all the pks of a measure's footnotes on the session, using the measure sid as key
        if f"instance_footnotes_{self.instance.sid}" not in self.request.session.keys():
            tx = WorkBasket.get_current_transaction(self.request)
            associations = (
                models.FootnoteAssociationMeasure.objects.approved_up_to_transaction(
                    tx,
                ).filter(
                    footnoted_measure=self.instance,
                )
            )
            self.request.session[f"instance_footnotes_{self.instance.sid}"] = [
                a.associated_footnote.pk for a in associations
            ]

        nested_forms_initial = {**self.initial}
        nested_forms_initial["geographical_area"] = self.instance.geographical_area
        kwargs.pop("initial")
        self.bind_nested_forms(*args, initial=nested_forms_initial, **kwargs)

    def clean_duty_sentence(self):
        duty_sentence = self.cleaned_data["duty_sentence"]
        valid_between = self.initial.get("valid_between")
        if duty_sentence and valid_between is not None:
            validate_duties(duty_sentence, valid_between.lower)

        return duty_sentence

    def clean(self):
        cleaned_data = super().clean()

        erga_omnes_instance = (
            GeographicalArea.objects.latest_approved()
            .as_at(self.instance.valid_between.lower)
            .get(
                area_code=1,
                area_id=1011,
            )
        )

        geographical_area_fields = {
            GeoAreaType.ERGA_OMNES: erga_omnes_instance,
            GeoAreaType.GROUP: cleaned_data.get("geographical_area_group"),
            GeoAreaType.COUNTRY: cleaned_data.get(
                "geographical_area_country_or_region",
            ),
        }

        if self.data.get("geo_area"):
            geo_area_choice = self.data.get("geo_area")
            cleaned_data["geographical_area"] = geographical_area_fields[
                geo_area_choice
            ]
            exclusions = cleaned_data.get(
                EXCLUSIONS_FORMSET_PREFIX_MAPPING[geo_area_choice],
            )
            if exclusions:
                cleaned_data["exclusions"] = [
                    exclusion[FIELD_NAME_MAPPING[geo_area_choice]]
                    for exclusion in cleaned_data[
                        EXCLUSIONS_FORMSET_PREFIX_MAPPING[geo_area_choice]
                    ]
                ]

        cleaned_data["sid"] = self.instance.sid

        return cleaned_data

    def save(self, commit=True):
        """Get the measure instance after form submission, get from session
        storage any footnote pks created via the Footnote formset and any pks
        not removed from the measure after editing and create footnotes via
        FootnoteAssociationMeasure."""
        instance = super().save(commit=False)
        if commit:
            instance.save()

        sid = instance.sid

        measure_creation_pattern = MeasureCreationPattern(
            workbasket=WorkBasket.current(self.request),
            base_date=instance.valid_between.lower,
            defaults={
                "generating_regulation": self.cleaned_data["generating_regulation"],
            },
        )

        if self.cleaned_data.get("exclusions"):
            for exclusion in self.cleaned_data.get("exclusions"):
                pattern = (
                    measure_creation_pattern.create_measure_excluded_geographical_areas(
                        instance,
                        exclusion,
                    )
                )
                [p for p in pattern]

        if (
            self.request.session[f"instance_duty_sentence_{self.instance.sid}"]
            != self.cleaned_data["duty_sentence"]
        ):
            diff_components(
                instance,
                self.cleaned_data["duty_sentence"],
                self.cleaned_data["valid_between"].lower,
                WorkBasket.current(self.request),
                # Creating components in the same transaction as the new version
                # of the measure minimises number of transaction and groups the
                # creation of measure and related objects in the same
                # transaction.
                instance.transaction,
                models.MeasureComponent,
                "component_measure",
            )

        footnote_pks = [
            dct["footnote"]
            for dct in self.request.session.get(f"formset_initial_{sid}", [])
        ]
        footnote_pks.extend(self.request.session.get(f"instance_footnotes_{sid}", []))

        self.request.session.pop(f"formset_initial_{sid}", None)
        self.request.session.pop(f"instance_footnotes_{sid}", None)

        for pk in footnote_pks:
            footnote = (
                Footnote.objects.filter(pk=pk)
                .approved_up_to_transaction(instance.transaction)
                .first()
            )

            existing_association = (
                models.FootnoteAssociationMeasure.objects.approved_up_to_transaction(
                    instance.transaction,
                )
                .filter(
                    footnoted_measure__sid=instance.sid,
                    associated_footnote__footnote_id=footnote.footnote_id,
                    associated_footnote__footnote_type__footnote_type_id=footnote.footnote_type.footnote_type_id,
                )
                .first()
            )
            if existing_association:
                existing_association.new_version(
                    workbasket=WorkBasket.current(self.request),
                    transaction=instance.transaction,
                    footnoted_measure=instance,
                )
            else:
                models.FootnoteAssociationMeasure.objects.create(
                    footnoted_measure=instance,
                    associated_footnote=footnote,
                    update_type=UpdateType.CREATE,
                    transaction=instance.transaction,
                )

        return instance

    def is_valid(self) -> bool:
        """Check that measure conditions data is valid before calling super() on
        the rest of the form data."""
        conditions_formset = MeasureConditionsFormSet(self.data)

        if not conditions_formset.is_valid():
            return False

        return super().is_valid()


class MeasureFilterForm(forms.Form):
    """Generic Filtering form which adds submit and clear buttons, and adds GDS
    formatting to field types."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.label_size = Size.SMALL
        self.helper.legend_size = Size.SMALL
        self.helper.layout = Layout(
            Div(
                Field.text("sid", field_width=Fluid.TWO_THIRDS),
                "goods_nomenclature",
                "additional_code",
                "order_number",
                "measure_type",
                "regulation",
                "geographical_area",
                "footnote",
                css_class="govuk-grid-row quarters",
            ),
            HTML(
                '<hr class="govuk-section-break govuk-section-break--s govuk-section-break--visible">',
            ),
            Div(
                Div(
                    Field.radios(
                        "start_date_modifier",
                        inline=True,
                    ),
                    "start_date",
                    css_class="govuk-grid-column-one-half form-group-margin-bottom-2",
                ),
                Div(
                    Field.radios(
                        "end_date_modifier",
                        inline=True,
                    ),
                    "end_date",
                    css_class="govuk-grid-column-one-half form-group-margin-bottom-2",
                ),
                css_class="govuk-grid-row govuk-!-margin-top-6",
            ),
            HTML(
                '<hr class="govuk-section-break govuk-section-break--s govuk-section-break--visible">',
            ),
            Button("submit", "Search and Filter", css_class="govuk-!-margin-top-6"),
            HTML(
                f'<a class="govuk-button govuk-button--secondary govuk-!-margin-top-6" href="{self.clear_url}"> Clear </a>',
            ),
        )


class MeasureCreateStartForm(forms.Form):
    pass


class MeasureDetailsForm(
    ValidityPeriodForm,
    forms.Form,
):
    class Meta:
        model = models.Measure
        fields = [
            "measure_type",
            "valid_between",
        ]

    measure_type = AutoCompleteField(
        label="Measure type",
        help_text=(
            "Search for a measure type using its ID number or a keyword. "
            "A dropdown list will appear after a few seconds. "
            "You can then select the measure type from the dropdown list."
        ),
        queryset=models.MeasureType.objects.all(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.label_size = Size.SMALL
        self.helper.legend_size = Size.SMALL
        self.helper.layout = Layout(
            "measure_type",
            "start_date",
            "end_date",
            Submit(
                "submit",
                "Continue",
                data_module="govuk-button",
                data_prevent_double_click="true",
            ),
        )

    def clean(self):
        cleaned_data = super().clean()

        if "measure_type" in cleaned_data and "valid_between" in cleaned_data:
            measure_type = cleaned_data["measure_type"]
            if not validity_range_contains_range(
                measure_type.valid_between,
                cleaned_data["valid_between"],
            ):
                raise ValidationError(
                    f"The date range of the measure can't be outside that of the measure type: "
                    f"{measure_type.valid_between} does not contain {cleaned_data['valid_between']}",
                )

        return cleaned_data


class MeasureRegulationIdForm(forms.Form):
    class Meta:
        model = models.Measure
        fields = [
            "generating_regulation",
        ]

    generating_regulation = AutoCompleteField(
        label="Regulation ID",
        help_text=(
            "Search for a regulation using its ID number or a keyword. "
            "A dropdown list will appear after a few seconds. "
            "You can then select the regulation from the dropdown list."
        ),
        queryset=Regulation.objects.all(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.label_size = Size.SMALL
        self.helper.legend_size = Size.SMALL
        self.helper.layout = Layout(
            "generating_regulation",
            Submit(
                "submit",
                "Continue",
                data_module="govuk-button",
                data_prevent_double_click="true",
            ),
        )


class MeasureQuotaOrderNumberForm(forms.Form):
    class Meta:
        model = models.Measure
        fields = [
            "order_number",
        ]

    order_number = AutoCompleteField(
        label="Quota order number",
        help_text=(
            "Search for a quota using its order number. "
            "You can then select the correct quota from the dropdown list. "
        ),
        queryset=QuotaOrderNumber.objects.all(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.label_size = Size.SMALL
        self.helper.legend_size = Size.SMALL
        self.helper.layout = Layout(
            "order_number",
            HTML.details(
                "I don't know what my quota ID number is",
                f'You can search for the quota number by using <a href="{reverse("quota-ui-list")}" class="govuk-link">find and edit quotas</a>',
            ),
            Submit(
                "submit",
                "Continue",
                data_module="govuk-button",
                data_prevent_double_click="true",
            ),
        )


class MeasureGeographicalAreaForm(BindNestedFormMixin, forms.Form):
    geo_area = RadioNested(
        label="",
        help_text=(
            "Choose the geographical area to which the measure applies. "
            "This can be a specific country or a group of countries, and exclusions can be specified. "
            "The measure will only apply to imports from or exports to the selected area."
        ),
        choices=GeoAreaType.choices,
        nested_forms={
            GeoAreaType.ERGA_OMNES.value: [ErgaOmnesExclusionsFormSet],
            GeoAreaType.GROUP.value: [GeoGroupForm, GeoGroupExclusionsFormSet],
            GeoAreaType.COUNTRY.value: [CountryRegionFormSet],
        },
        error_messages={"required": "A Geographical area must be selected"},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        kwargs.pop("initial")

        self.fields["geo_area"].initial = self.data.get(f"{self.prefix}-geo_area")

        geographical_area_fields = {
            GeoAreaType.ERGA_OMNES: self.erga_omnes_instance,
            GeoAreaType.GROUP: self.data.get(f"{self.prefix}-geographical_area_group"),
            GeoAreaType.COUNTRY: self.data.get(
                f"{self.prefix}-geographical_area_country_or_region",
            ),
        }

        nested_forms_initial = {}

        if self.fields["geo_area"].initial:
            nested_forms_initial["geographical_area"] = geographical_area_fields[
                self.fields["geo_area"].initial
            ]

        self.bind_nested_forms(*args, initial=nested_forms_initial, **kwargs)

        self.helper = FormHelper(self)
        self.helper.label_size = Size.SMALL
        self.helper.legend_size = Size.SMALL
        self.helper.layout = Layout(
            "geo_area",
            Submit(
                "submit",
                "Continue",
                data_module="govuk-button",
                data_prevent_double_click="true",
            ),
        )

    @property
    def erga_omnes_instance(self):
        return GeographicalArea.objects.current().erga_omnes().get()

    def clean(self):
        cleaned_data = super().clean()

        geo_area_choice = self.cleaned_data.get("geo_area")

        geographical_area_fields = {
            GeoAreaType.GROUP: "geographical_area_group",
            GeoAreaType.COUNTRY: "geographical_area_country_or_region",
        }

        if geo_area_choice:
            if not self.formset_submit():
                if geo_area_choice == GeoAreaType.ERGA_OMNES:
                    cleaned_data["geo_area_list"] = [self.erga_omnes_instance]

                elif geo_area_choice == GeoAreaType.GROUP:
                    data_key = SUBFORM_PREFIX_MAPPING[geo_area_choice]
                    cleaned_data["geo_area_list"] = [cleaned_data[data_key]]

                elif geo_area_choice == GeoAreaType.COUNTRY:
                    field_name = geographical_area_fields[geo_area_choice]
                    data_key = SUBFORM_PREFIX_MAPPING[geo_area_choice]
                    cleaned_data["geo_area_list"] = [
                        geo_area[field_name] for geo_area in cleaned_data[data_key]
                    ]

                exclusions = cleaned_data.get(
                    EXCLUSIONS_FORMSET_PREFIX_MAPPING[geo_area_choice],
                )
                if exclusions:
                    cleaned_data["geo_area_exclusions"] = [
                        exclusion[FIELD_NAME_MAPPING[geo_area_choice]]
                        for exclusion in cleaned_data[
                            EXCLUSIONS_FORMSET_PREFIX_MAPPING[geo_area_choice]
                        ]
                    ]

        return cleaned_data


class MeasureAdditionalCodeForm(forms.ModelForm):
    class Meta:
        model = models.Measure
        fields = [
            "additional_code",
        ]

    additional_code = AutoCompleteField(
        label="Additional code",
        help_text=(
            "Search for an additional code by typing in the code's number or a keyword. "
            "A dropdown list will appear after a few seconds. You can then select the correct code from the dropdown list."
        ),
        queryset=AdditionalCode.objects.all(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            "additional_code",
            Submit(
                "submit",
                "Continue",
                data_module="govuk-button",
                data_prevent_double_click="true",
            ),
        )


class MeasureCommodityAndDutiesForm(forms.Form):
    commodity = AutoCompleteField(
        label="Commodity code",
        help_text=(
            "Search for a commodity code by typing in the code's number or a keyword. "
            "After you've typed at least 3 numbers, a dropdown list will appear. "
            "You can then select the correct commodity from the dropdown list."
        ),
        queryset=GoodsNomenclature.objects.all(),
        attrs={"min_length": 3},
        error_messages={"required": "Select a commodity code"},
    )

    duties = forms.CharField(
        label="Duties",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        # remove measure_start_date from kwargs here because superclass will not be expecting it
        self.measure_start_date = kwargs.pop("measure_start_date")
        super().__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.label_size = Size.SMALL
        self.helper.layout = Layout(
            Fieldset(
                "commodity",
                "duties",
                HTML(
                    loader.render_to_string(
                        "components/duty_help.jinja",
                        context={"component": "measure"},
                    ),
                ),
                Field("DELETE", template="includes/common/formset-delete-button.jinja")
                if not self.prefix.endswith("__prefix__")
                else None,
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        duties = cleaned_data.get("duties", "")
        validate_duties(duties, self.measure_start_date)

        return cleaned_data


MeasureCommodityAndDutiesBaseFormSet = formset_factory(
    MeasureCommodityAndDutiesForm,
    prefix="measure_commodities_duties_formset",
    formset=FormSet,
    min_num=1,
    max_num=100,
    extra=1,
    validate_min=True,
    validate_max=True,
)


class MeasureCommodityAndDutiesFormSet(MeasureCommodityAndDutiesBaseFormSet):
    def non_form_errors(self):
        self._non_form_errors = super().non_form_errors()
        for e in self._non_form_errors.as_data():
            if e.code == "too_few_forms":
                e.message = "Select one or more commodity codes"

        return self._non_form_errors


class MeasureFootnotesForm(forms.Form):
    footnote = AutoCompleteField(
        label="",
        help_text=(
            "Search for a footnote by typing in the footnote's number or a keyword. "
            "A dropdown list will appear after a few seconds. You can then select the correct footnote from the dropdown list."
        ),
        queryset=Footnote.objects.all(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.legend_size = Size.SMALL
        self.helper.layout = Layout(
            Fieldset(
                "footnote",
                Field("DELETE", template="includes/common/formset-delete-button.jinja")
                if not self.prefix.endswith("__prefix__")
                else None,
                legend="Footnote",
                legend_size=Size.SMALL,
            ),
        )


class MeasureFootnotesFormSet(FormSet):
    form = MeasureFootnotesForm


class MeasureUpdateFootnotesForm(MeasureFootnotesForm):
    """
    Used with edit measure, this form has two buttons each submitting to
    different routes: one for submitting to the edit measure view
    (MeasureUpdate) and the other for submitting to the edit measure footnote
    view (MeasureFootnotesUpdate).

    This is done by setting the submit button's "formaction" attribute. This
    requires that the path is passed here on kwargs, allowing it to be accessed
    and used when rendering the edit forms' submit buttons.
    """

    def __init__(self, *args, **kwargs):
        path = kwargs.pop("path")
        if "edit" in path:
            self.path = path[:-1] + "-footnotes/"

        super().__init__(*args, **kwargs)


class MeasureUpdateFootnotesFormSet(FormSet):
    form = MeasureUpdateFootnotesForm


class MeasureReviewForm(forms.Form):
    pass


MeasureDeleteForm = delete_form_for(models.Measure)


class MeasureEndDateForm(forms.Form):
    end_date = DateInputFieldFixed(
        label="End date",
        help_text="For example, 27 3 2008",
    )

    def __init__(self, *args, **kwargs):
        self.selected_measures = kwargs.pop("selected_measures", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.label_size = Size.SMALL
        self.helper.legend_size = Size.SMALL
        self.helper.layout = Layout(
            "end_date",
            Submit(
                "submit",
                "Save measure end dates",
                data_module="govuk-button",
                data_prevent_double_click="true",
            ),
        )

    def clean(self):
        cleaned_data = super().clean()

        if "end_date" in cleaned_data:
            for measure in self.selected_measures:
                year = int(cleaned_data["end_date"].year)
                month = int(cleaned_data["end_date"].month)
                day = int(cleaned_data["end_date"].day)

                lower = measure.valid_between.lower
                upper = datetime.date(year, month, day)
                if lower > upper:
                    formatted_lower = lower.strftime("%d/%m/%Y")
                    formatted_upper = upper.strftime("%d/%m/%Y")
                    raise ValidationError(
                        f"The end date cannot be before the start date: "
                        f"Start date {formatted_lower} does not start before {formatted_upper}",
                    )

        return cleaned_data


class MeasureStartDateForm(forms.Form):
    start_date = DateInputFieldFixed(
        label="Start date",
        help_text="For example, 27 3 2008",
    )

    def __init__(self, *args, **kwargs):
        self.selected_measures = kwargs.pop("selected_measures", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.label_size = Size.SMALL
        self.helper.legend_size = Size.SMALL
        self.helper.layout = Layout(
            "start_date",
            Submit(
                "submit",
                "Save measure start dates",
                data_module="govuk-button",
                data_prevent_double_click="true",
            ),
        )

    def clean(self):
        cleaned_data = super().clean()

        if "start_date" in cleaned_data:
            for measure in self.selected_measures:
                year = int(cleaned_data["start_date"].year)
                month = int(cleaned_data["start_date"].month)
                day = int(cleaned_data["start_date"].day)

                upper = measure.valid_between.upper
                lower = datetime.date(year, month, day)
                # for an open-ended measure the end date can be None
                if upper and lower > upper:
                    formatted_lower = lower.strftime("%d/%m/%Y")
                    formatted_upper = upper.strftime("%d/%m/%Y")
                    raise ValidationError(
                        f"The start date cannot be after the end date: "
                        f"Start date {formatted_lower} does not start before {formatted_upper}",
                    )

        return cleaned_data


class MeasuresEditFieldsForm(forms.Form):
    fields_to_edit = forms.MultipleChoiceField(
        choices=MeasureEditSteps.choices,
        widget=forms.CheckboxSelectMultiple,
        label="",
        help_text="Select the fields you wish to edit",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.legend_size = Size.SMALL
        self.helper.layout = Layout(
            Fieldset(
                "fields_to_edit",
            ),
            Submit(
                "submit",
                "Continue",
                data_module="govuk-button",
                data_prevent_double_click="true",
            ),
        )


class MeasureRegulationForm(forms.Form):
    generating_regulation = AutoCompleteField(
        label="Regulation ID",
        help_text="Select the regulation which provides the legal basis for the measures.",
        queryset=Regulation.objects.all(),
    )

    def __init__(self, *args, **kwargs):
        self.selected_measures = kwargs.pop("selected_measures", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.legend_size = Size.SMALL
        self.helper.layout = Layout(
            Fieldset(
                "generating_regulation",
            ),
            Submit(
                "submit",
                "Save measure regulations",
                data_module="govuk-button",
                data_prevent_double_click="true",
            ),
        )
