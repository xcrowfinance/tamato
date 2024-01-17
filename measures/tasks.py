import logging

from common.celery import app
from measures.models import MeasuresBulkCreator

logger = logging.getLogger(__name__)


@app.task
def bulk_create_measures(measures_bulk_creator_pk: int) -> None:
    """Bulk create measures from serialized measures form data saved within an
    instance of MeasuresBulkCreator."""

    measures_bulk_creator = MeasuresBulkCreator.objects.get(pk=measures_bulk_creator_pk)
    measures = measures_bulk_creator.create_measures()

    logger.info(
        f"bulk_create_measures() - created {len(measures)} measures with PKs "
        f"[{', '.join([m.pk for m in measures])}].",
    )
