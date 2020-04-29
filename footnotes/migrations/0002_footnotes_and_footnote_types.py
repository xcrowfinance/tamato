# Generated by Django 3.0.4 on 2020-04-27 15:31
import django.contrib.postgres.fields.ranges
import django.db.models.deletion
from django.db import migrations
from django.db import models
from psycopg2.extras import DateTimeTZRange

from common.util import BREXIT_DATE


class Migration(migrations.Migration):

    dependencies = [
        ("footnotes", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FootnoteType",
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
                    "valid_between",
                    django.contrib.postgres.fields.ranges.DateTimeRangeField(),
                ),
                ("live", models.BooleanField(default=False)),
                ("footnote_type_id", models.CharField(max_length=3, unique=True)),
                ("description", models.CharField(max_length=500)),
            ],
            options={"abstract": False,},
        ),
        migrations.AddField(
            model_name="footnote",
            name="footnote_id",
            field=models.CharField(default="000", max_length=5, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="footnote",
            name="live",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="footnote",
            name="valid_between",
            field=django.contrib.postgres.fields.ranges.DateTimeRangeField(
                default=DateTimeTZRange(BREXIT_DATE, None)
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="footnote",
            name="description",
            field=models.CharField(max_length=500),
        ),
        migrations.AddField(
            model_name="footnote",
            name="footnote_type",
            field=models.ForeignKey(
                default=0,
                on_delete=django.db.models.deletion.PROTECT,
                to="footnotes.FootnoteType",
            ),
            preserve_default=False,
        ),
    ]
