# Generated by Django 3.2.24 on 2024-02-22 14:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0004_auto_20240125_1134'),
    ]

    operations = [
        migrations.RenameField(
            model_name='eudatamodel',
            old_name='origin',
            new_name='geographical_area_origin',
        ),
        migrations.RenameField(
            model_name='eudatamodel',
            old_name='goods_code',
            new_name='goods_nomenclature_code',
        ),
    ]
