# Generated by Django 3.0.7 on 2020-06-11 10:03
import django.db.models.deletion
from django.contrib.postgres.operations import BtreeGistExtension
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("workbaskets", "0001_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        BtreeGistExtension(),
        migrations.CreateModel(
            name="TrackedModel",
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
                    "polymorphic_ctype",
                    models.ForeignKey(
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="polymorphic_common.trackedmodel_set+",
                        to="contenttypes.ContentType",
                    ),
                ),
                (
                    "predecessor",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="successor",
                        related_query_name="successor",
                        to="common.TrackedModel",
                    ),
                ),
                (
                    "workbasket",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="workbaskets.WorkBasket",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "base_manager_name": "objects",
            },
        ),
    ]
