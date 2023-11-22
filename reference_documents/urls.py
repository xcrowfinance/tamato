from django.urls import path

from reference_documents import views

urlpatterns = [
    path(
        "reference-documents/",
        views.ReferenceDocumentsListView.as_view(),
        name="reference_documents-ui-list",
    ),
]
