# Generated by Django 3.1 on 2021-02-13 13:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("measures", "0003_auto_20210201_1639"),
    ]

    operations = [
        migrations.RenameField(
            model_name="measureconditioncomponent",
            old_name="condition_component_measurement",
            new_name="component_measurement",
        ),
    ]
