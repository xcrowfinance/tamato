# Generated by Django 3.1 on 2021-02-01 16:39

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("importer", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="importerxmlchunk",
            name="status",
            field=models.PositiveSmallIntegerField(
                choices=[(1, "Waiting"), (2, "Running"), (3, "Done"), (4, "Errored")],
                default=1,
            ),
        ),
    ]
