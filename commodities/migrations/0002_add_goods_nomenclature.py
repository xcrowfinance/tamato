# Generated by Django 3.0.8 on 2020-07-17 14:39

import django.contrib.postgres.fields.ranges
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0003_trackedmodel_update_type"),
        ("commodities", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FootnoteAssociationGoodsNomenclature",
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
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="GoodsNomenclature",
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
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(99999999),
                        ]
                    ),
                ),
                (
                    "item_id",
                    models.CharField(
                        max_length=10,
                        validators=[django.core.validators.RegexValidator("\\d{10}")],
                    ),
                ),
                (
                    "suffix",
                    models.CharField(
                        max_length=2,
                        validators=[django.core.validators.RegexValidator("\\d{2}")],
                    ),
                ),
                ("statistical", models.BooleanField()),
            ],
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="GoodsNomenclatureDescription",
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
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(99999999),
                        ]
                    ),
                ),
                ("description", models.TextField()),
            ],
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="GoodsNomenclatureIndent",
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
                ("path", models.CharField(max_length=255, unique=True)),
                ("depth", models.PositiveIntegerField()),
                ("numchild", models.PositiveIntegerField(default=0)),
                (
                    "valid_between",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(),
                ),
                (
                    "sid",
                    models.PositiveIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(99999999),
                        ]
                    ),
                ),
            ],
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.RemoveField(
            model_name="commodity",
            name="trackedmodel_ptr",
        ),
    ]
