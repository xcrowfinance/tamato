# Generated by Django 3.1.6 on 2021-03-02 13:49

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("importer", "0002_auto_20210201_1639"),
    ]

    operations = [
        migrations.AlterField(
            model_name="importbatch",
            name="dependencies",
            field=models.ManyToManyField(
                blank=True,
                through="importer.BatchDependencies",
                to="importer.ImportBatch",
            ),
        ),
    ]
