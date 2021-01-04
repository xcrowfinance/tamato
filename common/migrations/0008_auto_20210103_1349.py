# Generated by Django 3.1 on 2021-01-03 13:49
import django.utils.timezone
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0007_auto_20201229_1434"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="transaction",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
