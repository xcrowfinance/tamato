from datetime import date
from typing import Set

from django.db import models

from common.business_rules import UniqueIdentifyingFields
from common.business_rules import UpdateValidity
from common.fields import ApplicabilityCode
from common.fields import ShortDescription
from common.fields import SignedIntSID
from common.models import TrackedModel
from common.models.managers import TrackedModelManager
from common.models.mixins.validity import ValidityMixin
from common.util import TaricDateRange
from common.util import classproperty
from common.validators import UpdateType
from footnotes import validators as footnote_validators
from measures import business_rules
from measures import validators
from measures.querysets import MeasureConditionQuerySet
from measures.querysets import MeasuresQuerySet
from quotas import business_rules as quotas_business_rules
from quotas.validators import quota_order_number_validator
from workbaskets.models import WorkBasket


class MeasureTypeSeries(TrackedModel, ValidityMixin):
    """
    Measure types may be grouped into series.

    The series can be used to determine how duties are applied, and the possible
    cumulative effect of other applicable measures.
    """

    record_code = "140"
    subrecord_code = "00"

    description_record_code = "140"
    description_subrecord_code = "05"

    identifying_fields = ("sid",)

    sid = models.CharField(
        max_length=2,
        validators=[validators.measure_type_series_id_validator],
        db_index=True,
    )
    measure_type_combination = models.PositiveSmallIntegerField(
        choices=validators.MeasureTypeCombination.choices,
    )
    description = ShortDescription()

    indirect_business_rules = (business_rules.MT10,)
    business_rules = (
        business_rules.MTS1,
        business_rules.MTS2,
        UpdateValidity,
    )


class MeasurementUnit(TrackedModel, ValidityMixin):
    """The measurement unit refers to the ISO measurement unit code."""

    record_code = "210"
    subrecord_code = "00"

    description_record_code = "210"
    description_subrecord_code = "05"

    code = models.CharField(
        max_length=3,
        validators=[validators.measurement_unit_code_validator],
        db_index=True,
    )
    description = ShortDescription()
    abbreviation = models.CharField(max_length=32, blank=True)

    identifying_fields = ("code",)

    indirect_business_rules = (
        business_rules.ME51,
        business_rules.ME63,
    )

    business_rules = (UpdateValidity,)


class MeasurementUnitQualifier(TrackedModel, ValidityMixin):
    """
    The measurement unit qualifier is used to qualify a measurement unit.

    For example the measurement unit "kilogram" may be qualified as "net" or
    "gross".
    """

    record_code = "215"
    subrecord_code = "00"

    description_record_code = "215"
    description_subrecord_code = "05"

    code = models.CharField(
        max_length=1,
        validators=[validators.measurement_unit_qualifier_code_validator],
        db_index=True,
    )
    description = ShortDescription()
    abbreviation = models.CharField(max_length=32, blank=True)

    identifying_fields = ("code",)

    indirect_business_rules = (
        business_rules.ME52,
        business_rules.ME64,
        quotas_business_rules.QD11,
    )

    business_rules = (UpdateValidity,)


class Measurement(TrackedModel, ValidityMixin):
    """
    The measurement defines the relationship between a measurement unit and a
    measurement unit qualifier.

    This avoids meaningless combinations of the measurement unit and the
    measurement unit qualifier. Unlike in the TARIC model, we put all
    combinations of measurement in this table including ones where the qualifier
    is null. These do not appear in output XML.
    """

    record_code = "220"
    subrecord_code = "00"

    measurement_unit = models.ForeignKey("MeasurementUnit", on_delete=models.PROTECT)
    measurement_unit_qualifier = models.ForeignKey(
        "MeasurementUnitQualifier",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
    )

    identifying_fields = ("measurement_unit", "measurement_unit_qualifier")

    indirect_business_rules = (
        business_rules.ME50,
        business_rules.ME62,
    )

    business_rules = (UpdateValidity,)


class MonetaryUnit(TrackedModel, ValidityMixin):
    """The monetary unit identifies the currency code used in the system."""

    record_code = "225"
    subrecord_code = "00"

    description_record_code = "225"
    description_subrecord_code = "05"

    code = models.CharField(
        max_length=3,
        validators=[validators.monetary_unit_code_validator],
        db_index=True,
    )
    description = ShortDescription()

    identifying_fields = ("code",)

    indirect_business_rules = (
        business_rules.ME48,
        business_rules.ME49,
        business_rules.ME60,
        business_rules.ME61,
        quotas_business_rules.QD8,
    )

    business_rules = (UpdateValidity,)


class DutyExpression(TrackedModel, ValidityMixin):
    """
    The duty expression identifies the type of duty which must be applied for a
    given measure component.

    It will also control how the duty will be expressed, for example whether an
    amount is "permitted" or "mandatory".
    """

    record_code = "230"
    subrecord_code = "00"

    description_record_code = "230"
    description_subrecord_code = "05"

    identifying_fields = ("sid",)

    sid = models.IntegerField(
        choices=validators.DutyExpressionId.choices,
        db_index=True,
    )
    prefix = models.CharField(max_length=14, blank=True)
    duty_amount_applicability_code = ApplicabilityCode()
    measurement_unit_applicability_code = ApplicabilityCode()
    monetary_unit_applicability_code = ApplicabilityCode()
    description = ShortDescription()

    indirect_business_rules = (
        business_rules.ME40,
        business_rules.ME42,
        business_rules.ME45,
        business_rules.ME46,
        business_rules.ME47,
        business_rules.ME105,
        business_rules.ME106,
        business_rules.ME109,
        business_rules.ME110,
        business_rules.ME111,
    )

    business_rules = (UniqueIdentifyingFields, UpdateValidity)


class MeasureType(TrackedModel, ValidityMixin):
    """
    The measure type identifies a customs measure.

    TARIC customs measures cover a wide range of information, including tariff
    measures (such as levies and anti-dumping duties), and non-tariff measures
    (such as quantitative restrictions and prohibitions).
    """

    record_code = "235"
    subrecord_code = "00"

    description_record_code = "235"
    description_subrecord_code = "05"

    identifying_fields = ("sid",)

    sid = models.CharField(
        max_length=6,
        validators=[validators.measure_type_id_validator],
        db_index=True,
    )
    trade_movement_code = models.PositiveSmallIntegerField(
        choices=validators.ImportExportCode.choices,
    )
    priority_code = models.PositiveSmallIntegerField(
        validators=[validators.validate_priority_code],
    )
    measure_component_applicability_code = ApplicabilityCode()
    origin_destination_code = models.PositiveSmallIntegerField(
        choices=validators.ImportExportCode.choices,
    )
    order_number_capture_code = models.PositiveSmallIntegerField(
        choices=validators.OrderNumberCaptureCode.choices,
    )
    measure_explosion_level = models.PositiveSmallIntegerField(
        choices=validators.MeasureExplosionLevel.choices,
        validators=[validators.validate_measure_explosion_level],
    )
    description = ShortDescription()
    measure_type_series = models.ForeignKey(MeasureTypeSeries, on_delete=models.PROTECT)

    additional_code_types = models.ManyToManyField(
        "additional_codes.AdditionalCodeType",
        through="AdditionalCodeTypeMeasureType",
    )

    indirect_business_rules = (
        business_rules.ME1,
        business_rules.ME10,
        business_rules.ME88,
    )
    business_rules = (
        business_rules.MT1,
        business_rules.MT3,
        business_rules.MT4,
        business_rules.MT7,
        business_rules.MT10,
        UpdateValidity,
    )

    def __str__(self):
        return str(self.sid)

    @property
    def autocomplete_label(self):
        return f"{self} - {self.description}"

    @property
    def components_mandatory(self):
        return (
            self.measure_component_applicability_code
            == validators.ApplicabilityCode.MANDATORY
        )

    @property
    def components_not_permitted(self):
        return (
            self.measure_component_applicability_code
            == validators.ApplicabilityCode.NOT_PERMITTED
        )

    @property
    def order_number_mandatory(self):
        return self.order_number_capture_code == validators.ApplicabilityCode.MANDATORY

    @property
    def order_number_not_permitted(self):
        return (
            self.order_number_capture_code == validators.ApplicabilityCode.NOT_PERMITTED
        )


class AdditionalCodeTypeMeasureType(TrackedModel, ValidityMixin):
    """The relation between an additional code type and a measure type ensures a
    coherent association between additional codes and measures."""

    record_code = "240"
    subrecord_code = "00"

    measure_type = models.ForeignKey(MeasureType, on_delete=models.PROTECT)
    additional_code_type = models.ForeignKey(
        "additional_codes.AdditionalCodeType",
        on_delete=models.PROTECT,
    )

    identifying_fields = ("measure_type", "additional_code_type")

    business_rules = (UpdateValidity,)


class MeasureConditionCode(TrackedModel, ValidityMixin):
    """A measure condition code identifies a broad area where conditions are
    required, for example "C" will have the description "required to present a
    certificate"."""

    record_code = "350"
    subrecord_code = "00"

    description_record_code = "350"
    description_subrecord_code = "05"

    code = models.CharField(
        max_length=2,
        validators=[validators.measure_condition_code_validator],
        db_index=True,
    )
    description = ShortDescription()
    # A measure condition code must be created with one or both of
    # accepts_certificate and accepts_price set to True,
    # though a condition should only ever have one of either required_certificate or duty_amount set.
    accepts_certificate = models.BooleanField(default=False)
    accepts_price = models.BooleanField(default=False)

    identifying_fields = ("code",)

    business_rules = (
        business_rules.MC1,
        business_rules.MC4,
        UpdateValidity,
    )

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.description}"


class MeasureAction(TrackedModel, ValidityMixin):
    """
    The measure action identifies the action to take when a given condition is
    met.

    For example, the description of "01" will be "apply ACTION AMOUNT".
    """

    record_code = "355"
    subrecord_code = "00"

    description_record_code = "355"
    description_subrecord_code = "05"

    code = models.CharField(
        max_length=3,
        validators=[validators.validate_action_code],
        db_index=True,
    )
    description = ShortDescription()
    requires_duty = models.BooleanField(default=False)

    identifying_fields = ("code",)

    indirect_business_rules = (
        business_rules.MA4,
        business_rules.ME59,
    )
    business_rules = (
        business_rules.MA1,
        business_rules.MA2,
        UpdateValidity,
    )

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.description}"


class Measure(TrackedModel, ValidityMixin):
    """
    Defines the validity period in which a particular measure type is applicable
    to particular nomenclature for a particular geographical area.

    Measures in the TARIC database are stored against the nomenclature code
    which is at the highest level appropriate in the hierarchy. Thus, measures
    which apply to all the declarable codes in a complete chapter are stored
    against the nomenclature code for the chapter (i.e. at the 2-digit level
    only); those which apply to all sub-divisions of an HS code are stored
    against that HS code (i.e. at the 6-digit level only). The advantage of this
    system is that it reduces the number of measures stored in the database; the
    data capture workload (thus diminishing the possibility of introducing
    errors) and the transmission volumes.
    """

    record_code = "430"
    subrecord_code = "00"

    sid = SignedIntSID(db_index=True)
    measure_type = models.ForeignKey(MeasureType, on_delete=models.PROTECT)
    geographical_area = models.ForeignKey(
        "geo_areas.GeographicalArea",
        on_delete=models.PROTECT,
        related_name="measures",
    )
    goods_nomenclature = models.ForeignKey(
        "commodities.GoodsNomenclature",
        on_delete=models.PROTECT,
        related_name="measures",
        null=True,
        blank=True,
    )
    additional_code = models.ForeignKey(
        "additional_codes.AdditionalCode",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    dead_additional_code = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        db_index=True,
    )
    order_number = models.ForeignKey(
        "quotas.QuotaOrderNumber",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    dead_order_number = models.CharField(
        max_length=6,
        validators=[quota_order_number_validator],
        null=True,
        blank=True,
        db_index=True,
    )
    reduction = models.PositiveSmallIntegerField(
        validators=[validators.validate_reduction_indicator],
        null=True,
        blank=True,
        db_index=True,
    )
    generating_regulation = models.ForeignKey(
        "regulations.Regulation",
        on_delete=models.PROTECT,
    )
    terminating_regulation = models.ForeignKey(
        "regulations.Regulation",
        on_delete=models.PROTECT,
        related_name="terminated_measures",
        null=True,
        blank=True,
    )
    stopped = models.BooleanField(default=False)
    export_refund_nomenclature_sid = SignedIntSID(null=True, blank=True, default=None)

    footnotes = models.ManyToManyField(
        "footnotes.Footnote",
        through="FootnoteAssociationMeasure",
    )

    identifying_fields = ("sid",)

    indirect_business_rules = (
        business_rules.MA4,
        business_rules.MC3,
        business_rules.ME42,
        business_rules.ME49,
        business_rules.ME61,
        business_rules.ME65,
        business_rules.ME66,
        business_rules.ME67,
        business_rules.ME71,
        business_rules.ME73,
    )
    business_rules = (
        business_rules.ME1,
        business_rules.ME2,
        business_rules.ME3,
        business_rules.ME4,
        business_rules.ME5,
        business_rules.ME6,
        business_rules.ME7,
        business_rules.ME8,
        business_rules.ME88,
        business_rules.ME16,
        business_rules.ME115,
        business_rules.ME25,
        business_rules.ME32,
        business_rules.ME10,
        business_rules.ME116,
        business_rules.ME119,
        business_rules.ME9,
        business_rules.ME12,
        business_rules.ME17,
        business_rules.ME24,
        business_rules.ME87,
        business_rules.ME33,
        business_rules.ME34,
        business_rules.ME40,
        business_rules.ME45,
        business_rules.ME46,
        business_rules.ME47,
        business_rules.ME109,
        business_rules.ME110,
        business_rules.ME111,
        business_rules.ME104,
        UniqueIdentifyingFields,
        UpdateValidity,
    )

    objects = TrackedModelManager.from_queryset(MeasuresQuerySet)()

    @property
    def footnote_application_codes(self) -> Set[footnote_validators.ApplicationCode]:
        codes = {footnote_validators.ApplicationCode.DYNAMIC_FOOTNOTE}
        if self.goods_nomenclature:
            codes.add(footnote_validators.ApplicationCode.OTHER_MEASURES)
        if not self.goods_nomenclature.is_taric_code:
            codes.add(footnote_validators.ApplicationCode.CN_MEASURES)
        return codes

    validity_field_name = "db_effective_valid_between"

    @property
    def effective_end_date(self) -> date:
        """Measure end dates may be overridden by regulations."""
        if not hasattr(self, self.validity_field_name):
            effective_valid_between = (
                type(self)
                .objects.with_validity_field()
                .filter(pk=self.pk)
                .get()
                .db_effective_valid_between
            )
            setattr(self, self.validity_field_name, effective_valid_between)

        return getattr(self, self.validity_field_name).upper

    def __str__(self):
        return str(self.sid)

    @property
    def effective_valid_between(self) -> TaricDateRange:
        if hasattr(self, self.validity_field_name):
            return getattr(self, self.validity_field_name)

        return TaricDateRange(self.valid_between.lower, self.effective_end_date)

    @classproperty
    def auto_value_fields(cls):
        """Remove export refund SID because we don't want to auto-increment it –
        it should really be a foreign key to an ExportRefundNomenclature model
        but as we don't use them in the UK Tariff we don't store them."""
        counters = super().auto_value_fields
        counters.remove(cls._meta.get_field("export_refund_nomenclature_sid"))
        return counters

    def has_components(self, transaction):
        return (
            MeasureComponent.objects.approved_up_to_transaction(transaction)
            .filter(component_measure__sid=self.sid)
            .exists()
        )

    def has_condition_components(self, transaction):
        return (
            MeasureConditionComponent.objects.approved_up_to_transaction(transaction)
            .filter(condition__dependent_measure__sid=self.sid)
            .exists()
        )

    def terminate(self, workbasket, when: date):
        """
        Returns a new version of the measure updated to end on the specified
        date.

        If the measure would not have started on that date, the measure is
        deleted instead. If the measure will already have ended by this date,
        then does nothing.
        """
        update_params = {}
        if not self.terminating_regulation:
            update_params["terminating_regulation"] = self.generating_regulation

        return super().terminate(workbasket, when, **update_params)

    def save(self, *args, force_write=False, **kwargs):
        """If the commodity code is being changed on an existing measure, the
        measure is deleted instead of doing an `UPDATE` and a new measure
        created with the updated commodity code."""
        if (
            self.update_type == UpdateType.UPDATE
            and self.get_versions().order_by("transaction__order").last()
        ):
            previous = self.get_versions().order_by("transaction__order").last()
            try:
                nomenclature_removed = not (
                    previous.goods_nomenclature and self.goods_nomenclature
                )
            except type(previous.goods_nomenclature).DoesNotExist:
                return super().save(*args, force_write=force_write, **kwargs)
            nomenclature_changed = (
                True
                if nomenclature_removed
                else self.goods_nomenclature.sid != previous.goods_nomenclature.sid
            )
            if nomenclature_changed:
                self.update_type = UpdateType.DELETE
                instance = super().save(*args, force_write=force_write, **kwargs)
                return self.copy(self.transaction)

        return super().save(*args, force_write=force_write, **kwargs)

    def diff_components(
        self,
        duty_sentence: str,
        start_date: date,
        workbasket: WorkBasket,
    ):
        from measures.parsers import DutySentenceParser

        parser = DutySentenceParser.get(
            start_date,
        )

        new_components = parser.parse(duty_sentence)
        old_components = self.components.approved_up_to_transaction(
            workbasket.current_transaction,
        )
        new_by_id = {c.duty_expression.id: c for c in new_components}
        old_by_id = {c.duty_expression.id: c for c in old_components}
        all_ids = set(new_by_id.keys()) | set(old_by_id.keys())
        update_transaction = None
        for id in all_ids:
            new = new_by_id.get(id)
            old = old_by_id.get(id)
            if new and old:
                # Component is having amount/unit changed – UPDATE it
                new.update_type = UpdateType.UPDATE
                new.version_group = old.version_group
                new.component_measure = self
                if not update_transaction:
                    update_transaction = workbasket.new_transaction()
                new.transaction = update_transaction
                new.save()

            elif new:
                # Component exists only in new set - CREATE it
                new.update_type = UpdateType.CREATE
                new.component_measure = self
                new.transaction = workbasket.new_transaction()
                new.save()

            elif old:
                # Component exists only in old set – DELETE it
                old = old.new_version(
                    workbasket,
                    update_type=UpdateType.DELETE,
                    transaction=workbasket.new_transaction(),
                )


class MeasureComponent(TrackedModel):
    """Contains the duty information or part of the duty information."""

    record_code = "430"
    subrecord_code = "05"

    component_measure = models.ForeignKey(
        Measure,
        on_delete=models.PROTECT,
        related_name="components",
    )
    duty_expression = models.ForeignKey(DutyExpression, on_delete=models.PROTECT)
    duty_amount = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
    )
    monetary_unit = models.ForeignKey(
        MonetaryUnit,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    component_measurement = models.ForeignKey(
        Measurement,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    identifying_fields = ("component_measure__sid", "duty_expression__sid")

    indirect_business_rules = (
        business_rules.ME40,
        business_rules.ME45,
        business_rules.ME46,
        business_rules.ME47,
    )
    business_rules = (
        business_rules.ME41,
        business_rules.ME42,
        business_rules.ME43,
        business_rules.ME48,
        business_rules.ME49,
        business_rules.ME50,
        business_rules.ME51,
        business_rules.ME52,
        UpdateValidity,
    )


class MeasureCondition(TrackedModel):
    """
    A measure may be dependent on conditions.

    These are expressed in a series of conditions, each having zero or more
    components. Conditions for the same condition type will have sequence
    numbers. Conditions of different types may be combined.
    """

    record_code = "430"
    subrecord_code = "10"

    identifying_fields = ("sid",)

    sid = SignedIntSID(db_index=True)
    dependent_measure = models.ForeignKey(
        Measure,
        on_delete=models.PROTECT,
        related_name="conditions",
    )
    condition_code = models.ForeignKey(
        MeasureConditionCode,
        on_delete=models.PROTECT,
        related_name="conditions",
    )
    component_sequence_number = models.PositiveSmallIntegerField(
        validators=[validators.validate_component_sequence_number],
    )
    duty_amount = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
    )
    monetary_unit = models.ForeignKey(
        MonetaryUnit,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    condition_measurement = models.ForeignKey(
        Measurement,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    action = models.ForeignKey(
        MeasureAction,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    required_certificate = models.ForeignKey(
        "certificates.Certificate",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    objects = TrackedModelManager.from_queryset(MeasureConditionQuerySet)()

    indirect_business_rules = (
        business_rules.MA2,
        business_rules.MC4,
        business_rules.ME53,
    )
    business_rules = (
        business_rules.MC3,
        business_rules.MA4,
        business_rules.ME56,
        business_rules.ME57,
        business_rules.ME58,
        business_rules.ME59,
        business_rules.ME60,
        business_rules.ME61,
        business_rules.ME62,
        business_rules.ME63,
        business_rules.ME64,
        business_rules.ActionRequiresDuty,
        business_rules.ConditionCodeAcceptance,
        UniqueIdentifyingFields,
        UpdateValidity,
    )

    class Meta:
        ordering = [
            "dependent_measure__sid",
            "condition_code__code",
            "component_sequence_number",
        ]

    def is_certificate_required(self):
        return self.condition_code.code in ("A", "B", "C", "H", "Q", "Y", "Z")

    @property
    def description(self) -> str:
        out: list[str] = []

        out.append(
            f"Condition of type {self.condition_code.code} - {self.condition_code.description}",
        )

        if self.required_certificate:
            out.append(
                f"On presentation of certificate {self.required_certificate.code},",
            )
        elif self.is_certificate_required():
            out.append("On presentation of no certificate,")

        if hasattr(self, "reference_price_string") and self.reference_price_string:
            out.append(f"If reference price > {self.reference_price_string},")

        out.append(f"perform action {self.action.code} - {self.action.description}")

        if self.condition_string:
            out.append(f"\n\nApplicable duty is {self.condition_string}")

        return " ".join(out)

    @property
    def condition_string(self) -> str:
        out: list[str] = []

        components = self.components.latest_approved()
        measures: set[str] = set()
        measure_types: set[str] = set()
        additional_codes: set[str] = set()

        for mcc in components:
            measures.add(mcc.condition.dependent_measure.sid)
            measure_types.add(mcc.condition.dependent_measure.measure_type.sid)
            if mcc.condition.dependent_measure.additional_code:
                additional_codes.add(
                    mcc.condition.dependent_measure.additional_code.sid,
                )

        if (
            len(measures) == len(measure_types) == len(additional_codes) == 1
            or len(measure_types) > 1
            or len(additional_codes) > 1
        ):
            out.append(self.duty_sentence)

        return "".join(out)


class MeasureConditionComponent(TrackedModel):
    """Contains the duty information or part of the duty information of the
    measure condition."""

    record_code = "430"
    subrecord_code = "11"

    condition = models.ForeignKey(
        MeasureCondition,
        on_delete=models.PROTECT,
        related_name="components",
    )
    duty_expression = models.ForeignKey("DutyExpression", on_delete=models.PROTECT)
    duty_amount = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        null=True,
        blank=True,
    )
    monetary_unit = models.ForeignKey(
        MonetaryUnit,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    component_measurement = models.ForeignKey(
        Measurement,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    identifying_fields = ("condition__sid", "duty_expression__sid")

    class Meta:
        ordering = [
            "condition__sid",
            "duty_expression__sid",
        ]

    indirect_business_rules = (
        business_rules.ME109,
        business_rules.ME110,
        business_rules.ME111,
        business_rules.ME40,
    )
    business_rules = (
        business_rules.ME53,
        business_rules.ME105,
        business_rules.ME106,
        business_rules.ME108,
        UpdateValidity,
    )


class MeasureExcludedGeographicalArea(TrackedModel):
    """The measure excluded geographical area modifies the applicable
    geographical area of a measure, which must be a geographical area group."""

    record_code = "430"
    subrecord_code = "15"

    identifying_fields = ("modified_measure__sid", "excluded_geographical_area__sid")

    modified_measure = models.ForeignKey(
        Measure,
        on_delete=models.PROTECT,
        related_name="exclusions",
    )
    excluded_geographical_area = models.ForeignKey(
        "geo_areas.GeographicalArea",
        on_delete=models.PROTECT,
    )

    business_rules = (
        business_rules.ME65,
        business_rules.ME66,
        business_rules.ME67,
        business_rules.ME68,
        UpdateValidity,
    )


class FootnoteAssociationMeasure(TrackedModel):
    """The association of a footnote and a measure is always applicable for the
    entire period of the measure."""

    record_code = "430"
    subrecord_code = "20"

    footnoted_measure = models.ForeignKey(Measure, on_delete=models.PROTECT)
    associated_footnote = models.ForeignKey(
        "footnotes.Footnote",
        on_delete=models.PROTECT,
    )

    identifying_fields = (
        "footnoted_measure__sid",
        "associated_footnote__footnote_id",
        "associated_footnote__footnote_type__footnote_type_id",
    )

    business_rules = (
        business_rules.ME69,
        business_rules.ME70,
        business_rules.ME71,
        business_rules.ME73,
        UpdateValidity,
    )
