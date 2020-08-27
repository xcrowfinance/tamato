# Generated by Django 3.0.4 on 2020-07-10 14:11

import common.validators
import django.contrib.postgres.constraints
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0003_trackedmodel_update_type"),
        ("footnotes", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="footnotetypedescription",
            name="footnote_type",
        ),
        migrations.RemoveField(
            model_name="footnotetypedescription",
            name="trackedmodel_ptr",
        ),
        migrations.AlterModelOptions(
            name="footnotetype",
            options={},
        ),
        migrations.RemoveConstraint(
            model_name="footnote",
            name="FO2",
        ),
        migrations.RemoveConstraint(
            model_name="footnotedescription",
            name="FO4",
        ),
        migrations.AddField(
            model_name="footnotedescription",
            name="description_period_sid",
            field=models.PositiveIntegerField(
                default=1, validators=[common.validators.NumericSIDValidator()]
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="footnotetype",
            name="description",
            field=models.CharField(default="", max_length=500),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="footnote",
            name="footnote_id",
            field=models.CharField(
                max_length=5,
                validators=[
                    django.core.validators.RegexValidator("^([0-9]{3}|[0-9]{5})$")
                ],
            ),
        ),
        migrations.AlterField(
            model_name="footnotedescription",
            name="described_footnote",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="descriptions",
                to="footnotes.Footnote",
            ),
        ),
        migrations.AlterField(
            model_name="footnotetype",
            name="footnote_type_id",
            field=models.CharField(
                max_length=3,
                validators=[django.core.validators.RegexValidator("^[A-Z]{2}[A-Z ]?$")],
            ),
        ),
        migrations.AddConstraint(
            model_name="footnote",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                expressions=[
                    ("valid_between", "&&"),
                    ("footnote_id", "="),
                    ("footnote_type", "="),
                ],
                name="exclude_overlapping_footnotes_FO2",
            ),
        ),
        migrations.AddConstraint(
            model_name="footnotedescription",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                expressions=[("valid_between", "&&"), ("described_footnote", "=")],
                name="exclude_overlapping_footnote_descriptions",
            ),
        ),
        migrations.AddConstraint(
            model_name="footnotetype",
            constraint=django.contrib.postgres.constraints.ExclusionConstraint(
                expressions=[("valid_between", "&&"), ("footnote_type_id", "=")],
                name="exclude_overlapping_footnote_types",
            ),
        ),
        migrations.DeleteModel(
            name="FootnoteTypeDescription",
        ),
    ]
