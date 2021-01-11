import logging
from enum import Enum
from functools import cached_property
from itertools import chain
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Optional

import xlrd
from xlrd.sheet import Cell

from certificates.models import Certificate
from common.models import TrackedModel
from geo_areas.models import GeographicalArea
from importer.management.commands.doc_importer import RowsImporter
from importer.management.commands.patterns import BREXIT
from importer.management.commands.patterns import parse_date
from importer.management.commands.patterns import parse_list
from importer.management.commands.patterns import QuotaCreatingPattern
from importer.management.commands.patterns import QuotaType
from importer.management.commands.utils import blank
from importer.management.commands.utils import col
from importer.management.commands.utils import strint
from measures.models import Measurement
from quotas.models import QuotaOrderNumber
from quotas.models import QuotaOrderNumberOrigin
from quotas.models import QuotaOrderNumberOriginExclusion
from quotas.validators import AdministrationMechanism
from quotas.validators import QuotaCategory

logger = logging.getLogger(__name__)


class QuotaSource(Enum):
    PREFERENTIAL = "Pref"
    ORIGIN = "Origin"
    WTO = "WTO"


class QuotaRow:
    def __init__(
        self, row: List[Cell], origin: Optional[GeographicalArea] = None
    ) -> None:
        self.origin = origin
        self.origin_ids = parse_list(strint(row[col("B")]))
        if not any(self.origin_ids):
            self.origin_ids = ["1011"]
        if origin and origin.area_id not in self.origin_ids:
            return
        self.excluded_origin_ids = parse_list(strint(row[col("C")]))
        self.order_number = str(row[col("A")].value).strip()
        self.period_start = parse_date(row[col("D")])
        self.period_end = parse_date(row[col("E")])
        self.type = QuotaType(row[col("F")].value)
        self.volume = self.parse_volume(row[col("G")])
        self.interim_volume = blank(row[col("H")], self.parse_volume)
        self.unit = row[col("I")].value  # TODO convert to measurement
        self.qualifier = blank(row[col("J")].value, str)  # TODO convert to measurement
        self.parent_order_number = blank(row[col("L")].value, str)
        self.coefficient = blank(row[col("M")].value, str)
        self.source = QuotaSource(str(row[col("N")].value))
        self.suspension_start = blank(row[col("O")], parse_date)
        self.suspension_end = blank(row[col("P")], parse_date)
        self.certificate_str = blank(row[col("R")].value, str)
        self.end_use = bool(row[col("Q")].value)
        self.mechanism = (
            AdministrationMechanism.LICENSED
            if self.order_number.startswith("054")
            else AdministrationMechanism.FCFS
        )

    def parse_volume(self, cell: Cell) -> int:
        if cell.ctype == xlrd.XL_CELL_NUMBER:
            return int(cell.value)
        else:
            return int(cell.value.replace(",", ""))

    @cached_property
    def origins(self) -> List[GeographicalArea]:
        logger.debug("Origins: %s", self.origin_ids)
        return [GeographicalArea.objects.get(area_id=e) for e in self.origin_ids]

    @cached_property
    def excluded_origins(self) -> List[GeographicalArea]:
        logger.debug("Excluded origins: %s", self.excluded_origin_ids)
        return [
            GeographicalArea.objects.get(area_id=e) for e in self.excluded_origin_ids
        ]

    @cached_property
    def measurement(self) -> Measurement:
        kwargs = {"measurement_unit__code": self.unit}
        if self.qualifier is None:
            kwargs["measurement_unit_qualifier"] = None
        else:
            kwargs["measurement_unit_qualifier__code"] = self.qualifier

        return Measurement.objects.as_at(BREXIT).get(**kwargs)

    @cached_property
    def certificate(self) -> Optional[Certificate]:
        if self.certificate_str:
            logger.debug("Looking up certificate %s", self.certificate_str)
            return Certificate.objects.get(
                sid=self.certificate_str[1:],
                certificate_type__sid=self.certificate_str[0],
            )
        else:
            return None


class QuotaImporter(RowsImporter):
    def __init__(
        self, *args, category: QuotaCategory, critical_interim: bool = False, **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)
        self.category = category
        self.critical_interim = critical_interim
        self.quotas = {}

    def setup(self) -> Iterator[TrackedModel]:
        self.quota_creator = QuotaCreatingPattern(
            order_number_counter=self.counters["quota_order_number_id"],
            order_number_origin_counter=self.counters["quota_order_number_origin_id"],
            definition_counter=self.counters["quota_definition_id"],
            suspension_counter=self.counters["quota_suspension_id"],
            workbasket=self.workbasket,
            start_date=BREXIT,
            critical_interim=self.critical_interim,
        )
        return iter([])

    def compare_rows(self, new_row: Optional[QuotaRow], old_row: None) -> int:
        assert old_row is None
        return 1 if new_row else -1

    def handle_row(
        self, row: Optional[QuotaRow], old_row: None
    ) -> Iterator[Iterable[TrackedModel]]:
        if row.order_number in self.quotas:
            quota = QuotaOrderNumber.objects.get(order_number=row.order_number)
            defn = self.quota_creator.define_quota(
                quota=quota,
                volume=row.volume,
                unit=row.measurement,
                start_date=row.period_start,
                end_date=row.period_end,
            )
            defn.save()
            models = iter([[defn]])
        else:
            models = self.quota_creator.create(
                row.order_number,
                row.mechanism,
                row.origins,
                self.category,
                row.period_start,
                row.period_end,
                row.measurement,
                row.volume,
                row.type,
                row.interim_volume,
                row.parent_order_number,
                row.coefficient,
                row.excluded_origins,
                row.suspension_start,
                row.suspension_end,
            )

        self.quotas[row.order_number] = row
        for transaction in models:
            if row.mechanism != AdministrationMechanism.LICENSED:
                yield transaction
