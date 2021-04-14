import time
from typing import Type

import django.contrib.auth.views
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import OperationalError
from django.db import connection
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import generic
from django_filters.views import FilterView
from redis.exceptions import TimeoutError as RedisTimeoutError

from common.models import TrackedModel
from common.models import Transaction
from common.pagination import build_pagination_list
from common.validators import UpdateType
from workbaskets.models import WorkBasket
from workbaskets.views.mixins import WithCurrentWorkBasket


def index(request):
    try:
        workbasket = WorkBasket.objects.is_not_approved().get()
    except WorkBasket.DoesNotExist:
        workbasket = WorkBasket.objects.create(
            title=f"Workbasket {WorkBasket.objects.last().pk+1}",
            author=request.user,
        )

    paginated_tracked_models = Paginator(workbasket.tracked_models, per_page=10)
    page = paginated_tracked_models.get_page(request.GET.get("page", 1))
    return render(
        request,
        "common/index.jinja",
        context={
            "workbasket": workbasket,
            "page_obj": page,
            "paginator": paginated_tracked_models,
            "object_list": page.object_list,
        },
    )


def healthcheck(request):
    start = time.time()
    response_message = (
        "<pingdom_http_custom_check><status><strong>{message}</strong></status>"
        "<response_time><strong>{response_time}</strong></response_time>"
        "</pingdom_http_custom_check>"
    )
    response = HttpResponse(content_type="text/xml")
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"

    try:
        connection.cursor()
    except OperationalError:
        response.write(
            response_message.format(
                message="DB missing",
                response_time=int(time.time() - start),
            ),
        )
        response.status_code = 503
        return response

    try:
        cache.set("__pingdom_test", 1, timeout=1)
    except RedisTimeoutError:
        response.write(
            response_message.format(
                message="Redis missing",
                response_time=int(time.time() - start),
            ),
        )
        response.status_code = 503
        return response

    response.write(
        response_message.format(message="OK", response_time=int(time.time() - start)),
    )
    return response


class LoginView(django.contrib.auth.views.LoginView):
    template_name = "common/login.jinja"


class LogoutView(django.contrib.auth.views.LogoutView):
    template_name = "common/logged_out.jinja"


class CreateView(PermissionRequiredMixin, generic.CreateView):
    """Create a new tracked model."""

    permission_required = "common.add_trackedmodel"
    UPDATE_TYPE = UpdateType.CREATE

    def form_valid(self, form):
        transaction = self.get_transaction()
        transaction.save()
        self.object = form.save(commit=False)
        self.object.update_type = self.UPDATE_TYPE
        self.object.transaction = transaction
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_transaction(self):
        return Transaction()


class UpdateView(PermissionRequiredMixin, generic.UpdateView):
    """Create an updated version of a TrackedModel."""

    UPDATE_TYPE = UpdateType.UPDATE
    permission_required = "common.change_trackedmodel"
    template_name = "common/edit.jinja"

    def get_success_url(self):
        return self.object.get_url("confirm-update")


class DeleteView(CreateView):
    """Create a deletion of a TrackedModel."""

    UPDATE_TYPE = UpdateType.DELETE


class WithPaginationListView(FilterView):
    """Generic list view enabling pagination and adds a page link list to the
    context."""

    paginator_class = Paginator
    paginate_by = settings.REST_FRAMEWORK["PAGE_SIZE"]

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(object_list=object_list, **kwargs)
        page_obj = data["page_obj"]
        page_number = page_obj.number
        data["page_links"] = build_pagination_list(
            page_number,
            page_obj.paginator.num_pages,
        )
        return data


class RequiresSuperuserMixin(UserPassesTestMixin):
    """Only allow superusers to see this view."""

    def test_func(self):
        return self.request.user.is_superuser


class TamatoListView(WithCurrentWorkBasket, WithPaginationListView):
    pass


class TrackedModelDetailMixin:
    """Allows detail URLs to use <Identifying-Fields> instead of <pk>"""

    model: Type[TrackedModel]
    required_url_kwargs = None

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        required_url_kwargs = self.required_url_kwargs or self.model.identifying_fields

        if any(key not in self.kwargs for key in required_url_kwargs):
            raise AttributeError(
                f"{self.__class__.__name__} must be called with {', '.join(required_url_kwargs)} in the URLconf.",
            )

        queryset = queryset.filter(**self.kwargs)

        try:
            return queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(f"No {self.model.__name__} matching the query {self.kwargs}")


class TrackedModelDetailView(
    WithCurrentWorkBasket,
    TrackedModelDetailMixin,
    generic.DetailView,
):
    pass
