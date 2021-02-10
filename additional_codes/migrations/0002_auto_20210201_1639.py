# Generated by Django 3.1 on 2021-02-01 16:39
from django.db import migrations

from common.migration_operations import ConvertTaricDateRange


class Migration(migrations.Migration):

    dependencies = [
        ("additional_codes", "0001_initial"),
    ]

    operations = [
        ConvertTaricDateRange("additionalcode", "valid_between"),
        ConvertTaricDateRange("additionalcodedescription", "valid_between"),
        ConvertTaricDateRange("additionalcodetype", "valid_between"),
        ConvertTaricDateRange("footnoteassociationadditionalcode", "valid_between"),
    ]
