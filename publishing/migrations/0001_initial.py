# Generated by Django 3.1.14 on 2023-01-06 12:04

import django.db.models.deletion
import django_fsm
from django.conf import settings
from django.db import migrations
from django.db import models

import publishing.models
import publishing.storages


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("taric", "0002_auto_20210219_1043"),
        ("workbaskets", "0006_auto_20221220_1532"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
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
                (
                    "file",
                    models.FileField(
                        blank=True,
                        null=True,
                        storage=publishing.storages.LoadingReportStorage,
                        upload_to=publishing.models.report_bucket,
                    ),
                ),
                ("comments", models.TextField(blank=True, max_length=200)),
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
                            ("ABANDONED", "Abandoned"),
                        ],
                        db_index=True,
                        default="AWAITING_PROCESSING",
                        editable=False,
                        max_length=50,
                        protected=True,
                    ),
                ),
                (
                    "processing_started_at",
                    models.DateTimeField(blank=True, default=None, null=True),
                ),
                ("theme", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                (
                    "eif",
                    models.DateField(
                        blank=True,
                        help_text="For Example, 27 3 2008",
                        null=True,
                    ),
                ),
                ("embargo", models.CharField(blank=True, max_length=255, null=True)),
                ("jira_url", models.URLField(help_text="Insert Tops Jira ticket link")),
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
        migrations.CreateModel(
            name="OperationalStatus",
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
                (
                    "queue_state",
                    models.CharField(
                        choices=[
                            ("PAUSED", "Envelope processing is paused"),
                            (
                                "UNPAUSED",
                                "Envelope processing is unpaused and may proceed",
                            ),
                        ],
                        default="PAUSED",
                        editable=False,
                        max_length=8,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name_plural": "operational statuses",
                "ordering": ["pk"],
            },
        ),
    ]
