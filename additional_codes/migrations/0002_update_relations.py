# Generated by Django 3.0.8 on 2020-07-16 06:08
import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("footnotes", "0002_refactor_footnotes"),
        ("additional_codes", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="additionalcode",
            name="type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="additional_codes.AdditionalCodeType",
            ),
        ),
        migrations.AlterField(
            model_name="additionalcodedescription",
            name="described_additional_code",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="descriptions",
                to="additional_codes.AdditionalCode",
            ),
        ),
        migrations.AlterField(
            model_name="footnoteassociationadditionalcode",
            name="additional_code",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="additional_codes.AdditionalCode",
            ),
        ),
        migrations.AlterField(
            model_name="footnoteassociationadditionalcode",
            name="associated_footnote",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="footnotes.Footnote"
            ),
        ),
    ]
