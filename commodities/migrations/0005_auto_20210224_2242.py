# Generated by Django 3.1 on 2021-02-24 22:42

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("commodities", "0004_auto_20210219_0955"),
    ]

    operations = [
        migrations.AlterField(
            model_name="goodsnomenclatureindentnode",
            name="depth",
            field=models.PositiveIntegerField(),
        ),
    ]
