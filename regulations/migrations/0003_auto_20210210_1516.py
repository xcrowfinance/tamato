# Generated by Django 3.1 on 2021-02-10 15:16
from django.db import migrations

from common.migration_operations import ConvertTaricDateRange


class Migration(migrations.Migration):
    dependencies = [
        ("regulations", "0002_auto_20210201_1639"),
    ]

    operations = [
        ConvertTaricDateRange("group", "valid_between"),
        ConvertTaricDateRange("regulation", "valid_between", blank=True, null=True),
    ]
