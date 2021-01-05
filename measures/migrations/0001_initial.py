# Generated by Django 3.0.7 on 2020-06-11 10:03
import django.contrib.postgres.fields.ranges
import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("commodities", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Measure",
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
                ("duty", models.CharField(max_length=512)),
                (
                    "commodity_code",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="measures",
                        to="commodities.Commodity",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel", models.Model),
        ),
    ]
