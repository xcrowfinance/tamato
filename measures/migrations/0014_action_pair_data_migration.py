# Generated by Django 3.2.18 on 2023-03-28 15:39

from django.conf import settings
from django.db import migrations
from django.db.transaction import atomic

action_code_mappings = [
    ("24", "04"),
    ("25", "05"),
    ("26", "06"),
    ("27", "07"),
    ("28", "08"),
    ("29", "09"),
    ("34", "14"),
    ("36", "16"),
]
"""positive, negative action code tuples."""


@atomic
def generate_action_pairs(apps, schema_editor):
    # Generate MeasureActionPairs

    if settings.ENV == "test":
        return

    MeasureAction = apps.get_model("measures", "MeasureAction")
    MeasureActionPair = apps.get_model("measures", "MeasureActionPair")
    for positive, negative in action_code_mappings:
        positive_action = MeasureAction.objects.get(code=positive)
        negative_action = MeasureAction.objects.get(code=negative)
        MeasureActionPair.objects.create(
            positive_action=positive_action,
            negative_action=negative_action,
        )


def reverse_action_pairs(apps, schema_editor):
    # generate_action_pairs() creates MeasureActionPairs,
    # so reverse_action_pairs() should delete them.
    # if they are present
    if settings.ENV == "test":
        return

    MeasureActionPair = apps.get_model("measures", "MeasureActionPair")
    for positive, negative in action_code_mappings:
        measure_action_pair = MeasureActionPair.objects.filter(
            positive_action__code=positive,
            negative_action__code=negative,
        )
        if measure_action_pair:
            measure_action_pair.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("measures", "0013_measureactionpair"),
    ]

    operations = [
        migrations.RunPython(generate_action_pairs, reverse_action_pairs),
    ]
