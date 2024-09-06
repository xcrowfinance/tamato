from datetime import datetime

from django.conf import settings
from django.db import models

from common.models.mixins import TimestampedMixin
from workbaskets.models import WorkBasket


class Task(TimestampedMixin):
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(
        "TaskCategory",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    progress_state = models.ForeignKey(
        "TaskProgressState",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )
    workbasket = models.ForeignKey(
        WorkBasket,
        on_delete=models.PROTECT,
        related_name="tasks",
    )

    def __str__(self):
        return self.title


class TaskCategory(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
    )

    class Meta:
        verbose_name_plural = "task categories"

    def __str__(self):
        return self.name


class TaskProgressState(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
    )

    def __str__(self):
        return self.name


class TaskAssigneeQueryset(models.QuerySet):
    def assigned(self):
        return self.exclude(unassigned_at__isnull=False)

    def unassigned(self):
        return self.exclude(unassigned_at__isnull=True)

    def workbasket_workers(self):
        return self.filter(
            assignment_type=TaskAssignee.AssignmentType.WORKBASKET_WORKER,
        )

    def workbasket_reviewers(self):
        return self.filter(
            assignment_type=TaskAssignee.AssignmentType.WORKBASKET_REVIEWER,
        )


class TaskAssignee(TimestampedMixin):
    class AssignmentType(models.TextChoices):
        WORKBASKET_WORKER = "WORKBASKET_WORKER", "Workbasket worker"
        WORKBASKET_REVIEWER = "WORKBASKET_REVIEWER", "Workbasket reviewer"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_to",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        editable=False,
        related_name="assigned_by",
    )
    assignment_type = models.CharField(
        choices=AssignmentType.choices,
        max_length=50,
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        editable=False,
        related_name="assignees",
    )
    unassigned_at = models.DateTimeField(
        auto_now=False,
        blank=True,
        null=True,
    )

    objects = TaskAssigneeQueryset.as_manager()

    def __str__(self):
        return (
            f"User: {self.user} ({self.assignment_type}), " f"Task ID: {self.task.id}"
        )

    @property
    def is_assigned(self):
        return True if not self.unassigned_at else False

    @classmethod
    def unassign_user(cls, user, task):
        try:
            assignment = cls.objects.get(user=user, task=task)
            if assignment.unassigned_at:
                return False
            assignment.unassigned_at = datetime.now()
            assignment.save(update_fields=["unassigned_at"])
            return True
        except cls.DoesNotExist:
            return False


class Comment(TimestampedMixin):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        editable=False,
        related_name="authored_comments",
    )
    content = models.TextField(
        max_length=1000 * 5,  # Max words * average character word length.
    )
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        editable=False,
        related_name="comments",
    )
