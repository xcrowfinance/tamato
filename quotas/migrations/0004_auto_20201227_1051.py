# Generated by Django 3.1 on 2020-12-27 10:51
from django.db import migrations

import common.models.fields


class Migration(migrations.Migration):

    dependencies = [
        ("quotas", "0003_auto_20201027_1022"),
    ]

    operations = [
        migrations.AlterField(
            model_name="quotablocking",
            name="valid_between",
            field=common.models.fields.TaricDateTimeRangeField(),
        ),
        migrations.AlterField(
            model_name="quotadefinition",
            name="valid_between",
            field=common.models.fields.TaricDateTimeRangeField(),
        ),
        migrations.AlterField(
            model_name="quotaordernumber",
            name="valid_between",
            field=common.models.fields.TaricDateTimeRangeField(),
        ),
        migrations.AlterField(
            model_name="quotaordernumberorigin",
            name="valid_between",
            field=common.models.fields.TaricDateTimeRangeField(),
        ),
        migrations.AlterField(
            model_name="quotasuspension",
            name="valid_between",
            field=common.models.fields.TaricDateTimeRangeField(),
        ),
    ]
