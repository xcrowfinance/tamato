# Generated by Django 3.0.10 on 2020-09-23 23:59
import django.contrib.postgres.fields.ranges
import django.core.validators
import django.db.models.deletion
from django.db import migrations
from django.db import models

import common.fields
import common.models
import common.validators
import measures.validators


class Migration(migrations.Migration):

    dependencies = [
        ("certificates", "0002_use_common_fields"),
        ("common", "0004_refactor_update_type"),
        ("additional_codes", "0003_use_common_fields"),
        ("footnotes", "0005_add_measures_data_model"),
        ("geo_areas", "0002_use_common_fields"),
        ("regulations", "0002_use_common_fields"),
        ("commodities", "0003_remove_commodities_and_add_relations"),
        ("quotas", "0001_initial"),
        ("measures", "0002_link_to_goods_nomenclature"),
    ]

    operations = [
        migrations.CreateModel(
            name="AdditionalCodeTypeMeasureType",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.TrackedModel",
                    ),
                ),
                (
                    "valid_between",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(),
                ),
                (
                    "additional_code_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="additional_codes.AdditionalCodeType",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="DutyExpression",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.TrackedModel",
                    ),
                ),
                (
                    "valid_between",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(),
                ),
                (
                    "sid",
                    models.CharField(
                        choices=[
                            ("1", "% or amount"),
                            ("2", "minus\xa0% or amount"),
                            ("3", "The rate is replaced by the levy"),
                            ("4", "+\xa0% or amount"),
                            ("5", "The rate is replaced by the reduced levy"),
                            ("6", "+ Suplementary amount"),
                            ("7", "+ Levy"),
                            ("9", "+ Reduced levy"),
                            ("11", "+ Variable component"),
                            ("12", "+ agricultural component"),
                            ("13", "+ Reduced variable component"),
                            ("14", "+ reduced agricultural component"),
                            ("15", "Minimum"),
                            ("17", "Maximum"),
                            ("19", "+\xa0% or amount"),
                            ("20", "+\xa0% or amount"),
                            ("21", "+ additional duty on sugar"),
                            ("23", "+ 2\xa0% Additional duty on sugar"),
                            ("25", "+ reduced additional duty on sugar"),
                            ("27", "+ additional duty on flour"),
                            ("29", "+ reduced additional duty on flour"),
                            ("31", "Accession compensatory amount"),
                            ("33", "+ Accession compensatory amount"),
                            ("35", "Maximum"),
                            ("36", "minus\xa0% CIF"),
                            ("37", "(nothing)"),
                            ("40", "Export refunds for cereals"),
                            ("41", "Export refunds for rice"),
                            ("42", "Export refunds for eggs"),
                            ("43", "Export refunds for sugar"),
                            ("44", "Export refunds for milk products"),
                            ("99", "Supplementary unit"),
                        ],
                        max_length=2,
                    ),
                ),
                ("duty_amount_applicability_code", common.fields.ApplicabilityCode()),
                (
                    "measurement_unit_applicability_code",
                    common.fields.ApplicabilityCode(),
                ),
                ("monetary_unit_applicability_code", common.fields.ApplicabilityCode()),
                ("description", common.fields.ShortDescription()),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="MeasureAction",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.TrackedModel",
                    ),
                ),
                (
                    "valid_between",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(),
                ),
                (
                    "code",
                    models.CharField(
                        max_length=3,
                        validators=[measures.validators.validate_action_code],
                    ),
                ),
                ("description", common.fields.ShortDescription()),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="MeasureCondition",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.TrackedModel",
                    ),
                ),
                ("sid", common.fields.NumericSID()),
                (
                    "component_sequence_number",
                    models.PositiveSmallIntegerField(
                        validators=[common.validators.NumberRangeValidator(1, 999)]
                    ),
                ),
                (
                    "duty_amount",
                    models.DecimalField(
                        blank=True, decimal_places=3, max_digits=10, null=True
                    ),
                ),
                (
                    "action",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="measures.MeasureAction",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel",),
        ),
        migrations.CreateModel(
            name="MeasureConditionCode",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.TrackedModel",
                    ),
                ),
                (
                    "valid_between",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(),
                ),
                (
                    "code",
                    models.CharField(
                        max_length=2,
                        validators=[
                            django.core.validators.RegexValidator("^[A-Z][A-Z ]?$")
                        ],
                    ),
                ),
                ("description", common.fields.ShortDescription()),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="MeasurementUnit",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.TrackedModel",
                    ),
                ),
                (
                    "valid_between",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(),
                ),
                (
                    "code",
                    models.CharField(
                        max_length=3,
                        validators=[
                            django.core.validators.RegexValidator("^[A-Z]{3}$")
                        ],
                    ),
                ),
                ("description", common.fields.ShortDescription()),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="MeasurementUnitQualifier",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.TrackedModel",
                    ),
                ),
                (
                    "valid_between",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(),
                ),
                (
                    "code",
                    models.CharField(
                        max_length=1,
                        validators=[django.core.validators.RegexValidator("^[A-Z]$")],
                    ),
                ),
                ("description", common.fields.ShortDescription()),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="MeasureTypeSeries",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.TrackedModel",
                    ),
                ),
                (
                    "valid_between",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(),
                ),
                (
                    "sid",
                    models.CharField(
                        max_length=2,
                        validators=[
                            django.core.validators.RegexValidator("^[A-Z][A-Z ]?$")
                        ],
                    ),
                ),
                (
                    "measure_type_combination",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (
                                0,
                                "Only 1 measure at export and 1 at import from the series",
                            ),
                            (1, "All measure types in the series to be considered"),
                        ]
                    ),
                ),
                ("description", common.fields.ShortDescription()),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="MonetaryUnit",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.TrackedModel",
                    ),
                ),
                (
                    "valid_between",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(),
                ),
                (
                    "code",
                    models.CharField(
                        max_length=3,
                        validators=[
                            django.core.validators.RegexValidator("^[A-Z]{3}$")
                        ],
                    ),
                ),
                ("description", common.fields.ShortDescription()),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.RemoveField(
            model_name="measure",
            name="commodity_code",
        ),
        migrations.RemoveField(
            model_name="measure",
            name="duty",
        ),
        migrations.AddField(
            model_name="measure",
            name="additional_code",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="additional_codes.AdditionalCode",
            ),
        ),
        migrations.AddField(
            model_name="measure",
            name="export_refund_nomenclature_sid",
            field=common.fields.NumericSID(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="measure",
            name="generating_regulation",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                to="regulations.Regulation",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="measure",
            name="geographical_area",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                to="geo_areas.GeographicalArea",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="measure",
            name="goods_nomenclature",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="measures",
                to="commodities.GoodsNomenclature",
            ),
        ),
        migrations.AddField(
            model_name="measure",
            name="order_number",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="quotas.QuotaOrderNumber",
            ),
        ),
        migrations.AddField(
            model_name="measure",
            name="reduction",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                validators=[common.validators.NumberRangeValidator(1, 3)],
            ),
        ),
        migrations.AddField(
            model_name="measure",
            name="sid",
            field=common.fields.NumericSID(default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="measure",
            name="stopped",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="measure",
            name="terminating_regulation",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="terminated_measures",
                to="regulations.Regulation",
            ),
        ),
        migrations.CreateModel(
            name="MeasureType",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.TrackedModel",
                    ),
                ),
                (
                    "valid_between",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(),
                ),
                (
                    "sid",
                    models.CharField(
                        max_length=6,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^[0-9]{3}|[0-9]{6}|[A-Z]{3}$"
                            )
                        ],
                    ),
                ),
                (
                    "trade_movement_code",
                    models.PositiveSmallIntegerField(
                        choices=[(0, "Import"), (1, "Export"), (2, "Import/Export")]
                    ),
                ),
                (
                    "priority_code",
                    models.PositiveSmallIntegerField(
                        validators=[common.validators.NumberRangeValidator(1, 9)]
                    ),
                ),
                (
                    "measure_component_applicability_code",
                    common.fields.ApplicabilityCode(),
                ),
                (
                    "order_number_capture_code",
                    models.PositiveSmallIntegerField(
                        choices=[(1, "Mandatory"), (2, "Not permitted")]
                    ),
                ),
                (
                    "measure_explosion_level",
                    models.PositiveSmallIntegerField(
                        validators=[
                            measures.validators.validate_measure_explosion_level
                        ]
                    ),
                ),
                ("description", common.fields.ShortDescription()),
                (
                    "additional_code_types",
                    models.ManyToManyField(
                        through="measures.AdditionalCodeTypeMeasureType",
                        to="additional_codes.AdditionalCodeType",
                    ),
                ),
                (
                    "measure_type_series",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="measures.MeasureTypeSeries",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="Measurement",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.TrackedModel",
                    ),
                ),
                (
                    "valid_between",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(),
                ),
                (
                    "measurement_unit",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="measures.MeasurementUnit",
                    ),
                ),
                (
                    "measurement_unit_qualifier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="measures.MeasurementUnitQualifier",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="MeasureExcludedGeographicalArea",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.TrackedModel",
                    ),
                ),
                (
                    "excluded_geographical_area",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="geo_areas.GeographicalArea",
                    ),
                ),
                (
                    "modified_measure",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="measures.Measure",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel",),
        ),
        migrations.CreateModel(
            name="MeasureConditionComponent",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.TrackedModel",
                    ),
                ),
                (
                    "duty_amount",
                    models.DecimalField(
                        blank=True, decimal_places=3, max_digits=10, null=True
                    ),
                ),
                (
                    "condition",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="components",
                        to="measures.MeasureCondition",
                    ),
                ),
                (
                    "condition_component_measurement",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="measures.Measurement",
                    ),
                ),
                (
                    "duty_expression",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="measures.DutyExpression",
                    ),
                ),
                (
                    "monetary_unit",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="measures.MonetaryUnit",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel",),
        ),
        migrations.AddField(
            model_name="measurecondition",
            name="condition_code",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="measures.MeasureConditionCode",
            ),
        ),
        migrations.AddField(
            model_name="measurecondition",
            name="condition_measurement",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="measures.Measurement",
            ),
        ),
        migrations.AddField(
            model_name="measurecondition",
            name="dependent_measure",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="measures.Measure"
            ),
        ),
        migrations.AddField(
            model_name="measurecondition",
            name="monetary_unit",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="measures.MonetaryUnit",
            ),
        ),
        migrations.AddField(
            model_name="measurecondition",
            name="required_certificate",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="certificates.Certificate",
            ),
        ),
        migrations.CreateModel(
            name="MeasureComponent",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.TrackedModel",
                    ),
                ),
                (
                    "duty_amount",
                    models.DecimalField(
                        blank=True, decimal_places=3, max_digits=10, null=True
                    ),
                ),
                (
                    "component_measure",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="measures.Measure",
                    ),
                ),
                (
                    "component_measurement",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="measures.Measurement",
                    ),
                ),
                (
                    "duty_expression",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="measures.DutyExpression",
                    ),
                ),
                (
                    "monetary_unit",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="measures.MonetaryUnit",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel",),
        ),
        migrations.CreateModel(
            name="FootnoteAssociationMeasure",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.TrackedModel",
                    ),
                ),
                (
                    "associated_footnote",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="footnotes.Footnote",
                    ),
                ),
                (
                    "footnoted_measure",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="measures.Measure",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel",),
        ),
        migrations.AddField(
            model_name="additionalcodetypemeasuretype",
            name="measure_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="measures.MeasureType"
            ),
        ),
        migrations.AddField(
            model_name="measure",
            name="measure_type",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.PROTECT,
                to="measures.MeasureType",
            ),
            preserve_default=False,
        ),
    ]
