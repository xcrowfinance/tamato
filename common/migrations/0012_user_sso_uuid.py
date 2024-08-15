# Generated by Django 4.2.11 on 2024-08-15 10:39

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0011_alter_trackedmodel_polymorphic_ctype"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="sso_uuid",
            field=models.UUIDField(
                blank=True,
                help_text="This field is populated by the Staff SSO authentication backend override.",
                null=True,
                unique=True,
            ),
        ),
    ]
