"""Mixins for models."""
from django.db import models

from common.fields import TaricDateRangeField


class TimestampedMixin(models.Model):
    """Mixin adding timestamps for creation and last update."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ValidityMixin(models.Model):
    """
    The model is live after the validity start date
    (:attr:`valid_between.lower`) and before the validity end date
    (:attr:`valid_between.upper`).

    Start and end validity dates are inclusive – meaning that the model is live
    from the beginning of the start date to the end of the end date. A model
    with the same start and end date is therefore live for 1 day. If the
    validity end date is blank (:attr:`valid_between.upper_inf`) then the model
    is live indefinitely after the start date.

    Validity dates can be modified with a new version of a model, so a model
    that initially has a blank end date can be updated to subsequently add one.
    """

    valid_between = TaricDateRangeField(db_index=True)

    validity_field_name: str = "valid_between"
    """The name of the field that should be used for validity date checking."""

    @classmethod
    def objects_with_validity_field(cls):
        """
        Returns a QuerySet which will have this model's validity date field (as
        specified by :attr:`validity_field_name`) present on the returned
        models.

        The need for this is that some models (e.g.
        :class:`~measures.models.Measure`) use a validity date that is computed
        on demand as part of a database query and hence is not present on the
        default queryset.
        """
        return cls.objects

    class Meta:
        abstract = True
