# Generated by Django 3.1.14 on 2022-05-10 14:08

import django_fsm
from django.db import migrations


class Migration(migrations.Migration):
    """Schema migration to add ARCHIVED as a valid TransactionPartition
    partition."""

    dependencies = [
        ("common", "0005_transaction_index"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="partition",
            field=django_fsm.FSMIntegerField(
                choices=[(1, "Seed"), (2, "Revision"), (3, "Draft"), (4, "Archived")],
                db_index=True,
                default=3,
            ),
        ),
    ]
