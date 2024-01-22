import re

import pytest
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import Permission
from django.test import modify_settings
from django.test import override_settings
from django.urls import reverse

from common.tests import factories
from common.util import xml_fromstring
from common.views import HealthCheckResponse
from common.views import handler403
from common.views import handler500

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("action", "permission"),
    [
        ("Create new workbasket", "add_workbasket"),
        ("Edit workbaskets", "add_workbasket"),
        ("Package workbaskets", "manage_packaging_queue"),
        ("Process envelopes", "consume_from_packaging_queue"),
        ("Search the tariff", ""),
        ("Import EU Taric files", "add_trackedmodel"),
        ("Search for workbaskets", "view_workbasket"),
    ],
)
def test_home_form_actions_match_permissions(action, permission, client):
    """Tests that the workbasket action form on the home page displays the
    appropriate radio options for the user's permissions."""
    user = factories.UserFactory.create()
    if permission:
        user.user_permissions.add(Permission.objects.get(codename=permission))
    client.force_login(user)

    response = client.get(reverse("home"))
    assert response.status_code == 200

    page = BeautifulSoup(response.content.decode(response.charset), "html.parser")
    assert page.find("label", class_="govuk-radios__label", string=re.compile(action))


def test_index_displays_logout_buttons_correctly_SSO_off_logged_in(valid_user_client):
    settings.SSO_ENABLED = False
    response = valid_user_client.get(reverse("home"))

    assert response.status_code == 200

    page = BeautifulSoup(str(response.content), "html.parser")
    assert page.find_all("a", {"href": "/logout"})


def test_index_redirects_to_login_page_logged_out_SSO_off(client):
    settings.SSO_ENABLED = False
    response = client.get(reverse("home"))

    assert response.status_code == 302
    response.url.startswith(reverse("admin:login"))


def test_index_displays_login_buttons_correctly_SSO_on(valid_user_client):
    settings.SSO_ENABLED = True
    response = valid_user_client.get(reverse("home"))

    assert response.status_code == 200

    page = BeautifulSoup(str(response.content), "html.parser")
    assert not page.find_all("a", {"href": "/logout"})
    assert not page.find_all("a", {"href": "/login"})


@pytest.mark.parametrize(
    ("data", "response_url"),
    (
        (
            {
                "workbasket_action": "CREATE",
            },
            "workbaskets:workbasket-ui-create",
        ),
        (
            {
                "workbasket_action": "EDIT",
            },
            "workbaskets:workbasket-ui-list",
        ),
        (
            {
                "workbasket_action": "PACKAGE_WORKBASKETS",
            },
            "publishing:packaged-workbasket-queue-ui-list",
        ),
        (
            {
                "workbasket_action": "PROCESS_ENVELOPES",
            },
            "publishing:envelope-queue-ui-list",
        ),
        (
            {
                "workbasket_action": "SEARCH",
            },
            "search-page",
        ),
        (
            {
                "workbasket_action": "IMPORT",
            },
            "commodity_importer-ui-list",
        ),
        (
            {
                "workbasket_action": "WORKBASKET_LIST_ALL",
            },
            "workbaskets:workbasket-ui-list-all",
        ),
    ),
)
def test_workbasket_action_form_response_redirects_user(
    valid_user,
    client,
    data,
    response_url,
):
    client.force_login(valid_user)
    response = client.post(reverse("home"), data)
    assert response.status_code == 302
    assert response.url == reverse(response_url)


@pytest.mark.parametrize(
    "response, status_code, status",
    [
        (HealthCheckResponse(), 200, "OK"),
        (HealthCheckResponse().fail("Not OK"), 503, "Not OK"),
    ],
)
def test_healthcheck_response(response, status_code, status):
    assert response.status_code == status_code
    payload = xml_fromstring(response.content)
    assert payload.tag == "pingdom_http_custom_check"
    assert payload[0].tag == "status"
    assert payload[0].text == status
    assert payload[1].tag == "response_time"


def test_app_info_non_superuser(valid_user_client):
    """Users without the superuser permission have a restricted view of
    application information."""
    response = valid_user_client.get(reverse("app-info"))

    assert response.status_code == 200

    page = BeautifulSoup(str(response.content), "html.parser")
    h2_elements = page.select(".info-section h2")

    assert len(h2_elements) == 2
    assert "Active business rule checks" in h2_elements[0].text
    assert "Active envelope generation tasks" in h2_elements[1].text


def test_app_info_superuser(superuser_client, new_workbasket):
    """
    Superusers should have an unrestricted view of application information.

    The new_workbasket fixture provides access to transaction information in the
    deployment infomation section.
    """
    response = superuser_client.get(reverse("app-info"))

    assert response.status_code == 200

    page = BeautifulSoup(str(response.content), "html.parser")
    h2_elements = page.select(".info-section h2")

    assert len(h2_elements) == 3
    assert "Deployment information" in h2_elements[0].text
    assert "Active business rule checks" in h2_elements[1].text
    assert "Active envelope generation tasks" in h2_elements[2].text


def test_index_displays_footer_links(valid_user_client):
    response = valid_user_client.get(reverse("home"))

    assert response.status_code == 200

    page = BeautifulSoup(str(response.content), "html.parser")
    a_tags = page.select("footer a")

    assert len(a_tags) == 7
    assert "Privacy policy" in a_tags[0].text
    assert (
        a_tags[0].attrs["href"]
        == "https://workspace.trade.gov.uk/working-at-dit/policies-and-guidance/policies/tariff-application-privacy-policy/"
    )


def test_search_page_displays_links(valid_user_client):
    url = reverse("search-page")
    response = valid_user_client.get(url)
    assert response.status_code == 200

    page = BeautifulSoup(str(response.content), "html.parser")
    links = page.select(".govuk-link")
    assert len(links) == 8


def test_handler403(client):
    request = client.get("/")
    response = handler403(request)

    assert response.status_code == 403
    assert response.template_name == "common/403.jinja"

    user = factories.UserFactory.create()
    client.force_login(user)
    response = client.get(reverse("workbaskets:workbasket-ui-list"))

    assert response.status_code == 403
    assert response.template_name == "common/403.jinja"


def test_handler500(client):
    request = client.get("/")
    response = handler500(request)

    assert response.status_code == 500
    assert response.template_name == "common/500.jinja"


def test_accessibility_statement_view_returns_200(valid_user_client):
    url = reverse("accessibility-statement")
    response = valid_user_client.get(url)

    assert response.status_code == 200

    page = BeautifulSoup(str(response.content), "html.parser")
    assert (
        "Accessibility statement for the Tariff application platform"
        in page.select("h1")[0].text
    )


@override_settings(MAINTENANCE_MODE=True)
@modify_settings(
    MIDDLEWARE={
        "append": "common.middleware.MaintenanceModeMiddleware",
    },
)
def test_user_redirect_during_maintenance_mode(valid_user_client):
    response = valid_user_client.get(reverse("home"))
    assert response.status_code == 302
    assert response.url == reverse("maintenance")


def test_maintenance_mode_page_content(valid_user_client):
    response = valid_user_client.get(reverse("maintenance"))
    assert response.status_code == 200
    assert "Sorry, the service is unavailable" in str(response.content)
