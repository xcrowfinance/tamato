from rest_framework import serializers

from additional_codes.serializers import AdditionalCodeSerializer
from additional_codes.serializers import AdditionalCodeTypeSerializer
from certificates.serializers import CertificateSerializer
from commodities.serializers import GoodsNomenclatureSerializer
from common.serializers import TrackedModelSerializer
from common.serializers import TrackedModelSerializerMixin
from common.serializers import ValiditySerializerMixin
from footnotes.serializers import FootnoteSerializer
from geo_areas.serializers import GeographicalAreaSerializer
from measures import models
from quotas.serializers import QuotaOrderNumberSerializer
from regulations.serializers import RegulationSerializer


@TrackedModelSerializer.register_polymorphic_model
class MeasureTypeSeriesSerializer(TrackedModelSerializerMixin, ValiditySerializerMixin):
    class Meta:
        model = models.MeasureTypeSeries
        fields = [
            "sid",
            "measure_type_combination",
            "description",
            "valid_between",
            "update_type",
            "record_code",
            "subrecord_code",
            "description_record_code",
            "description_subrecord_code",
            "taric_template",
            "start_date",
            "end_date",
        ]


@TrackedModelSerializer.register_polymorphic_model
class MeasurementUnitSerializer(TrackedModelSerializerMixin, ValiditySerializerMixin):
    class Meta:
        model = models.MeasurementUnit
        fields = [
            "code",
            "description",
            "valid_between",
            "update_type",
            "record_code",
            "subrecord_code",
            "description_record_code",
            "description_subrecord_code",
            "taric_template",
            "start_date",
            "end_date",
        ]


@TrackedModelSerializer.register_polymorphic_model
class MeasurementUnitQualifierSerializer(
    TrackedModelSerializerMixin, ValiditySerializerMixin
):
    class Meta:
        model = models.MeasurementUnitQualifier
        fields = [
            "code",
            "description",
            "valid_between",
            "update_type",
            "record_code",
            "subrecord_code",
            "description_record_code",
            "description_subrecord_code",
            "taric_template",
            "start_date",
            "end_date",
        ]


@TrackedModelSerializer.register_polymorphic_model
class MeasurementSerializer(TrackedModelSerializerMixin, ValiditySerializerMixin):
    measurement_unit = MeasurementUnitSerializer(read_only=True)
    measurement_unit_qualifier = MeasurementUnitQualifierSerializer(read_only=True)

    class Meta:
        model = models.Measurement
        fields = [
            "measurement_unit",
            "measurement_unit_qualifier",
            "valid_between",
            "update_type",
            "record_code",
            "subrecord_code",
            "taric_template",
            "start_date",
            "end_date",
        ]


@TrackedModelSerializer.register_polymorphic_model
class MonetaryUnitSerializer(TrackedModelSerializerMixin, ValiditySerializerMixin):
    class Meta:
        model = models.MonetaryUnit
        fields = [
            "code",
            "description",
            "valid_between",
            "update_type",
            "record_code",
            "subrecord_code",
            "description_record_code",
            "description_subrecord_code",
            "taric_template",
            "start_date",
            "end_date",
        ]


@TrackedModelSerializer.register_polymorphic_model
class DutyExpressionSerializer(TrackedModelSerializerMixin, ValiditySerializerMixin):
    class Meta:
        model = models.DutyExpression
        fields = [
            "sid",
            "duty_amount_applicability_code",
            "measurement_unit_applicability_code",
            "monetary_unit_applicability_code",
            "description",
            "valid_between",
            "update_type",
            "record_code",
            "subrecord_code",
            "description_record_code",
            "description_subrecord_code",
            "taric_template",
            "start_date",
            "end_date",
        ]


@TrackedModelSerializer.register_polymorphic_model
class MeasureTypeSerializer(TrackedModelSerializerMixin, ValiditySerializerMixin):
    measure_type_series = MeasureTypeSeriesSerializer(read_only=True)

    class Meta:
        model = models.MeasureType
        fields = [
            "sid",
            "trade_movement_code",
            "priority_code",
            "measure_component_applicability_code",
            "order_number_capture_code",
            "measure_explosion_level",
            "description",
            "measure_type_series",
            "additional_code_types",
            "valid_between",
            "update_type",
            "record_code",
            "subrecord_code",
            "description_record_code",
            "description_subrecord_code",
            "taric_template",
            "start_date",
            "end_date",
        ]


@TrackedModelSerializer.register_polymorphic_model
class AdditionalCodeTypeMeasureTypeSerializer(
    TrackedModelSerializerMixin, ValiditySerializerMixin
):
    measure_type = MeasureTypeSerializer(read_only=True)
    additional_code_type = AdditionalCodeTypeSerializer(read_only=True)

    class Meta:
        model = models.AdditionalCodeTypeMeasureType
        fields = [
            "measure_type",
            "additional_code_type",
            "valid_between",
            "update_type",
            "record_code",
            "subrecord_code",
            "taric_template",
            "start_date",
            "end_date",
        ]


@TrackedModelSerializer.register_polymorphic_model
class MeasureConditionCodeSerializer(
    TrackedModelSerializerMixin, ValiditySerializerMixin
):
    class Meta:
        model = models.MeasureConditionCode
        fields = [
            "code",
            "description",
            "valid_between",
            "update_type",
            "record_code",
            "subrecord_code",
            "description_record_code",
            "description_subrecord_code",
            "taric_template",
            "start_date",
            "end_date",
        ]


@TrackedModelSerializer.register_polymorphic_model
class MeasureActionSerializer(TrackedModelSerializerMixin, ValiditySerializerMixin):
    class Meta:
        model = models.MeasureAction
        fields = [
            "code",
            "description",
            "valid_between",
            "update_type",
            "record_code",
            "subrecord_code",
            "description_record_code",
            "description_subrecord_code",
            "taric_template",
            "start_date",
            "end_date",
        ]


@TrackedModelSerializer.register_polymorphic_model
class MeasureSerializer(TrackedModelSerializerMixin, ValiditySerializerMixin):
    sid = serializers.IntegerField(min_value=1, max_value=99999999)
    measure_type = MeasureTypeSerializer(read_only=True)
    geographical_area = GeographicalAreaSerializer(read_only=True)
    goods_nomenclature = GoodsNomenclatureSerializer(read_only=True)
    additional_code = AdditionalCodeSerializer(read_only=True)
    order_number = QuotaOrderNumberSerializer(read_only=True)
    generating_regulation = RegulationSerializer(read_only=True)
    terminating_regulation = RegulationSerializer(read_only=True)
    export_refund_nomenclature_sid = serializers.IntegerField(
        min_value=1, max_value=99999999
    )

    class Meta:
        model = models.Measure
        fields = [
            "sid",
            "measure_type",
            "geographical_area",
            "goods_nomenclature",
            "additional_code",
            "order_number",
            "reduction",
            "generating_regulation",
            "terminating_regulation",
            "stopped",
            "export_refund_nomenclature_sid",
            "valid_between",
            "update_type",
            "record_code",
            "subrecord_code",
            "taric_template",
            "start_date",
            "end_date",
        ]


@TrackedModelSerializer.register_polymorphic_model
class MeasureComponentSerializer(TrackedModelSerializerMixin):
    component_measure = MeasureSerializer(read_only=True)
    duty_expression = DutyExpressionSerializer(read_only=True)
    monetary_unit = MonetaryUnitSerializer(read_only=True)
    component_measurement = MeasurementSerializer(read_only=True)

    class Meta:
        model = models.MeasureComponent
        fields = [
            "component_measure",
            "duty_expression",
            "duty_amount",
            "monetary_unit",
            "component_measurement",
            "update_type",
            "record_code",
            "subrecord_code",
            "taric_template",
        ]


@TrackedModelSerializer.register_polymorphic_model
class MeasureConditionSerializer(TrackedModelSerializerMixin):
    sid = serializers.IntegerField(min_value=1, max_value=99999999)
    dependent_measure = MeasureSerializer(read_only=True)
    condition_code = MeasureConditionCodeSerializer(read_only=True)
    monetary_unit = MonetaryUnitSerializer(read_only=True)
    condition_measurement = MeasurementSerializer(read_only=True)
    action = MeasureActionSerializer(read_only=True)
    required_certificate = CertificateSerializer(read_only=True)

    class Meta:
        model = models.MeasureCondition
        fields = [
            "sid",
            "dependent_measure",
            "condition_code",
            "component_sequence_number",
            "duty_amount",
            "monetary_unit",
            "condition_measurement",
            "action",
            "required_certificate",
            "update_type",
            "record_code",
            "subrecord_code",
            "taric_template",
        ]


@TrackedModelSerializer.register_polymorphic_model
class MeasureConditionComponentSerializer(TrackedModelSerializerMixin):
    condition = MeasureConditionSerializer(read_only=True)
    duty_expression = DutyExpressionSerializer(read_only=True)
    monetary_unit = MonetaryUnitSerializer(read_only=True)
    condition_component_measurement = MeasurementSerializer(read_only=True)

    class Meta:
        model = models.MeasureConditionComponent
        fields = [
            "condition",
            "duty_expression",
            "duty_amount",
            "monetary_unit",
            "condition_component_measurement",
            "update_type",
            "record_code",
            "subrecord_code",
            "taric_template",
        ]


@TrackedModelSerializer.register_polymorphic_model
class MeasureExcludedGeographicalAreaSerializer(TrackedModelSerializerMixin):
    modified_measure = MeasureSerializer(read_only=True)
    excluded_geographical_area = GeographicalAreaSerializer(read_only=True)

    class Meta:
        model = models.MeasureExcludedGeographicalArea
        fields = [
            "modified_measure",
            "excluded_geographical_area",
            "update_type",
            "record_code",
            "subrecord_code",
            "taric_template",
        ]


@TrackedModelSerializer.register_polymorphic_model
class FootnoteAssociationMeasureSerializer(TrackedModelSerializerMixin):
    footnoted_measure = MeasureSerializer(read_only=True)
    associated_footnote = FootnoteSerializer(read_only=True)

    class Meta:
        model = models.FootnoteAssociationMeasure
        fields = [
            "footnoted_measure",
            "associated_footnote",
            "update_type",
            "record_code",
            "subrecord_code",
            "taric_template",
        ]
