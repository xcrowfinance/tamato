# Generated by Django 3.0.10 on 2020-09-24 13:58
from django.db import migrations

import common.models


class Migration(migrations.Migration):

    dependencies = [
        ("geo_areas", "0003_geographicalareadescription_sid"),
    ]

    operations = [
        migrations.AlterField(
            model_name="geographicalareadescription",
            name="sid",
            field=common.models.NumericSID(),
        ),
    ]
