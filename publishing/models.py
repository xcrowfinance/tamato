from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import F
from django.db.models import Max
from django.db.models import Q
from django.db.models import QuerySet
from django.db.models import TextChoices
from django.db.models import Value
from django.db.models.functions import Coalesce
from django.db.transaction import atomic
from django_fsm import FSMField
from django_fsm import transition
from notifications_python_client import prepare_upload

from common.models.mixins import TimestampedMixin
from notifications.models import NotificationLog
from notifications.tasks import send_emails
from publishing.storages import LoadingReportStorage
from publishing.tasks import schedule_create_xml_envelope_file
from taric.models import Envelope
from workbaskets.models import WorkBasket
from workbaskets.validators import WorkflowStatus


class OperationalStatusQuerySet(QuerySet):
    def current_status(self):
        return self.order_by("pk").last()


class QueueState(TextChoices):
    PAUSED = ("PAUSED", "Envelope processing is paused")
    UNPAUSED = ("UNPAUSED", "Envelope processing is unpaused and may proceed")


class OperationalStatus(models.Model):
    """
    Operational status of the packaging system.

    The packaging queue's state is of primary concern here: either unpaused,
    which allows processing the next available workbasket, or paused, which
    blocks the begin_processing transition of the next available queued
    workbasket until the system is unpaused.
    """

    class Meta:
        ordering = ["pk"]
        verbose_name_plural = "operational statuses"

    objects = OperationalStatusQuerySet.as_manager()

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        editable=False,
        null=True,
    )
    """If a new instance is created as a result of direct user action (for
    instance pausing or unpausing the packaging queue) then `created_by` should
    be associated with that user."""
    queue_state = models.CharField(
        max_length=8,
        default=QueueState.PAUSED,
        choices=QueueState.choices,
        editable=False,
    )

    @classmethod
    def pause_queue(cls, user: settings.AUTH_USER_MODEL) -> "OperationalStatus":
        """
        Transition the workbasket queue into a paused state (if it is not
        already paused) by creating a new `OperationalStatus` and returning it
        to the caller.

        If the queue is already paused, then do nothing and return None.
        """
        if cls.is_queue_paused():
            return None
        return OperationalStatus.objects.create(
            queue_state=QueueState.PAUSED,
            created_by=user,
        )

    @classmethod
    def unpause_queue(cls, user: settings.AUTH_USER_MODEL) -> "OperationalStatus":
        """
        Transition the workbasket queue into an unpaused state (if it is not
        already unpaused) by creating a new `OperationalStatus` and returning it
        to the caller.

        If the queue is already unpaused, then do nothing and return None.
        """
        if not cls.is_queue_paused():
            return None
        return OperationalStatus.objects.create(
            queue_state=QueueState.UNPAUSED,
            created_by=user,
        )

    @classmethod
    def is_queue_paused(cls) -> bool:
        """Returns True if the workbasket queue is paused, False otherwise."""
        current_status = cls.objects.current_status()
        if not current_status or current_status.queue_state == QueueState.PAUSED:
            return True
        else:
            return False


class PackagedWorkBasketDuplication(Exception):
    pass


class PackagedWorkBasketInvalidCheckStatus(Exception):
    pass


class PackagedWorkBasketInvalidQueueOperation(Exception):
    pass


class ProcessingState(TextChoices):
    """Processing states of PackagedWorkBasket instances."""

    AWAITING_PROCESSING = (
        "AWAITING_PROCESSING",
        "Reviewed and awaiting processing",
    )
    """Queued up and awaiting processing."""
    CURRENTLY_PROCESSING = (
        "CURRENTLY_PROCESSING",
        "Currently processing",
    )
    """Picked off the queue and now currently being processed - now attempting
    to ingest envelope into CDS."""
    SUCCESSFULLY_PROCESSED = (
        "SUCCESSFULLY_PROCESSED",
        "Successfully processed",
    )
    """Processing now completed with a successful outcome - envelope ingested
    into CDS."""
    FAILED_PROCESSING = (
        "FAILED_PROCESSING",
        "Failed processing",
    )
    """Processing now completed with a failure outcome - CDS rejected the
    envelope."""
    ABANDONED = (
        "ABANDONED",
        "Abandoned",
    )
    """Processing has been abandoned."""

    @classmethod
    def queued_states(cls):
        """Returns all states that represent a queued  instance, including those
        that are being processed."""
        return (cls.AWAITING_PROCESSING, cls.CURRENTLY_PROCESSING)

    @classmethod
    def completed_processing_states(cls):
        return (
            cls.SUCCESSFULLY_PROCESSED,
            cls.FAILED_PROCESSING,
        )


def report_bucket(instance: "LoadingReport", filename: str):
    """Generate the filepath to upload to loading report bucket."""
    return str(Path(settings.LOADING_REPORTS_STORAGE_DIRECTORY) / filename)


class LoadingReport(TimestampedMixin):
    """Report associated with an attempt to load (process) a PackagedWorkBasket
    instance."""

    file = models.FileField(
        blank=True,
        null=True,
        storage=LoadingReportStorage,
        upload_to=report_bucket,
    )
    comments = models.TextField(
        blank=True,
        max_length=200,
    )


def save_after(func):
    @atomic
    def inner(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self.save()
        return result

    return inner


class PackagedWorkBasketManager(models.Manager):
    @atomic
    def create(self, workbasket, **kwargs):
        """Create a new instance, associating with workbasket."""

        if workbasket.status in WorkflowStatus.unchecked_statuses():
            raise PackagedWorkBasketInvalidCheckStatus(
                "Unable to create PackagedWorkBasket from WorkBasket instance "
                f"({workbasket}) due to unchecked {workbasket.status} status.",
            )

        packaged_work_baskets = PackagedWorkBasket.objects.all_queued().filter(
            workbasket=workbasket,
        )
        if packaged_work_baskets.exists():
            raise PackagedWorkBasketDuplication(
                f"Unable to create PackagedWorkBasket from {workbasket} since "
                "it is already packaged and actively queued - "
                f"{packaged_work_baskets}.",
            )

        position = (
            PackagedWorkBasket.objects.aggregate(
                out=Coalesce(
                    Max("position"),
                    Value(0),
                ),
            )["out"]
            + 1
        )

        new_obj = super().create(workbasket=workbasket, position=position, **kwargs)

        # If this instance is created at queue position 1 and no other
        # PackagedWorkBasket is being processed then schedule envelope creation.
        # See `publishing.tasks.create_xml_envelope_file()` for details.
        if (
            not PackagedWorkBasket.objects.currently_processing()
            and new_obj == PackagedWorkBasket.objects.get_top_awaiting()
        ):
            schedule_create_xml_envelope_file(new_obj)

        return new_obj


class PackagedWorkBasketQuerySet(QuerySet):
    def awaiting_processing(self) -> "PackagedWorkBasketQuerySet":
        """Return all PackagedWorkBasket instances whose processing_state is set
        to AWAITING_PROCESSING."""
        return self.filter(processing_state=ProcessingState.AWAITING_PROCESSING)

    def currently_processing(self) -> "PackagedWorkBasket":
        """
        Returns a single PackagedWorkBasket instance if one currently has a
        processing_state of CURRENTLY_PROCESSING.

        If no instance has a processing_state of CURRENTLY_PROCESSING, then None
        is returned.
        """
        try:
            return self.get(
                processing_state=ProcessingState.CURRENTLY_PROCESSING,
            )
        except ObjectDoesNotExist:
            return None

    def all_queued(self) -> "PackagedWorkBasketQuerySet":
        """Return all PackagedWorkBasket instances whose processing_state is one
        of the actively queued / non-completed states."""
        return self.filter(
            processing_state__in=ProcessingState.queued_states(),
        )

    def completed_processing(self) -> "PackagedWorkBasketQuerySet":
        """Return all PackagedWorkBasket instances whose processing_state is one
        of the completed processing states."""
        return self.filter(
            processing_state__in=ProcessingState.completed_processing_states(),
        )

    def max_position(self) -> int:
        return PackagedWorkBasket.objects.aggregate(out=Max("position"))["out"]

    def get_top_awaiting(self):
        """Return the top-most (position 1) PackagedWorkBasket instance with
        processing_state ProcessingState.AWAITING_PROCESSING, else None if there
        there are no such instances."""
        top = self.filter(
            processing_state=ProcessingState.AWAITING_PROCESSING,
            position=1,
        )
        return top.first() if top else None


class PackagedWorkBasket(TimestampedMixin):
    """
    Encapsulates state and behaviour of a WorkBasket on its journey through the
    packaging process.

    A PackagedWorkBasket must be queued, in priority order, allowing HMRC users
    to pick only the top-most instance when attempting a CDS ingestion. In order
    for a workbasket to be submitted for packaging it must have a complete and
    successful set of rules checks and its status must be QUEUED, indicating
    that it has passed through the review process.
    """

    class Meta:
        ordering = ["position"]

    objects: PackagedWorkBasketQuerySet = PackagedWorkBasketManager.from_queryset(
        PackagedWorkBasketQuerySet,
    )()

    workbasket = models.ForeignKey(
        WorkBasket,
        on_delete=models.PROTECT,
        editable=False,
    )
    position = models.PositiveSmallIntegerField(
        db_index=True,
        editable=False,
    )
    """Position 1 is the top position, ready for processing. An instance that
    is being processed or has been processed has its position value set to 0.
    """
    envelope = models.ForeignKey(
        Envelope,
        null=True,
        on_delete=models.PROTECT,
        editable=False,
    )
    processing_state = FSMField(
        default=ProcessingState.AWAITING_PROCESSING,
        choices=ProcessingState.choices,
        db_index=True,
        protected=True,
        editable=False,
    )
    processing_started_at = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
    )
    """The date and time at which processing_state transitioned to
    CURRENTLY_PROCESSING.
    """
    loading_report = models.ForeignKey(
        LoadingReport,
        null=True,
        on_delete=models.PROTECT,
        editable=False,
    )
    """The report file associated with an attempt (either successful or failed)
    to process / load the associated workbasket's envelope file.
    """
    theme = models.CharField(
        max_length=255,
    )
    description = models.TextField(
        blank=True,
    )
    eif = models.DateField(
        null=True,
        blank=True,
        help_text="For Example, 27 3 2008",
    )
    """The enter into force date determines when changes should go live in CDS.
    A file will need to be ingested by CDS on the day before this. If left,
    blank CDS will ingest the file immediately.
    """
    embargo = models.CharField(
        blank=True,
        null=True,
        max_length=255,
    )
    """The date until which CDS prevents envelope from being displayed after
    ingestion.
    """
    jira_url = models.URLField(
        help_text="Insert Tops Jira ticket link",
    )
    """URL linking the packaged workbasket with a ticket on the Tariff
    Operations (TOPS) project's Jira board.
    """
    create_envelope_task_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        unique=True,
    )
    """ID of Celery task used to generate this instance's associated envelope.
    Its necessary to set null=True (unusually for CharField) in order to support
    the unique=True attribute."""

    @classmethod
    def create_envelope_for_top(cls):
        """Schedule the envelope generation process for the top-most (position
        1) instance."""
        top = cls.objects.get_top_awaiting()
        schedule_create_xml_envelope_file(top)

    # processing_state transition management.

    def begin_processing_condition_at_position_1(self):
        """Django FSM condition: Instance must be at position 1 in order to
        complete the begin_processing transition to CURRENTLY_PROCESSING."""

        return self.position == 1

    def begin_processing_condition_no_instances_currently_processing(self):
        """Django FSM condition: No other instance is currently being processed
        in order to complete the begin_processing and transition this instance
        to CURRENTLY_PROCESSING."""

        return not PackagedWorkBasket.objects.currently_processing()

    @save_after
    @transition(
        field=processing_state,
        source=ProcessingState.AWAITING_PROCESSING,
        target=ProcessingState.CURRENTLY_PROCESSING,
        conditions=[
            begin_processing_condition_at_position_1,
            begin_processing_condition_no_instances_currently_processing,
        ],
        custom={"label": "Begin processing"},
    )
    def begin_processing(self):
        """
        Start processing a PackagedWorkBasket.

        Only a single instance may have its `processing_state` set to
        CURRENTLY_PROCESSING. This is to avoid an otherwise intractable CDS
        envelope sequencing issue that results from a CDS contiguous envelope
        numbering requirement - CDS failed envelope IDs must be recycled and
        therefore CDS envelope processing must complete to establish the correct
        next envelope ID.

        A successful transition also sets the instance's position to 0.

        Because transitioning processing_state can update the position of
        multiple instances it's necessary for this method to perform a save()
        operation upon successful transitions.
        """

        self.processing_started_at = datetime.now()
        self.save()
        self.pop_top()

    @save_after
    @transition(
        field=processing_state,
        source=ProcessingState.CURRENTLY_PROCESSING,
        target=ProcessingState.SUCCESSFULLY_PROCESSED,
        custom={"label": "Processing succeeded"},
    )
    def processing_succeeded(self):
        """
        Processing completed with a successful outcome.

        Because transitioning processing_state can update the position of
        multiple instances it's necessary for this method to perform a save()
        operation upon successful transitions.
        """

    @save_after
    @transition(
        field=processing_state,
        source=ProcessingState.CURRENTLY_PROCESSING,
        target=ProcessingState.FAILED_PROCESSING,
        custom={"label": "Processing failed"},
    )
    def processing_failed(self):
        """
        Processing completed with a failed outcome.

        Because transitioning processing_state can update the position of
        multiple instances it's necessary for this method to perform a save()
        operation upon successful transitions.
        """

    @save_after
    @transition(
        field=processing_state,
        source=ProcessingState.AWAITING_PROCESSING,
        target=ProcessingState.ABANDONED,
        custom={"label": "Abandon"},
    )
    def abandon(self):
        """
        Abandon an instance before any processing attempt has been made.

        Because transitioning processing_state can update the position of
        multiple instances it's necessary for this method to perform a save()
        operation upon successful transitions.
        """

        self.remove_from_queue()
        self.workbasket.dequeue()
        self.workbasket.save()

    @atomic
    def refresh_from_db(self, using=None, fields=None):
        """Reload instance from database but avoid writing to
        self.processing_state directly in order to avoid the exception
        'AttributeError: Direct processing_state modification is not allowed.'
        """
        if fields is None:
            refresh_state = True
            fields = [f.name for f in self._meta.concrete_fields]
        else:
            refresh_state = "processing_state" in fields

        fields_without_state = [f for f in fields if f != "processing_state"]

        super().refresh_from_db(using=using, fields=fields_without_state)

        if refresh_state:
            new_state = (
                type(self)
                .objects.only("processing_state")
                .get(pk=self.pk)
                .processing_state
            )
            self._meta.get_field("processing_state").set_state(self, new_state)

    # Notification management.

    def notify_ready_for_processing(self):
        """
        Notify users that an envelope is ready to download and process.

        This requires that the envelope has been generated and saved and is
        therefore normally called when the process for doing that has completed
        (see `publishing.tasks.create_xml_envelope_file()`).
        """

        personalisation = {
            "envelope_id": self.envelope.envelope_id,
            "theme": self.theme,
            "eif": self.eif if self.eif else "Immediately",
            "jira_url": self.jira_url,
        }
        send_emails.delay(
            template_id=settings.READY_FOR_CDS_TEMPLATE_ID,
            personalisation=personalisation,
        )

    def notify_processing_succeeded(self):
        """
        Notify users that envelope processing has been succeeded for this.

        instance - correctly ingested into HMRC systems.
        """

        f = self.loading_report.file.open("rb")
        personalisation = {
            "envelope_id": self.envelope.envelope_id,
            "transaction_count": self.workbasket.transactions.count(),
            "link_to_file": prepare_upload(f),
        }
        send_emails.delay(
            template_id=settings.CDS_ACCEPTED_TEMPLATE_ID,
            personalisation=personalisation,
        )

    def notify_processing_failed(self):
        """Notify users that envelope processing has been failed - HMRC systems
        rejected this instances associated envelope file."""

        f = self.loading_report.file.open("rb")
        personalisation = {
            "envelope_id": self.envelope.envelope_id,
            "link_to_file": prepare_upload(f),
        }
        send_emails.delay(
            template_id=settings.CDS_REJECTED_TEMPLATE_ID,
            personalisation=personalisation,
        )

    @property
    def cds_notified_notification_log(self) -> NotificationLog:
        """
        NotificationLog instance created when HMRC are notified of an instance's
        envelope being ready for processing by CDS.

        None if there is no NotificationLog instance associated with this
        PackagedWorkBasket instance.
        """
        # TODO: Apply correct lookup when .packaged_work_basket is available.
        # return NotificationLog.objects.filter(packaged_work_basket=self).last()
        return NotificationLog.objects.last() if self.position == 1 else None

    # Queue management.

    @atomic
    def pop_top(self):
        """
        Pop the top-most instance, shuffling all remaining queued instances
        (with `state` AWAITING_PROCESSING) up one position.

        Management of the popped instance's `processing_state` is not altered by
        this function and should be managed separately by the caller.
        """

        if self.position != 1:
            raise PackagedWorkBasketInvalidQueueOperation(
                "Unable to pop instance at position {self.position} in queue "
                "because it is not at position 1.",
            )

        PackagedWorkBasket.objects.filter(position__gt=0).update(
            position=F("position") - 1,
        )
        self.refresh_from_db()

        return self

    @atomic
    def remove_from_queue(self):
        """
        Remove instance from the queue, shuffling all successive queued
        instances (with `state` AWAITING_PROCESSING) up one position.

        Management of the queued instance's `processing_state` is not altered by
        this function and should be managed separately by the caller.
        """

        if self.position == 0:
            raise PackagedWorkBasketInvalidQueueOperation(
                "Unable to remove instance with a position value of 0 from "
                "queue because 0 indicates that it is not a queue member.",
            )

        current_position = self.position
        self.position = 0
        self.save()

        PackagedWorkBasket.objects.filter(position__gt=current_position).update(
            position=F("position") - 1,
        )
        self.refresh_from_db()

        return self

    @atomic
    def promote_to_top_position(self):
        """Promote the instance to the top position of the package processing
        queue so that it occupies position 1."""

        if self.position == 1:
            return self

        position = self.position

        PackagedWorkBasket.objects.filter(
            Q(position__gte=1) & Q(position__lt=position),
        ).update(position=F("position") + 1)

        self.position = 1
        self.save()

        return self

    @atomic
    def promote_position(self):
        """Promote the instance by one position up the package processing
        queue."""

        if self.position == 1:
            return

        obj_to_swap = PackagedWorkBasket.objects.get(position=self.position - 1)
        obj_to_swap.position += 1
        self.position -= 1
        PackagedWorkBasket.objects.bulk_update(
            [self, obj_to_swap],
            ["position"],
        )
        self.refresh_from_db()

        return self

    @atomic
    def demote_position(self):
        """Demote the instance by one position down the package processing
        queue."""

        if self.position == PackagedWorkBasket.objects.max_position():
            return

        obj_to_swap = PackagedWorkBasket.objects.get(position=self.position + 1)
        obj_to_swap.position -= 1
        self.position += 1
        PackagedWorkBasket.objects.bulk_update(
            [self, obj_to_swap],
            ["position"],
        )
        self.refresh_from_db()

        return self
