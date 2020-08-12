# Generated by Django 3.0.9 on 2020-08-13 11:13
from django.db import migrations

import common.models


class Migration(migrations.Migration):

    dependencies = [
        ("footnotes", "0003_remove_exclusion_constraints"),
    ]

    operations = [
        migrations.AlterField(
            model_name="footnotedescription",
            name="description_period_sid",
            field=common.models.NumericSID(),
        ),
        migrations.AlterField(
            model_name="footnotetype",
            name="description",
            field=common.models.ShortDescription(blank=True, max_length=500, null=True),
        ),
    ]
