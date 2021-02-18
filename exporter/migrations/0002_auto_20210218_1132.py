# Generated by Django 3.1.6 on 2021-02-18 11:32

import storages.backends.s3boto3
from django.db import migrations
from django.db import models

import exporter.models


class Migration(migrations.Migration):

    dependencies = [
        ("exporter", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="upload",
            name="file",
            field=models.FileField(
                storage=storages.backends.s3boto3.S3Boto3Storage,
                upload_to=exporter.models.to_hmrc,
            ),
        ),
    ]
