# Generated by Django 3.1 on 2021-01-06 15:33
import django.core.validators
import django.db.models.deletion
from django.db import migrations
from django.db import models

import common.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("common", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Certificate",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.trackedmodel",
                    ),
                ),
                ("valid_between", common.fields.TaricDateTimeRangeField(db_index=True)),
                (
                    "sid",
                    models.CharField(
                        db_index=True,
                        max_length=3,
                        validators=[
                            django.core.validators.RegexValidator("^[A-Z0-9]{3}$"),
                        ],
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="CertificateType",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.trackedmodel",
                    ),
                ),
                ("valid_between", common.fields.TaricDateTimeRangeField(db_index=True)),
                (
                    "sid",
                    models.CharField(
                        db_index=True,
                        max_length=1,
                        validators=[
                            django.core.validators.RegexValidator("^[A-Z0-9]{1}$"),
                        ],
                    ),
                ),
                ("description", common.fields.ShortDescription()),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.CreateModel(
            name="CertificateDescription",
            fields=[
                (
                    "trackedmodel_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="common.trackedmodel",
                    ),
                ),
                ("valid_between", common.fields.TaricDateTimeRangeField(db_index=True)),
                ("sid", common.fields.SignedIntSID()),
                ("description", common.fields.ShortDescription()),
                (
                    "described_certificate",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="descriptions",
                        to="certificates.certificate",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
            bases=("common.trackedmodel", models.Model),
        ),
        migrations.AddField(
            model_name="certificate",
            name="certificate_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="certificates",
                to="certificates.certificatetype",
            ),
        ),
    ]
