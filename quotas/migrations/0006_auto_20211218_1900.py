# Generated by Django 3.1.13 on 2021-12-18 19:00

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("quotas", "0005_quotaordernumber_required_certificates"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="quotadefinition",
            options={},
        ),
        migrations.AddConstraint(
            model_name="quotadefinition",
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(
                        ("measurement_unit__isnull", True),
                        ("monetary_unit__isnull", False),
                    ),
                    models.Q(
                        ("measurement_unit__isnull", False),
                        ("monetary_unit__isnull", True),
                    ),
                    _connector="OR",
                ),
                name="quota_definition_must_have_one_unit",
            ),
        ),
    ]
