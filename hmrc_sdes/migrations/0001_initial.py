# Generated by Django 3.0.10 on 2020-11-10 11:10
import uuid

import django.db.models.deletion
import storages.backends.s3boto3
from django.db import migrations
from django.db import models

import hmrc_sdes.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("taric", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Upload",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "file",
                    models.FileField(
                        storage=storages.backends.s3boto3.S3Boto3Storage,
                        upload_to=hmrc_sdes.models.to_hmrc,
                    ),
                ),
                (
                    "correlation_id",
                    models.UUIDField(default=uuid.uuid4, editable=False),
                ),
                ("checksum", models.CharField(editable=False, max_length=32)),
                ("notification_sent", models.DateTimeField(editable=False, null=True)),
                (
                    "envelope",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="taric.Envelope"
                    ),
                ),
            ],
        ),
    ]
