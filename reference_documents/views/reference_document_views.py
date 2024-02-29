from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import UpdateView
from django.views.generic.edit import FormMixin

from geo_areas.models import GeographicalAreaDescription
from reference_documents import forms
from reference_documents import models
from reference_documents.models import ReferenceDocument


class ReferenceDocumentList(PermissionRequiredMixin, ListView):
    """UI endpoint for viewing and filtering workbaskets."""

    template_name = "reference_documents/index.jinja"
    permission_required = "reference_documents.view_reference_document"
    model = ReferenceDocument

    def get_name_by_area_id(self, area_id):
        description = (
            GeographicalAreaDescription.objects.latest_approved()
            .filter(described_geographicalarea__area_id=area_id)
            .order_by("-validity_start")
            .first()
        )
        if description:
            return description.description
        else:
            return f"{area_id} (unknown description)"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        reference_documents = []

        for reference in ReferenceDocument.objects.all().order_by("area_id"):
            if reference.reference_document_versions.count() == 0:
                reference_documents.append(
                    [
                        {"text": "None"},
                        {
                            "text": f"{reference.area_id} - ({self.get_name_by_area_id(reference.area_id)})",
                        },
                        {"text": 0},
                        {"text": 0},
                        {
                            "html": f'<a href="/reference_documents/{reference.id}">Details</a><br>'
                            f"<a href={reverse('reference_documents:update', kwargs={'pk': reference.id})}>Edit</a><br>"
                            f"<a href={reverse('reference_documents:delete', kwargs={'pk': reference.id})}>Delete</a>",
                        },
                    ],
                )

            else:
                reference_documents.append(
                    [
                        {"text": reference.reference_document_versions.last().version},
                        {
                            "text": f"{reference.area_id} - ({self.get_name_by_area_id(reference.area_id)})",
                        },
                        {
                            "text": reference.reference_document_versions.last().preferential_rates.count(),
                        },
                        {
                            "text": reference.reference_document_versions.last().preferential_quotas.count(),
                        },
                        {
                            "html": f'<a href="/reference_documents/{reference.id}">Details</a><br>'
                            f"<a href={reverse('reference_documents:update', kwargs={'pk': reference.id})}>Edit</a><br>"
                            f"<a href={reverse('reference_documents:delete', kwargs={'pk': reference.id})}>Delete</a>",
                        },
                    ],
                )

        context["reference_documents"] = reference_documents
        context["reference_document_headers"] = [
            {"text": "Latest Version"},
            {"text": "Country"},
            {"text": "Duties"},
            {"text": "Quotas"},
            {"text": "Actions"},
        ]
        return context


class ReferenceDocumentDetails(PermissionRequiredMixin, DetailView):
    template_name = "reference_documents/details.jinja"
    permission_required = "reference_documents.view_reference_document"
    model = ReferenceDocument

    def get_context_data(self, *args, **kwargs):
        context = super(ReferenceDocumentDetails, self).get_context_data(
            *args,
            **kwargs,
        )

        context["reference_document_versions_headers"] = [
            {"text": "Version"},
            {"text": "Duties"},
            {"text": "Quotas"},
            {"text": "EIF date"},
            {"text": "Actions"},
        ]
        reference_document_versions = []

        print(self.request)

        for version in context["object"].reference_document_versions.order_by(
            "version",
        ):
            reference_document_versions.append(
                [
                    {
                        "text": version.version,
                    },
                    {
                        "text": version.preferential_rates.count(),
                    },
                    {
                        "text": version.preferential_quotas.count(),
                    },
                    {
                        "text": version.entry_into_force_date,
                    },
                    {
                        "html": f'<a href="/reference_document_versions/{version.id}">Version details</a><br>'
                        f'<a href="{reverse("reference_documents:reference_document_version_edit", args=[version.pk])}">Edit</a><br>'
                        f'<a href="/reference_document_version_alignment_reports/{version.id}">Alignment reports</a>',
                    },
                ],
            )

        context["reference_document_versions"] = reference_document_versions

        return context


class ReferenceDocumentCreate(PermissionRequiredMixin, CreateView):
    template_name = "reference_documents/create.jinja"
    permission_required = "reference_documents.add_referencedocument"
    form_class = forms.ReferenceDocumentCreateUpdateForm

    def get_success_url(self):
        return reverse(
            "reference_documents:confirm-create",
            kwargs={"pk": self.object.pk},
        )


class ReferenceDocumentUpdate(PermissionRequiredMixin, UpdateView):
    model = models.ReferenceDocument
    permission_required = "reference_documents.change_referencedocument"
    template_name = "reference_documents/update.jinja"
    form_class = forms.ReferenceDocumentCreateUpdateForm

    def get_success_url(self):
        return reverse(
            "reference_documents:confirm-update",
            kwargs={"pk": self.object.pk},
        )


class ReferenceDocumentDelete(PermissionRequiredMixin, FormMixin, DeleteView):
    form_class = forms.ReferenceDocumentDeleteForm
    model = ReferenceDocument
    permission_required = "reference_documents.delete_referencedocument"
    template_name = "reference_documents/delete.jinja"

    # TODO: Update this to get rid of FormMixin with Django 4.2 as no need to overwrite the post anymore
    def get_success_url(self) -> str:
        return reverse(
            "reference_documents:confirm-delete",
            kwargs={"deleted_pk": self.kwargs["pk"]},
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.get_object()
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object.delete()
        return redirect(self.get_success_url())


class ReferenceDocumentConfirmCreate(DetailView):
    template_name = "reference_documents/confirm_create.jinja"
    model = ReferenceDocument


class ReferenceDocumentConfirmUpdate(DetailView):
    template_name = "reference_documents/confirm_update.jinja"
    model = ReferenceDocument


class ReferenceDocumentConfirmDelete(TemplateView):
    template_name = "reference_documents/confirm_delete.jinja"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["deleted_pk"] = self.kwargs["deleted_pk"]
        return context_data
