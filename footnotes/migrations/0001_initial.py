# Generated by Django 3.0.7 on 2020-06-11 10:05

import django.contrib.postgres.constraints
import django.contrib.postgres.fields.ranges
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.functions.text
import footnotes.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("common", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Footnote",
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
                    "footnote_id",
                    models.CharField(
                        max_length=5,
                        validators=[footnotes.validators.FootnoteIDValidator],
                    ),
                ),
            ],
            options={
                "ordering": ["footnote_type__footnote_type_id", "footnote_id"],
            },
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="FootnoteType",
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
                    "footnote_type_id",
                    models.CharField(
                        max_length=3,
                        validators=[footnotes.validators.FootnoteTypeIDValidator],
                    ),
                ),
                (
                    "application_code",
                    models.PositiveIntegerField(
                        choices=[
                            (1, "Cn Nomenclature"),
                            (2, "Taric Nomenclature"),
                            (3, "Export Refund Nomenclature"),
                            (4, "Wine Reference Nomenclature"),
                            (5, "Additional Codes"),
                            (6, "Cn Measures"),
                            (7, "Other Measures"),
                            (8, "Meursing Heading"),
                            (9, "Dynamic Footnote"),
                        ]
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
            name="FootnoteTypeDescription",
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
                ("description", models.CharField(max_length=500)),
                (
                    "footnote_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="footnotes.FootnoteType",
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
            name="FootnoteDescription",
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
                ("description", models.TextField()),
                (
                    "described_footnote",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="footnotes.Footnote",
                    ),
                ),
            ],
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.AddField(
            model_name="footnote",
            name="footnote_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="footnotes.FootnoteType"
            ),
        ),
        migrations.AddConstraint(
            model_name="footnotedescription",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                expressions=[
                    (django.db.models.functions.text.Lower("valid_between"), "="),
                    ("described_footnote", "="),
                ],
                name="FO4",
            ),
        ),
        migrations.AddConstraint(
            model_name="footnote",
            constraint=models.UniqueConstraint(
                fields=("footnote_id", "footnote_type"), name="FO2"
            ),
        ),
    ]
