# Generated by Django 3.0.10 on 2020-09-24 13:58
from django.db import migrations

import common.fields
import common.models


class Migration(migrations.Migration):

    dependencies = [
        ("geo_areas", "0002_use_common_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="geographicalareadescription",
            name="sid",
            field=common.fields.NumericSID(null=True),
        ),
    ]
