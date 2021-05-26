from django.db import models
from django.db.models import Max

from certificates import business_rules
from certificates import validators
from common.business_rules import UpdateValidity
from common.fields import ShortDescription
from common.fields import SignedIntSID
from common.models import TrackedModel
from common.models.mixins.description import DescriptionMixin
from common.models.mixins.validity import ValidityMixin
from measures import business_rules as measures_business_rules


class CertificateType(TrackedModel, ValidityMixin):
    sid = models.CharField(
        max_length=1,
        validators=[validators.certificate_type_sid_validator],
        db_index=True,
    )
    description = ShortDescription()

    indirect_business_rules = (business_rules.CE7,)
    business_rules = (
        business_rules.CET1,
        business_rules.CET2,
        UpdateValidity,
    )

    def in_use(self):
        return (
            Certificate.objects.filter(certificate_type__sid=self.sid)
            .approved_up_to_transaction(self.transaction)
            .exists()
        )

    def __str__(self):
        return self.sid


class Certificate(TrackedModel, ValidityMixin):
    sid = models.CharField(
        max_length=3,
        validators=[validators.certificate_sid_validator],
        db_index=True,
    )

    certificate_type = models.ForeignKey(
        CertificateType,
        related_name="certificates",
        on_delete=models.PROTECT,
    )

    identifying_fields = (
        "certificate_type__sid",
        "sid",
    )

    indirect_business_rules = (
        measures_business_rules.ME56,
        measures_business_rules.ME57,
    )
    business_rules = (
        business_rules.CE2,
        business_rules.CE4,
        business_rules.CE5,
        business_rules.CE6,
        business_rules.CE7,
        UpdateValidity,
    )

    @property
    def code(self):
        return self.certificate_type.sid + self.sid

    def __str__(self):
        return self.code

    @property
    def autocomplete_label(self):
        return f"{self} - {self.get_description().description}"

    def in_use(self):
        return (
            self.measurecondition_set.model.objects.filter(
                required_certificate__sid=self.sid,
                required_certificate__certificate_type=self.certificate_type,
            )
            .approved_up_to_transaction(self.transaction)
            .exists()
        )


class CertificateDescription(DescriptionMixin, TrackedModel):

    sid = SignedIntSID(db_index=True)

    description = ShortDescription()
    described_certificate = models.ForeignKey(
        Certificate,
        related_name="descriptions",
        on_delete=models.PROTECT,
    )

    indirect_business_rules = (business_rules.CE6,)

    def save(self, *args, **kwargs):
        if getattr(self, "sid") is None:
            highest_sid = CertificateDescription.objects.aggregate(Max("sid"))[
                "sid__max"
            ]
            self.sid = highest_sid + 1

        return super().save(*args, **kwargs)

    class Meta:
        ordering = ("validity_start",)
