# Generated by Django 3.1.12 on 2021-09-02 10:02

import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("commodities", "0008_allow_blank_descriptions"),
    ]

    operations = [
        migrations.AlterField(
            model_name="footnoteassociationgoodsnomenclature",
            name="goods_nomenclature",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="footnote_associations",
                to="commodities.goodsnomenclature",
            ),
        ),
    ]
