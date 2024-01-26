# Generated by Django 3.2.23 on 2024-01-22 17:46

import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0007_auto_20221114_1040_fix_missing_current_versions"),
        ("measures", "0017_rename_createmeasures_measuresbulkcreator"),
    ]

    operations = [
        migrations.RenameField(
            model_name="measuresbulkcreator",
            old_name="cleaned_data",
            new_name="form_data",
        ),
        migrations.AddField(
            model_name="measuresbulkcreator",
            name="current_transaction",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="measures_bulk_creators",
                to="common.transaction",
            ),
        ),
    ]
