import contextlib
from datetime import datetime
from datetime import timedelta
from datetime import timezone
from io import StringIO

import pytest
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.urls import reverse
from lxml import etree
from psycopg2._range import DateTimeTZRange

from common.renderers import counter_generator
from common.serializers import TrackedModelSerializer

COMMODITIES_IMPLEMENTED = False
MEASURES_IMPLEMENTED = False
MEURSING_TABLES_IMPLEMENTED = False
INTERDEPENDENT_EXPORT_IMPLEMENTED = False
UTC = timezone.utc

requires_commodities = pytest.mark.skipif(
    not COMMODITIES_IMPLEMENTED, reason="Commodities not implemented",
)

requires_measures = pytest.mark.skipif(
    not MEASURES_IMPLEMENTED, reason="Measures not implemented",
)

requires_meursing_tables = pytest.mark.skipif(
    not MEURSING_TABLES_IMPLEMENTED, reason="Meursing tables not implemented",
)

requires_interdependent_export = pytest.mark.skipif(
    not INTERDEPENDENT_EXPORT_IMPLEMENTED,
    reason="Interdependent exports not implemented",
)


@contextlib.contextmanager
def raises_if(exception, expected):
    try:
        yield
    except exception:
        if not expected:
            raise
    else:
        if expected:
            pytest.fail(f"Did not raise {exception}")


def check_validator(validate, value, expected_valid):
    try:
        validate(value)
    except ValidationError:
        if expected_valid:
            pytest.fail(f'Unexpected validation error for value "{value}"')
    except Exception:
        raise
    else:
        if not expected_valid:
            pytest.fail(f'Expected validation error for value "{value}"')


def validate_taric_xml(factory=None, instance=None, factory_kwargs=None):
    def decorator(func):
        def wraps(api_client, taric_schema, approved_workbasket, *args, **kwargs):
            if not factory and not instance:
                raise AssertionError(
                    "Either a factory or an object instance need to be provided"
                )
            if factory and instance:
                raise AssertionError(
                    "Either a fatory or an object instance need to be provided - not both."
                )

            if not instance:
                factory(workbasket=approved_workbasket, **factory_kwargs or {})

            response = api_client.get(
                reverse("workbasket-detail", kwargs={"pk": approved_workbasket.pk}),
                {"format": "xml"},
            )

            assert response.status_code == 200

            xml = etree.XML(response.content)

            taric_schema.validate(xml)

            assert not taric_schema.error_log, f"XML errors: {taric_schema.error_log}"

            func(
                api_client, taric_schema, approved_workbasket, *args, xml=xml, **kwargs
            )

        return wraps

    return decorator


class Dates:
    normal = DateTimeTZRange(
        datetime(2021, 1, 1, tzinfo=UTC), datetime(2021, 2, 1, tzinfo=UTC),
    )
    earlier = DateTimeTZRange(
        datetime(2020, 1, 1, tzinfo=UTC), datetime(2020, 2, 1, tzinfo=UTC),
    )
    later = DateTimeTZRange(
        datetime(2022, 2, 2, tzinfo=UTC), datetime(2022, 3, 1, tzinfo=UTC),
    )
    big = DateTimeTZRange(
        datetime(2019, 1, 1, tzinfo=UTC), datetime(2023, 1, 2, tzinfo=UTC),
    )
    adjacent_earlier = DateTimeTZRange(
        datetime(2020, 12, 1, tzinfo=UTC), datetime(2020, 12, 31, tzinfo=UTC),
    )
    adjacent_later = DateTimeTZRange(
        datetime(2021, 2, 1, tzinfo=UTC), datetime(2021, 3, 1, tzinfo=UTC),
    )
    adjacent_later_big = DateTimeTZRange(
        datetime(2021, 2, 1, tzinfo=UTC), datetime(2023, 3, 1, tzinfo=UTC),
    )
    overlap_normal = DateTimeTZRange(
        datetime(2021, 1, 15, tzinfo=UTC), datetime(2022, 2, 15, tzinfo=UTC),
    )
    overlap_normal_earlier = DateTimeTZRange(
        datetime(2020, 12, 15, tzinfo=UTC), datetime(2021, 1, 15, tzinfo=UTC),
    )
    overlap_big = DateTimeTZRange(
        datetime(2022, 1, 1, tzinfo=UTC), datetime(2024, 1, 3, tzinfo=UTC),
    )
    after_big = DateTimeTZRange(
        datetime(2024, 2, 1, tzinfo=UTC), datetime(2024, 3, 1, tzinfo=UTC),
    )
    backwards = DateTimeTZRange(
        datetime(2021, 2, 1, tzinfo=UTC), datetime(2021, 1, 2, tzinfo=UTC),
    )
    starts_with_normal = DateTimeTZRange(
        datetime(2021, 1, 1, tzinfo=UTC), datetime(2021, 1, 15, tzinfo=UTC),
    )
    ends_with_normal = DateTimeTZRange(
        datetime(2021, 1, 15, tzinfo=UTC), datetime(2021, 2, 1, tzinfo=UTC),
    )
    current = DateTimeTZRange(
        datetime(2020, 8, 1, tzinfo=UTC) - timedelta(weeks=4),
        datetime(2020, 8, 1, tzinfo=UTC) + timedelta(weeks=4),
    )
    future = DateTimeTZRange(
        datetime(2020, 8, 1, tzinfo=UTC) + timedelta(weeks=10),
        datetime(2020, 8, 1, tzinfo=UTC) + timedelta(weeks=20),
    )
    no_end = DateTimeTZRange(datetime(2021, 1, 1, tzinfo=UTC), None)
    normal_first_half = DateTimeTZRange(
        datetime(2021, 1, 1, tzinfo=UTC), datetime(2021, 1, 15, tzinfo=UTC),
    )


def generate_test_import_xml(obj: dict) -> StringIO:
    xml = render_to_string(
        template_name="workbaskets/taric/transaction_detail.xml",
        context={
            "tracked_models": [obj],
            "transaction_id": 1,
            "message_counter": counter_generator(),
            "counter_generator": counter_generator,
        },
    )

    return StringIO(xml)
