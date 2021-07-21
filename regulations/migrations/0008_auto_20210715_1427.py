# Generated by Django 3.1.12 on 2021-07-15 14:27

import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("regulations", "0007_auto_20210715_1326"),
    ]

    operations = [
        migrations.AlterField(
            model_name="regulation",
            name="published_at",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="regulation",
            name="regulation_group",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="regulations.group",
            ),
        ),
    ]
