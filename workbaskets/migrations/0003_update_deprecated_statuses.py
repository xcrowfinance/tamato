# Generated by Django 3.1.12 on 2021-09-21 14:24

from django.db import migrations


def translate_status(apps, schema_editor):
    WorkBasket = apps.get_model("workbaskets", "WorkBasket")
    for workbasket in WorkBasket.objects.exclude(
        status__in=["EDITING", "PROPOSED", "APPROVED", "SENT", "PUBLISHED", "ERRORED"],
    ):
        if workbasket.status in ["NEW_IN_PROGRESS", "APPROVAL_REJECTED"]:
            workbasket.status = "EDITING"
        if workbasket.status == "AWAITING_APPROVAL":
            workbasket.status = "PROPOSED"
        if workbasket.status == "READY_FOR_EXPORT":
            workbasket.status = "APPROVED"
        if workbasket.status in [
            "AWAITING_CDS_UPLOAD_CREATE_NEW",
            "AWAITING_CDS_UPLOAD_EDIT",
            "AWAITING_CDS_UPLOAD_OVERWRITE",
            "AWAITING_CDS_UPLOAD_DELETE",
        ]:
            workbasket.status = "APPROVED"
        if workbasket.status in ["SENT_TO_CDS", "SENT_TO_CDS_DELETE"]:
            workbasket.status = "SENT"
        if workbasket.status == "CDS_ERROR":
            workbasket.status = "ERRORED"
        workbasket.save()


class Migration(migrations.Migration):

    dependencies = [
        ("workbaskets", "0002_change_status_per_ADR008"),
    ]

    operations = [
        migrations.RunPython(translate_status),
    ]
