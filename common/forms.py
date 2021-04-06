from datetime import date

from crispy_forms_gds.fields import DateInputField
from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field
from crispy_forms_gds.layout import Layout
from crispy_forms_gds.layout import Size
from crispy_forms_gds.layout import Submit
from django import forms
from django.contrib.postgres.forms.ranges import DateRangeField
from django.core.exceptions import ValidationError

from common.util import TaricDateRange


class DateInputFieldFixed(DateInputField):
    def compress(self, data_list):
        day, month, year = data_list or [None, None, None]
        if day and month and year:
            return date(day=int(day), month=int(month), year=int(year))
        else:
            return None


class GovukDateRangeField(DateRangeField):
    base_field = DateInputFieldFixed

    def clean(self, value):
        """Validate the date range input `value` should be a 2-tuple or list or
        datetime objects or None."""
        clean_data = []
        errors = []
        if self.disabled and not isinstance(value, list):
            value = self.widget.decompress(value)

        # start date is always required
        if not value:
            raise ValidationError(self.error_messages["required"], code="required")

        # somehow we didn't get a list or tuple of datetimes
        if not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages["invalid"], code="invalid")

        for i, (field, value) in enumerate(zip(self.fields, value)):
            limit = ("start", "end")[i]

            if value in self.empty_values and (
                limit == "lower" or self.require_all_fields
            ):
                error = ValidationError(
                    self.error_messages[f"{limit}_required"],
                    code=f"{limit}_required",
                )
                error.subfield = i
                raise error

            try:
                clean_data.append(field.clean(value))
            except ValidationError as e:
                for error in e.error_list:
                    if "Enter a valid date" in str(error):
                        error.message = f"Enter a valid {limit} date."
                    error.subfield = i
                    errors.append(error)

        if errors:
            raise ValidationError(errors)

        out = self.compress(clean_data)
        self.validate(out)
        self.run_validators(out)
        return out


class DescriptionForm(forms.ModelForm):
    start_date = DateInputFieldFixed(
        label="Start date",
    )

    description = forms.CharField(
        help_text="Edit or overwrite the existing description",
        widget=forms.Textarea,
    )

    valid_between = GovukDateRangeField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.valid_between.lower:
            self.fields["start_date"].initial = self.instance.valid_between.lower
        if self.instance.valid_between.upper:
            self.fields["end_date"].initial = self.instance.valid_between.upper

        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Field("start_date", context={"legend_size": "govuk-label--s"}),
            Field.textarea("description", label_size=Size.SMALL, rows=5),
            Submit("submit", "Save"),
        )

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.pop("start_date", None)
        cleaned_data["valid_between"] = TaricDateRange(
            start_date,
            self.instance.valid_between.upper,
        )

        return cleaned_data

    class Meta:
        fields = ("description", "valid_between")
