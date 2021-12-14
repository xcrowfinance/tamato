from typing import Any
from typing import Optional
from typing import Union

from common.util import TaricDateRange
from common.util import strint


class InvalidItemId(Exception):
    pass


def clean_item_id(value: Union[str, int, float]) -> str:
    """Given a value, return a string representing the 10-digit item id of a
    goods nomenclature item taking into account that the value may have a
    leading zero or trailing zeroes missing."""
    item_id = strint(value)
    if type(value) in (int, float) and len(item_id) % 2 == 1:
        # If we have an odd number of digits its because
        # we lost a leading zero due to the numeric storage
        item_id = "0" + item_id

    item_id = item_id.replace(" ", "").replace(".", "")

    # We need a full 10 digit code so padd with trailing zeroes
    if len(item_id) % 2 != 0:
        raise InvalidItemId(f"Item ID {item_id} contains an odd number of characters")
    item_id = f"{item_id:0<10}"

    return item_id


def date_ranges_overlap(a: TaricDateRange, b: TaricDateRange) -> bool:
    """Returns true if two date ranges overlap."""
    if a.upper and b.lower > a.upper:
        return False
    if b.upper and a.lower > b.upper:
        return False

    return True


def contained_date_range(
    date_range: TaricDateRange,
    containing_date_range: TaricDateRange,
    fallback: Optional[Any] = None,
) -> Optional[TaricDateRange]:
    """
    Returns a trimmed contained range that is fully contained by the container
    range.

    Trimming is not eager: only the minimum amount of trimming is done to ensure
    that the result is fully contained by the container date range.

    If the two ranges do not overlap, the method returns None.
    """
    a = date_range
    b = containing_date_range

    if not date_ranges_overlap(a, b):
        return fallback

    start_date = None
    end_date = None

    if b.upper:
        if a.upper is None or b.upper < a.upper:
            end_date = b.upper
    if b.lower > a.lower:
        start_date = b.lower

    return TaricDateRange(
        start_date or a.lower,
        end_date or a.upper,
    )


def is_contained(
    date_range: TaricDateRange,
    containing_date_range: TaricDateRange,
) -> bool:
    """Returns true iof the date range is fully contained by the containing
    range."""
    contained_range = contained_date_range(
        date_range,
        containing_date_range,
    )

    return contained_range == date_range
