# Generated by Django 3.1.6 on 2021-03-17 11:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("commodities", "0005_auto_20210224_2242"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="goodsnomenclature",
            options={"verbose_name": "commodity code"},
        ),
    ]
