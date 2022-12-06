# Generated by Django 3.1.14 on 2022-12-06 14:44

import django.db.models.deletion
import django_fsm
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("taric", "0002_auto_20210219_1043"),
        ("workbaskets", "0005_workbasket_rule_check_task_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="LoadingReport",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="PackagedWorkBasket",
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
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "position",
                    models.PositiveSmallIntegerField(db_index=True, editable=False),
                ),
                (
                    "processing_state",
                    django_fsm.FSMField(
                        choices=[
                            ("AWAITING_PROCESSING", "Reviewed and awaiting processing"),
                            ("CURRENTLY_PROCESSING", "Currently processing"),
                            ("SUCCESSFULLY_PROCESSED", "Successfully processed"),
                            ("FAILED_PROCESSING", "Failed processing"),
                        ],
                        db_index=True,
                        default="AWAITING_PROCESSING",
                        editable=False,
                        max_length=50,
                        protected=True,
                    ),
                ),
                ("theme", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("eif", models.DateField(blank=True, null=True)),
                ("embargo", models.DateField(blank=True, null=True)),
                ("jira_url", models.URLField()),
                (
                    "envelope",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="taric.envelope",
                    ),
                ),
                (
                    "loading_report",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="publishing.loadingreport",
                    ),
                ),
                (
                    "workbasket",
                    models.ForeignKey(
                        editable=False,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="workbaskets.workbasket",
                    ),
                ),
            ],
            options={
                "ordering": ["position"],
            },
        ),
    ]
