# Generated by Django 3.0.7 on 2020-06-11 10:16
import django.contrib.postgres.constraints
import django.contrib.postgres.fields.ranges
import django.core.validators
import django.db.models.deletion
import django.db.models.expressions
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("common", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="GeographicalArea",
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
                    models.PositiveIntegerField(
                        validators=[django.core.validators.MaxValueValidator(99999999)]
                    ),
                ),
                (
                    "area_id",
                    models.CharField(
                        max_length=4,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^[A-Z0-9]{2}$|^[A-Z0-9]{4}$"
                            )
                        ],
                    ),
                ),
                (
                    "area_code",
                    models.PositiveSmallIntegerField(
                        choices=[
                            (0, "Country"),
                            (1, "Geographical Area Group"),
                            (2, "Region"),
                        ]
                    ),
                ),
            ],
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="GeographicalMembership",
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
                    "geo_group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="members",
                        to="geo_areas.GeographicalArea",
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="groups",
                        to="geo_areas.GeographicalArea",
                    ),
                ),
            ],
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="GeographicalAreaDescription",
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
                ("description", models.CharField(max_length=500)),
                (
                    "area",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="geo_areas.GeographicalArea",
                    ),
                ),
            ],
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.AddField(
            model_name="geographicalarea",
            name="memberships",
            field=models.ManyToManyField(
                related_name="_geographicalarea_memberships_+",
                through="geo_areas.GeographicalMembership",
                to="geo_areas.GeographicalArea",
            ),
        ),
        migrations.AddField(
            model_name="geographicalarea",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="geo_areas.GeographicalArea",
            ),
        ),
        migrations.AddConstraint(
            model_name="geographicalmembership",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                expressions=[
                    ("valid_between", "&&"),
                    (django.db.models.expressions.F("geo_group"), "="),
                    (django.db.models.expressions.F("member"), "="),
                ],
                name="exclude_overlapping_memberships",
            ),
        ),
        migrations.AddConstraint(
            model_name="geographicalareadescription",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                expressions=[("valid_between", "&&"), ("area", "=")],
                name="exclude_overlapping_area_descriptions",
            ),
        ),
        migrations.AddConstraint(
            model_name="geographicalarea",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                expressions=[("valid_between", "&&"), ("area_id", "=")],
                name="exclude_overlapping_areas",
            ),
        ),
        migrations.AddConstraint(
            model_name="geographicalarea",
            constraint=models.CheckConstraint(
                check=models.Q(
                    ("area_code", 1), ("parent__isnull", True), _connector="OR"
                ),
                name="only_groups_have_parents",
            ),
        ),
    ]
