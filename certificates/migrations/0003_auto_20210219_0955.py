# Generated by Django 3.1.6 on 2021-02-19 09:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("certificates", "0002_auto_20210201_1639"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="certificatedescription",
            options={"ordering": ("valid_between",)},
        ),
    ]
