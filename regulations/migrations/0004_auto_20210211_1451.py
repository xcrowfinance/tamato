# Generated by Django 3.1 on 2021-02-11 14:51

from django.db import migrations

import common.fields


class Migration(migrations.Migration):

    dependencies = [
        ("regulations", "0003_auto_20210210_1516"),
    ]

    operations = [
        migrations.AlterField(
            model_name="regulation",
            name="valid_between",
            field=common.fields.TaricDateRangeField(blank=True, null=True),
        ),
    ]
