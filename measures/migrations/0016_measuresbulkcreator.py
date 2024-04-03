# Generated by Django 4.2.11 on 2024-04-03 11:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_fsm
import measures.models.bulk_processing


class Migration(migrations.Migration):

    dependencies = [
        ("workbaskets", "0008_datarow_dataupload"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("measures", "0015_alter_measure_dead_order_number"),
    ]

    operations = [
        migrations.CreateModel(
            name="MeasuresBulkCreator",
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
                    "task_id",
                    models.CharField(blank=True, max_length=50, null=True, unique=True),
                ),
                (
                    "processing_state",
                    django_fsm.FSMField(
                        choices=[
                            ("AWAITING_PROCESSING", "Awaiting processing"),
                            ("CURRENTLY_PROCESSING", "Currently processing"),
                            ("SUCCESSFULLY_PROCESSED", "Successfully processed"),
                            ("FAILED_PROCESSING", "Failed processing"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        db_index=True,
                        default="AWAITING_PROCESSING",
                        editable=False,
                        max_length=50,
                        protected=True,
                    ),
                ),
                (
                    "successfully_processed_count",
                    models.PositiveIntegerField(default=0),
                ),
                ("form_data", models.JSONField()),
                ("form_kwargs", models.JSONField()),
                (
                    "user",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "workbasket",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=measures.models.bulk_processing.REVOKE_TASKS_AND_SET_NULL,
                        to="workbaskets.workbasket",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
