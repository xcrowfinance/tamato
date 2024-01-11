from django.urls import path

import reports.utils as utils
from reports import views

app_name = "reports"

urlpatterns = [
    path("reports/", views.index, name="index"),
    path(
        "reports/<str:report_slug>/export-csv/",
        views.export_report_to_csv,
        name="export_report_to_csv",
    ),
]

for report in utils.get_reports():
    urlpatterns.append(
        path(f"reports/{report.slug()}", views.report, name=report.slug()),
    )
