from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from tasks.models import Task
from tasks.models import TaskAssignee
from tasks.models import TaskCategory
from tasks.models import TaskProgressState


class TaskAdminMixin:
    def link_to_task(self, task: Task):
        task_url = reverse(
            "admin:tasks_task_change",
            args=(task.pk,),
        )
        return mark_safe(
            f'<a href="{task_url}">{task.pk}</a>',
        )

    def link_to_workbasket(self, workbasket):
        workbasket_url = reverse(
            "admin:workbaskets_workbasket_change",
            args=(workbasket.pk,),
        )
        return mark_safe(
            f'<a href="{workbasket_url}">{workbasket.pk}</a>',
        )


class TaskAdmin(TaskAdminMixin, admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "description",
        "category",
        "progress_state_name",
        "parent_task_id",
        "workbasket_id",
        "creator",
    ]
    search_fields = ["id", "title", "description"]
    list_filter = ["category", "progress_state"]

    @admin.display(description="Progress state")
    def progress_state_name(self, obj):
        return obj.progress_state.get_name_display()

    def parent_task_id(self, obj):
        if not obj.parent_task:
            return None
        return self.link_to_task(obj.parent_task)

    def workbasket_id(self, obj):
        if not obj.workbasket:
            return "-"
        return self.link_to_workbasket(obj.workbasket)


class TaskCategoryAdmin(admin.ModelAdmin):
    ordering = ["name"]
    search_fields = ["name"]


class TaskProgressStateAdmin(admin.ModelAdmin):
    list_display = ["progress_state_name"]
    ordering = ["name"]
    search_fields = ["name"]

    @admin.display(description="Task progress state")
    def progress_state_name(self, obj):
        return obj.get_name_display()


class TaskAssigneeAdmin(TaskAdminMixin, admin.ModelAdmin):
    list_display = ["id", "assignee", "assignment_type", "task_id", "unassigned_at"]
    search_fields = ["user__username", "assignment_type", "task__id"]

    @admin.display(description="User")
    def assignee(self, obj):
        if not obj.user:
            return "Missing user!"
        return obj.user.get_displayname()

    def task_id(self, obj):
        if not obj.task:
            return "Missing task!"
        return self.link_to_task(obj.task)


admin.site.register(Task, TaskAdmin)

admin.site.register(TaskCategory, TaskCategoryAdmin)

admin.site.register(TaskProgressState, TaskProgressStateAdmin)

admin.site.register(TaskAssignee, TaskAssigneeAdmin)
