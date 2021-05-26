"""Transaction model and manager."""
from __future__ import annotations

import json
from typing import Iterator

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.aggregates import Count
from django_cte import CTEManager
from django_cte import With
from django_cte.cte import CTEQuerySet

from common import xml
from common.business_rules import BusinessRuleChecker
from common.business_rules import BusinessRuleViolation
from common.models.mixins import TimestampedMixin
from common.models.records import TrackedModel


class TransactionManager(CTEManager):
    """Sorts TrackedModels by record_number and subrecord_number."""

    def get_queryset(self):
        annotate_record_code = self.model.tracked_models.rel.related_model.objects
        return TransactionQueryset(self.model, using=self._db).prefetch_related(
            models.Prefetch("tracked_models", queryset=annotate_record_code),
        )


class TransactionQueryset(CTEQuerySet):
    def ordered_tracked_models(self):
        """TrackedModel in order of their transactions creation order."""

        tracked_models = self.model.tracked_models.rel.related_model.objects.filter(
            transaction__in=self,
        ).order_by(
            "transaction__order",
        )  # order_by record_code, subrecord_code already happened in get_queryset
        return tracked_models

    def with_xml(self):
        from importer.taric import TransactionParser

        cte = With(TrackedModel.objects.with_xml().filter(transaction__in=self))
        return self.with_cte(cte).annotate(
            xml=xml.XMLSerialize(TransactionParser().serializer(cte)),
        )

    def not_empty(self):
        # Django bug 2361  https://code.djangoproject.com/ticket/2361
        #   Queryset.filter(m2mfield__isnull=False) may duplicate records,
        #   so cannot be used, instead the count() of each tracked_models
        #   resultset is checked.
        full_transactions = self.annotate(models=Count("tracked_models")).filter(
            models__gt=0,
        )
        return self.filter(pk__in=full_transactions)

    def get_xml(self) -> Iterator[str]:
        return (
            self.with_xml()
            .values_list("xml", flat=True)
            .iterator(
                chunk_size=settings.EXPORTER_MAXIMUM_DATABASE_CHUNK,
            )
        )


class Transaction(TimestampedMixin):
    """
    Contains a group of one or more TrackedModel instances that must be applied
    atomically.

    Linked to a WorkBasket and may be contained by one or more Envelopes when exported.

    Business rule validation is performed at Transaction level for creates, updates and
    deletes. Business rules are also validated at the TrackedModel level for creates.
    """

    import_transaction_id = models.IntegerField(null=True, editable=False)
    workbasket = models.ForeignKey(
        "workbaskets.WorkBasket",
        on_delete=models.PROTECT,
        related_name="transactions",
    )

    # The order this transaction appears within the workbasket
    order = models.IntegerField()

    composite_key = models.CharField(max_length=16, unique=True)

    objects = TransactionManager.from_queryset(TransactionQueryset)()

    def clean(self):
        """Validate business rules against contained TrackedModels."""

        if settings.SKIP_VALIDATION:
            return

        self.errors = []

        try:
            BusinessRuleChecker(self.tracked_models.all(), self).validate()
        except BusinessRuleViolation as violation:
            self.errors.append(violation)

        if self.errors:
            raise ValidationError(self.errors)

    def to_json(self):
        """
        Serialize to JSON.

        Used for storing in the session.
        """

        return json.dumps(
            {key: val for key, val in self.__dict__.items() if key != "_state"},
            cls=DjangoJSONEncoder,
        )

    def __enter__(self):
        models.signals.pre_save.connect(self.add_to_transaction, dispatch_uid=id(self))
        return self

    def __exit__(self, *exc):
        models.signals.pre_save.disconnect(
            self.add_to_transaction,
            dispatch_uid=id(self),
        )

    def add_to_transaction(self, instance, **kwargs):
        if hasattr(instance, "transaction"):
            instance.transaction = self

    @classmethod
    def latest_approved(cls) -> Transaction:
        """Returns the transaction most recently committed to the global stream
        of approved transactions."""
        WorkBasket = cls._meta.get_field("workbasket").related_model
        WorkflowStatus = type(WorkBasket._meta.get_field("status").default)
        return (
            cls.objects.exclude(
                workbasket=WorkBasket.objects.first(),
            )
            .filter(
                workbasket__status__in=WorkflowStatus.approved_statuses(),
            )
            .order_by("order")
            .last()
        )


class TransactionGroup(models.Model):
    """
    An ordered group of Transactions.

    Transactions often must be applied in a specific sequence, for example to ensure
    a Measure exists before a Footnote can be associated with it.

    A Transaction may belong to several groups, for example a group associated with an
    imported Envelope, and with a WorkBasket.
    """

    group_id = models.IntegerField()
    order_in_group = models.IntegerField()
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT)
