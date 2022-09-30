from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from django.test import override_settings
from django.urls import reverse
from django.utils.timezone import localtime

from checks.tests.factories import TrackedModelCheckFactory
from common.models.utils import override_current_transaction
from common.tests import factories
from common.tests.factories import GeographicalAreaFactory
from common.tests.factories import GoodsNomenclatureFactory
from common.tests.factories import MeasureFactory
from common.tests.util import validity_period_post_data
from common.validators import UpdateType
from exporter.tasks import upload_workbaskets
from measures.models import Measure
from workbaskets import models
from workbaskets.forms import SelectableObjectsForm
from workbaskets.models import WorkBasket
from workbaskets.tests.util import assert_workbasket_valid
from workbaskets.validators import WorkflowStatus
from workbaskets.views import ui

pytestmark = pytest.mark.django_db


def test_workbasket_create_form_creates_workbasket_object(
    valid_user_api_client,
):

    # Post a form
    create_url = reverse("workbaskets:workbasket-ui-create")

    form_data = {
        "title": "My new workbasket",
        "reason": "Making a new workbasket",
    }

    response = valid_user_api_client.post(create_url, form_data)
    #  get the workbasket we have made, and make sure it matches title and description
    workbasket = models.WorkBasket.objects.filter(
        title=form_data["title"],
    )[0]

    assert str(workbasket.id) in response.url
    assert workbasket.title == form_data["title"]
    assert workbasket.reason == form_data["reason"]


def test_workbasket_create_user_not_logged_in_dev_sso_disabled(client, settings):
    """Tests that, when a user who hasn't logged in tries to create a workbasket
    in the dev env with SSO disabled, they are redirected to the login page."""
    settings.ENV = "dev"
    settings.SSO_ENABLED = False
    settings.LOGIN_URL = reverse("login")
    settings.MIDDLEWARE.remove("authbroker_client.middleware.ProtectAllViewsMiddleware")
    create_url = reverse("workbaskets:workbasket-ui-create")
    form_data = {
        "title": "My new workbasket",
        "reason": "Making a new workbasket",
    }
    response = client.post(create_url, form_data)

    assert response.status_code == 302
    assert response.url == f"{settings.LOGIN_URL}?next={create_url}"


def test_workbasket_create_without_permission(client):
    """Tests that WorkBasketCreate returns 403 to user without add_workbasket
    permission."""
    create_url = reverse("workbaskets:workbasket-ui-create")
    form_data = {
        "title": "My new workbasket",
        "reason": "Making a new workbasket",
    }
    user = factories.UserFactory.create()
    client.force_login(user)
    response = client.post(create_url, form_data)

    assert response.status_code == 403


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPOGATES=True)
@patch("exporter.tasks.upload_workbaskets")
def test_submit_workbasket(
    mock_upload,
    approved_transaction,
    unapproved_transaction,
    valid_user,
    client,
):
    workbasket = unapproved_transaction.workbasket
    assert_workbasket_valid(workbasket)

    url = reverse(
        "workbaskets:workbasket-ui-submit",
        kwargs={"pk": workbasket.pk},
    )

    client.force_login(valid_user)
    response = client.get(url)

    assert response.status_code == 302
    assert response.url == reverse("home")

    workbasket.refresh_from_db()

    assert workbasket.approver is not None
    assert "workbasket" not in client.session
    mock_upload.delay.assert_called_once_with()


@pytest.mark.parametrize(
    ("other_statuses", "should_reuse"),
    (
        ({}, False),
        ({WorkflowStatus.PROPOSED, WorkflowStatus.ARCHIVED}, False),
        ({WorkflowStatus.EDITING}, True),
    ),
    ids=(
        "will create basket if none exists",
        "will not reuse unapproved baskets",
        "will reuse basket in EDITING state",
    ),
)
@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPOGATES=True)
@patch("exporter.tasks.upload_workbaskets")
def test_edit_after_submit(
    upload,
    valid_user_client,
    date_ranges,
    other_statuses,
    should_reuse,
):
    # submit a workbasket containing a newly created footnote
    workbasket = factories.WorkBasketFactory.create()
    with workbasket.new_transaction():
        footnote = factories.FootnoteFactory.create(
            update_type=UpdateType.CREATE,
        )
    assert footnote.transaction.workbasket == workbasket

    assert_workbasket_valid(workbasket)

    # create workbaskets in different unapproved states
    # to check that the system doesn't select these
    other_baskets = [
        factories.WorkBasketFactory.create(status=other_status)
        for other_status in other_statuses
    ]

    response = valid_user_client.get(
        reverse(
            "workbaskets:workbasket-ui-submit",
            kwargs={"pk": workbasket.pk},
        ),
    )
    assert response.status_code == 302

    # edit the footnote description start date, to avoid FO4 violation
    description = footnote.descriptions.first()
    description.validity_start = date_ranges.later.lower
    description.save(force_write=True)

    # edit the footnote
    response = valid_user_client.post(
        footnote.get_url("edit"),
        validity_period_post_data(
            date_ranges.later.lower,
            date_ranges.later.upper,
        ),
    )
    assert response.status_code == 302

    # check that the session workbasket has been replaced by a new one
    session_workbasket = WorkBasket.load_from_session(valid_user_client.session)
    assert session_workbasket.id != workbasket.id
    assert session_workbasket.status == WorkflowStatus.EDITING
    assert (session_workbasket in other_baskets) == should_reuse

    # check that the footnote edit is in the new session workbasket
    assert session_workbasket.transactions.count() == 1
    tx = session_workbasket.transactions.first()
    assert tx.tracked_models.count() == 1
    new_footnote_version = tx.tracked_models.first()
    assert new_footnote_version.pk != footnote.pk
    assert new_footnote_version.version_group == footnote.version_group


def test_download(
    approved_workbasket,
    client,
    valid_user,
    hmrc_storage,
    s3_resource,
    s3_object_names,
    settings,
):
    client.force_login(valid_user)
    bucket = "hmrc"
    settings.HMRC_STORAGE_BUCKET_NAME = bucket
    s3_resource.create_bucket(Bucket="hmrc")
    with patch(
        "exporter.storages.HMRCStorage.save",
        wraps=MagicMock(side_effect=hmrc_storage.save),
    ):
        upload_workbaskets.apply()
        url = reverse("workbaskets:workbasket-download")

        response = client.get(url)

        # the url signature will always be unique, so we can only compare the first part of the url
        expected_url, _ = s3_resource.meta.client.generate_presigned_url(
            ClientMethod="get_object",
            ExpiresIn=3600,
            Params={
                "Bucket": settings.HMRC_STORAGE_BUCKET_NAME,
                "Key": s3_object_names("hmrc")[0],
            },
        ).split("?", 1)

        assert response.status_code == 302
        assert expected_url in response.url


def test_review_workbasket_displays_objects_in_current_workbasket(
    valid_user_client,
    session_workbasket,
):
    """Verify that changes in the current workbasket are displayed on the bulk
    selection form of the review workbasket page."""

    with session_workbasket.new_transaction():
        GoodsNomenclatureFactory.create()

    response = valid_user_client.get(
        reverse(
            "workbaskets:workbasket-ui-detail",
            kwargs={"pk": session_workbasket.id},
        ),
    )
    page = BeautifulSoup(
        response.content.decode(response.charset),
        features="lxml",
    )
    for obj in session_workbasket.tracked_models.all():
        field_name = SelectableObjectsForm.field_name_for_object(obj)
        assert page.find("input", {"name": field_name})


def test_review_workbasket_displays_rule_violation_summary(
    valid_user_client,
    session_workbasket,
):
    """Test that the review workbasket page includes an error summary box
    detailing the number of tracked model changes and business rule violations,
    dated to the most recent `TrackedModelCheck`."""
    with session_workbasket.new_transaction() as transaction:
        good = GoodsNomenclatureFactory.create(transaction=transaction)
        check = TrackedModelCheckFactory.create(
            transaction_check__transaction=transaction,
            model=good,
            successful=False,
        )

    response = valid_user_client.get(
        reverse(
            "workbaskets:workbasket-ui-detail",
            kwargs={"pk": session_workbasket.id},
        ),
    )
    page = BeautifulSoup(
        response.content.decode(response.charset),
        features="lxml",
    )
    status_heading = page.find_all("h2", attrs={"class": "govuk-heading-s"})[0]
    error_headings = page.find_all("h2", attrs={"class": "govuk-error-summary__title"})
    tracked_model_count = session_workbasket.tracked_models.count()
    local_created_at = localtime(check.created_at)
    created_at = f"{local_created_at:%d %b %Y %H:%M}"

    assert f"{created_at}): failing business rules." in status_heading.text
    assert f"Number of changes: {tracked_model_count}" in error_headings[0].text
    assert f"Number of violations: 1" in error_headings[1].text


def test_edit_workbasket_page_sets_workbasket(valid_user_client, session_workbasket):
    response = valid_user_client.get(
        reverse("workbaskets:edit-workbasket", kwargs={"pk": session_workbasket.pk}),
    )
    assert response.status_code == 200
    soup = BeautifulSoup(str(response.content), "html.parser")
    assert str(session_workbasket.pk) in soup.select(".govuk-heading-xl")[0].text


def test_workbasket_detail_page_url_params(
    valid_user_client,
    session_workbasket,
):
    url = reverse(
        "workbaskets:workbasket-ui-detail",
        kwargs={"pk": session_workbasket.pk},
    )
    response = valid_user_client.get(url)
    assert response.status_code == 200
    soup = BeautifulSoup(str(response.content), "html.parser")
    buttons = soup.select(".govuk-button.govuk-button--primary")
    for button in buttons:
        # test that accidental spacing in template hasn't mangled the url
        assert " " not in button.get("href")
        assert "%20" not in button.get("href")


def test_select_workbasket_page_200(valid_user_client):
    """
    Checks the page returns 200.

    Then checks that only workbaskets with certain statuses are displayed i.e.
    we don't want users to be able to edit workbaskets that are archived, sent,
    or published.
    """
    factories.WorkBasketFactory.create(status=WorkflowStatus.ARCHIVED)
    factories.WorkBasketFactory.create(status=WorkflowStatus.SENT)
    factories.WorkBasketFactory.create(status=WorkflowStatus.PUBLISHED)
    factories.WorkBasketFactory.create(status=WorkflowStatus.EDITING)
    factories.WorkBasketFactory.create(status=WorkflowStatus.APPROVED)
    factories.WorkBasketFactory.create(status=WorkflowStatus.PROPOSED)
    factories.WorkBasketFactory.create(status=WorkflowStatus.ERRORED)
    valid_statuses = {
        WorkflowStatus.EDITING,
        WorkflowStatus.APPROVED,
        WorkflowStatus.PROPOSED,
        WorkflowStatus.ERRORED,
    }
    response = valid_user_client.get(reverse("workbaskets:workbasket-ui-list"))
    assert response.status_code == 200
    soup = BeautifulSoup(str(response.content), "html.parser")
    statuses = [
        element.text for element in soup.select(".govuk-table__row .status-badge")
    ]
    assert len(statuses) == 4
    assert not set(statuses).difference(valid_statuses)


def test_select_workbasket_without_permission(client):
    """Tests that SelectWorkbasketView returns 403 to user without
    change_workbasket permission."""
    user = factories.UserFactory.create()
    client.force_login(user)
    response = client.get(reverse("workbaskets:workbasket-ui-list"))

    assert response.status_code == 403


@pytest.mark.parametrize(
    "form_action, url_name",
    [
        ("publish-all", "workbaskets:workbasket-ui-submit"),
        ("remove-selected", "workbaskets:workbasket-ui-delete-changes"),
        ("page-prev", "workbaskets:workbasket-ui-detail"),
        ("page-next", "workbaskets:workbasket-ui-detail"),
    ],
)
def test_review_workbasket_redirects(
    form_action,
    url_name,
    valid_user_client,
):
    workbasket = factories.WorkBasketFactory.create(
        status=WorkflowStatus.EDITING,
    )
    with workbasket.new_transaction() as tx:
        factories.FootnoteTypeFactory.create_batch(30, transaction=tx)
    url = reverse("workbaskets:workbasket-ui-detail", kwargs={"pk": workbasket.pk})
    data = {"form-action": form_action}
    response = valid_user_client.post(f"{url}?page=2", data)
    assert response.status_code == 302
    assert reverse(url_name, kwargs={"pk": workbasket.pk}) in response.url

    if form_action == "page-prev":
        assert "?page=1" in response.url

    elif form_action == "page-next":
        assert "?page=3" in response.url


def test_delete_changes_confirm_200(valid_user_client, session_workbasket):
    url = reverse(
        "workbaskets:workbasket-ui-delete-changes-done",
        kwargs={"pk": session_workbasket.pk},
    )
    response = valid_user_client.get(url)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "url_name,",
    (
        "workbaskets:workbasket-ui-delete-changes",
        "workbaskets:edit-workbasket",
        "workbaskets:workbasket-ui-submit",
    ),
)
def test_workbasket_views_without_permission(url_name, client, session_workbasket):
    """Tests that delete, edit, and submit endpoints return 403s to user without
    permissions."""
    url = reverse(
        url_name,
        kwargs={"pk": session_workbasket.pk},
    )
    user = factories.UserFactory.create()
    client.force_login(user)
    response = client.get(url)

    assert response.status_code == 403


def test_workbasket_list_view_get_queryset():
    """Test that WorkBasketList.get_queryset() returns a queryset with the
    expected number of baskets ordered by updated_at."""
    wb_1 = factories.WorkBasketFactory.create()
    wb_2 = factories.WorkBasketFactory.create()
    wb_1.title = "most recently updated"
    wb_1.save()
    view = ui.WorkBasketList()
    qs = view.get_queryset()

    assert qs.count() == 2
    assert qs.first() == wb_1
    assert qs.last() == wb_2


def test_workbasket_list_all_view(valid_user_client):
    """Test that valid user receives a 200 on GET for WorkBasketList view and wb
    values display in html table."""
    wb = factories.WorkBasketFactory.create()
    url = reverse("workbaskets:workbasket-ui-list-all")
    response = valid_user_client.get(url)

    assert response.status_code == 200

    soup = BeautifulSoup(str(response.content), "html.parser")
    table = soup.select("table")[0]
    row_text = [row.text for row in table.findChildren("td")]

    assert wb.title in row_text
    assert str(wb.id) in row_text
    assert wb.get_status_display() in row_text
    assert wb.updated_at.strftime("%d %b %y") in row_text
    assert wb.created_at.strftime("%d %b %y") in row_text
    assert str(wb.tracked_models.count()) in row_text
    assert wb.reason in row_text


def test_workbasket_measures_review(valid_user_client):
    """Test that valid user receives a 200 on GET for
    ReviewMeasuresWorkbasketView and correct measures display in html table."""
    workbasket = factories.WorkBasketFactory.create(
        status=WorkflowStatus.EDITING,
    )
    non_workbasket_measures = factories.MeasureFactory.create_batch(5)

    with workbasket.new_transaction() as tx:
        factories.MeasureFactory.create_batch(30, transaction=tx)

    url = reverse("workbaskets:review-workbasket", kwargs={"pk": workbasket.pk})
    response = valid_user_client.get(url)

    assert response.status_code == 200

    soup = BeautifulSoup(str(response.content), "html.parser")

    non_workbasket_measures_sids = {str(m.sid) for m in non_workbasket_measures}
    measure_sids = [e.text for e in soup.select("table tr td:first-child")]
    workbasket_measures = Measure.objects.filter(
        trackedmodel_ptr__transaction__workbasket_id=workbasket.id,
    ).order_by("sid")
    table_measure_sids = [str(m.sid) for m in workbasket_measures]
    assert table_measure_sids == measure_sids
    assert set(measure_sids).difference(non_workbasket_measures_sids)

    # 5th column is start date
    table_start_dates = {e.text for e in soup.select("table tr td:nth-child(5)")}
    measure_start_dates = {
        f"{m.valid_between.lower:%d %b %Y}" for m in workbasket_measures
    }
    assert not measure_start_dates.difference(table_start_dates)
    # 6th column is end date
    table_end_dates = {e.text for e in soup.select("table tr td:nth-child(6)")}
    measure_end_dates = {
        f"{m.effective_end_date:%d %b %Y}"
        for m in workbasket_measures
        if m.effective_end_date
    }
    assert not measure_end_dates.difference(table_end_dates)


def test_workbasket_measures_review_pagination(
    valid_user_client,
    unapproved_transaction,
):
    """Test that the first 30 measures in the workbasket are displayed in the
    table."""

    with override_current_transaction(unapproved_transaction):
        workbasket = factories.WorkBasketFactory.create(
            status=WorkflowStatus.EDITING,
        )
        factories.MeasureFactory.create_batch(40, transaction=unapproved_transaction)

    url = reverse("workbaskets:review-workbasket", kwargs={"pk": workbasket.pk})
    response = valid_user_client.get(url)

    assert response.status_code == 200

    soup = BeautifulSoup(str(response.content), "html.parser")

    measure_sids = {e.text for e in soup.select("table tr td:first-child")}
    workbasket_measures = Measure.objects.filter(
        trackedmodel_ptr__transaction__workbasket_id=workbasket.id,
    )
    assert measure_sids.issubset({str(m.sid) for m in workbasket_measures})


def test_workbasket_measures_review_conditions(valid_user_client):
    workbasket = factories.WorkBasketFactory.create(
        status=WorkflowStatus.EDITING,
    )
    factories.MeasureFactory.create_batch(5)
    certificate = factories.CertificateFactory.create()
    tx = workbasket.new_transaction()
    measure = factories.MeasureFactory.create(transaction=tx)
    condition = factories.MeasureConditionFactory.create(
        # transaction=tx,
        dependent_measure=measure,
        condition_code__code="B",
        required_certificate=certificate,
        action__code="27",
    )
    url = reverse("workbaskets:review-workbasket", kwargs={"pk": workbasket.pk})
    response = valid_user_client.get(url)
    soup = BeautifulSoup(str(response.content), "html.parser")
    # 11th column is conditions. We're interested in the first (and only) row.
    condition_text = soup.select("table tr td:nth-child(11)")[0].text

    assert "B" in condition_text
    assert certificate.code in condition_text
    assert "27" in condition_text


@patch("workbaskets.tasks.call_check_workbasket_sync.delay")
def test_run_business_rules(check_workbasket, valid_user_client, session_workbasket):
    """Test that a GET request to the run-business-rules endpoint returns a 302,
    redirecting to the review workbasket page, runs the `check_workbasket` task,
    saves the task id on the workbasket, and deletes pre-existing
    `TrackedModelCheck` objects associated with the workbasket."""
    check_workbasket.return_value.id = 123
    assert not session_workbasket.rule_check_task_id

    with session_workbasket.new_transaction() as transaction:
        good = GoodsNomenclatureFactory.create(transaction=transaction)
        check = TrackedModelCheckFactory.create(
            transaction_check__transaction=transaction,
            model=good,
            successful=False,
        )

    session = valid_user_client.session
    session["workbasket"] = {
        "id": session_workbasket.pk,
        "status": session_workbasket.status,
        "title": session_workbasket.title,
    }
    session.save()
    url = reverse(
        "workbaskets:workbasket-ui-detail",
        kwargs={"pk": session_workbasket.id},
    )
    response = valid_user_client.post(
        url,
        {"form-action": "run-business-rules"},
    )

    assert response.status_code == 302
    response_url = f"/workbaskets/{session_workbasket.pk}/"
    # Only compare the response URL up to the query string.
    assert response.url[: len(response_url)] == response_url

    session_workbasket.refresh_from_db()

    check_workbasket.assert_called_once_with(session_workbasket.pk)
    assert session_workbasket.rule_check_task_id
    assert not session_workbasket.tracked_model_checks.exists()


def test_workbasket_violations(valid_user_client, session_workbasket):
    """Test that a GET request to the violations endpoint returns a 200 and
    displays the correct column values for one unsuccessful
    `TrackedModelCheck`."""
    url = reverse(
        "workbaskets:workbasket-ui-violations",
        kwargs={"pk": session_workbasket.pk},
    )
    with session_workbasket.new_transaction() as transaction:
        good = GoodsNomenclatureFactory.create(transaction=transaction)
        check = TrackedModelCheckFactory.create(
            transaction_check__transaction=transaction,
            model=good,
            successful=False,
        )
    session = valid_user_client.session
    session["workbasket"] = {
        "id": session_workbasket.pk,
        "status": session_workbasket.status,
        "title": session_workbasket.title,
        "error_count": session_workbasket.tracked_model_check_errors.count(),
    }
    session.save()
    response = valid_user_client.get(url)

    assert response.status_code == 200

    page = BeautifulSoup(str(response.content), "html.parser")
    table = page.findChildren("table")[0]
    row = table.findChildren("tr")[1]
    cells = row.findChildren("td")

    assert cells[0].text == str(check.pk)
    assert cells[1].text == good._meta.verbose_name.title()
    assert cells[2].text == check.rule_code
    assert cells[3].text == check.message
    assert cells[4].text == f"{check.transaction_check.transaction.created_at:%d %b %Y}"


def test_violation_detail_page(valid_user_client, session_workbasket):
    with session_workbasket.new_transaction() as transaction:
        good = GoodsNomenclatureFactory.create(transaction=transaction)
        check = TrackedModelCheckFactory.create(
            transaction_check__transaction=transaction,
            model=good,
            successful=False,
        )
    url = reverse(
        "workbaskets:workbasket-ui-violation-detail",
        kwargs={"wb_pk": session_workbasket.pk, "pk": check.pk},
    )
    session = valid_user_client.session
    session["workbasket"] = {
        "id": session_workbasket.pk,
        "status": session_workbasket.status,
        "title": session_workbasket.title,
        "error_count": session_workbasket.tracked_model_check_errors.count(),
    }
    session.save()
    response = valid_user_client.get(url)
    assert response.status_code == 200

    soup = BeautifulSoup(str(response.content), "html.parser")
    paragraphs_text = [e.text for e in soup.select("p")]
    assert check.rule_code in paragraphs_text
    assert check.message in paragraphs_text
    # Attribute does not exist yet. This will fail when we eventually add it
    with pytest.raises(AttributeError):
        assert check.solution


@pytest.fixture
def setup(session_workbasket, valid_user_client):
    with session_workbasket.new_transaction() as transaction:
        good = GoodsNomenclatureFactory.create(transaction=transaction)
        measure = MeasureFactory.create(transaction=transaction)
        geo_area = GeographicalAreaFactory.create(transaction=transaction)
        objects = [good, measure, geo_area]
        for obj in objects:
            TrackedModelCheckFactory.create(
                transaction_check__transaction=transaction,
                model=obj,
                successful=False,
            )
    session = valid_user_client.session
    session["workbasket"] = {
        "id": session_workbasket.pk,
        "status": session_workbasket.status,
        "title": session_workbasket.title,
        "error_count": session_workbasket.tracked_model_check_errors.count(),
    }
    session.save()


def test_violation_list_page_sorting_date(setup, valid_user_client, session_workbasket):
    """Tests the sorting of the queryset when GET params are set."""
    url = reverse(
        "workbaskets:workbasket-ui-violations",
        kwargs={"pk": session_workbasket.pk},
    )
    response = valid_user_client.get(f"{url}?sort_by=date&order=asc")

    assert response.status_code == 200

    checks = session_workbasket.tracked_model_check_errors

    soup = BeautifulSoup(str(response.content), "html.parser")
    activity_dates = [
        element.text for element in soup.select("table tbody tr td:nth-child(5)")
    ]
    exp_dates = sorted(
        [f"{c.transaction_check.transaction.created_at:%d %b %Y}" for c in checks],
    )

    assert activity_dates == exp_dates

    response = valid_user_client.get(f"{url}?sort_by=date&order=desc")
    exp_dates.reverse()

    assert activity_dates == exp_dates


def test_violation_list_page_sorting_model_name(
    setup,
    valid_user_client,
    session_workbasket,
):
    """Tests the sorting of the queryset when GET params are set."""
    url = reverse(
        "workbaskets:workbasket-ui-violations",
        kwargs={"pk": session_workbasket.pk},
    )
    response = valid_user_client.get(f"{url}?sort_by=model&order=asc")

    assert response.status_code == 200

    checks = session_workbasket.tracked_model_check_errors

    soup = BeautifulSoup(str(response.content), "html.parser")
    activity_dates = [
        element.text for element in soup.select("table tbody tr td:nth-child(5)")
    ]
    exp_dates = sorted(
        [f"{c.transaction_check.transaction.created_at:%d %b %Y}" for c in checks],
    )

    assert activity_dates == exp_dates

    response = valid_user_client.get(f"{url}?sort_by=model&order=desc")
    exp_dates.reverse()

    assert activity_dates == exp_dates


def test_violation_list_page_sorting_check_name(
    setup,
    valid_user_client,
    session_workbasket,
):
    """Tests the sorting of the queryset when GET params are set."""
    url = reverse(
        "workbaskets:workbasket-ui-violations",
        kwargs={"pk": session_workbasket.pk},
    )
    response = valid_user_client.get(f"{url}?sort_by=check_name&order=asc")

    assert response.status_code == 200

    checks = session_workbasket.tracked_model_check_errors

    soup = BeautifulSoup(str(response.content), "html.parser")
    rule_codes = [
        element.text for element in soup.select("table tbody tr td:nth-child(3)")
    ]
    exp_rule_codes = sorted([c.rule_code for c in checks])

    assert rule_codes == exp_rule_codes

    response = valid_user_client.get(f"{url}?sort_by=check_name&order=desc")
    exp_rule_codes.reverse()
    assert rule_codes == exp_rule_codes


def test_violation_list_page_sorting_ignores_invalid_params(
    setup,
    valid_user_client,
    session_workbasket,
):
    """Tests that the page doesn't break if invalid params are sent."""
    url = reverse(
        "workbaskets:workbasket-ui-violations",
        kwargs={"pk": session_workbasket.pk},
    )
    response = valid_user_client.get(f"{url}?sort_by=foo&order=bar")

    assert response.status_code == 200
