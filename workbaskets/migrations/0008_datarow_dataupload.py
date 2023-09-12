# Generated by Django 3.2.20 on 2023-09-12 15:37

import django.db.models.deletion
from django.db import migrations
from django.db import models

import common.fields


class Migration(migrations.Migration):
    dependencies = [
        ("workbaskets", "0007_alter_workbasket_options"),
    ]

    operations = [
        migrations.CreateModel(
            name="DataUpload",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("raw_data", models.TextField()),
                (
                    "workbasket",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="workbaskets.workbasket",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="DataRow",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("valid_between", common.fields.TaricDateRangeField(db_index=True)),
                ("commodity", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "duty_sentence",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "data_upload",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rows",
                        to="workbaskets.dataupload",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
