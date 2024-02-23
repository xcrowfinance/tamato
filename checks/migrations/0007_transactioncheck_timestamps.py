# Generated by Django 3.2.18 on 2023-03-28 15:39

from django.db import migrations
from django.db.models import Max
from django.db.models import Min
from django.db.transaction import atomic

from workbaskets.validators import WorkflowStatus


@atomic
def generate_timestamps(apps, schema_editor):
    TransactionCheck = apps.get_model("checks", "transactioncheck")

    transaction_checks_to_update = TransactionCheck.objects.filter(
        transaction__workbasket__status=WorkflowStatus.EDITING,
        completed=True,
    )

    for check in transaction_checks_to_update:
        if not check.model_checks.all():
            continue
        aggregated_checks = check.model_checks.aggregate(
            first_created_at=Min("created_at"),
            last_updated_at=Max("updated_at"),
        )
        check.completed = True
        check.successful = False
        check.created_at = aggregated_checks["first_created_at"]
        check.updated_at = aggregated_checks["last_updated_at"]
        check.save()


class Migration(migrations.Migration):
    dependencies = [
        ("checks", "0006_auto_20231211_1642"),
    ]

    operations = [
        migrations.RunPython(
            generate_timestamps,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
