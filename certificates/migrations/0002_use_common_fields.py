# Generated by Django 3.0.9 on 2020-08-13 11:13
from django.db import migrations

import common.models


class Migration(migrations.Migration):

    dependencies = [
        ("certificates", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="certificatedescription",
            name="description",
            field=common.models.ShortDescription(blank=True, max_length=500, null=True),
        ),
        migrations.AlterField(
            model_name="certificatedescription",
            name="sid",
            field=common.models.NumericSID(),
        ),
        migrations.AlterField(
            model_name="certificatetype",
            name="description",
            field=common.models.ShortDescription(blank=True, max_length=500, null=True),
        ),
    ]
