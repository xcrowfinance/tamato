# Generated by Django 3.0.9 on 2020-08-07 13:20

import common.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("geo_areas", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="geographicalarea", name="sid", field=common.models.NumericSID(),
        ),
        migrations.AlterField(
            model_name="geographicalareadescription",
            name="description",
            field=common.models.ShortDescription(blank=True, max_length=500, null=True),
        ),
    ]
