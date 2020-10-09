import logging
from datetime import datetime
from datetime import timedelta
from enum import Enum
from typing import cast
from typing import IO
from typing import Iterator
from typing import List
from typing import Optional
from typing import Set

import xlrd
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from psycopg2._range import DateTimeTZRange
from xlrd.sheet import Cell
from xlrd.sheet import Sheet

import geo_areas
import settings
from certificates.models import Certificate
from certificates.models import CertificateType
from commodities.models import GoodsNomenclature
from common.models import TrackedModel
from common.renderers import counter_generator
from common.validators import UpdateType
from footnotes.models import Footnote
from footnotes.models import FootnoteDescription
from footnotes.models import FootnoteType
from geo_areas.models import GeographicalArea
from geo_areas.models import GeographicalMembership
from geo_areas.validators import AreaCode
from importer.management.commands.doc_importer import RowsImporter
from importer.management.commands.patterns import BREXIT
from importer.management.commands.patterns import LONDON
from importer.management.commands.patterns import MeasureEndingPattern
from importer.management.commands.patterns import OldMeasureRow
from importer.management.commands.utils import blank
from importer.management.commands.utils import col
from importer.management.commands.utils import EnvelopeSerializer
from importer.management.commands.utils import maybe_min
from importer.management.commands.utils import MeasureTypeSlicer
from importer.management.commands.utils import NomenclatureTreeCollector
from importer.management.commands.utils import SeasonalRateParser
from measures.models import FootnoteAssociationMeasure
from measures.models import Measure
from measures.models import MeasureAction
from measures.models import MeasureCondition
from measures.models import MeasureConditionCode
from measures.models import MeasureExcludedGeographicalArea
from measures.models import MeasureType
from regulations.models import Group
from regulations.models import Regulation
from workbaskets.models import WorkBasket
from workbaskets.validators import WorkflowStatus

logger = logging.getLogger(__name__)


class GeneralFrameworkRegime(Enum):
    NONE = "Not included in GSP"
    GF1 = "GF1"
    GF2 = "GF2"
    GF3 = "GF3"
    IGNORE = "GF preferences set at 10-digit"


class LeastDevelopedCountryRegime(Enum):
    NONE = "Not included in EBA"
    DUTY_FREE_QUOTA_FREE = "DFQF"


class EnhancedFrameworkRegime(Enum):
    NONE = "Not included in GSP+"
    EF1 = "EF1"
    EF2 = "EF2"
    IGNORE = "EF preferences set at the 10 digit level"


class NewRow:
    def __init__(self, new_row: List[Cell]) -> None:
        assert new_row is not None
        commodity_code = new_row[col("A")]

        # Columns to generate General framework measures
        self.gf_regime = GeneralFrameworkRegime(new_row[col("D")].value)
        self.gf_tariff = new_row[col("F")]
        self.gf_exclusion = blank(new_row[col("G")].value, str)
        self.gf_seasonal = str(new_row[col("H")].value) == "Seasonal"
        self.gf4_footnote = str(new_row[col("I")].value) == "GF4"

        # Columns to generate LDC measures
        self.ldc_regime = LeastDevelopedCountryRegime(new_row[col("J")].value)
        self.ldc_tariff = new_row[col("K")]
        self.ldc_exclusion = blank(new_row[col("L")].value, str)

        # Columns to generate Enhanced framework measures
        self.ef_regime = EnhancedFrameworkRegime(new_row[col("M")].value)
        self.ef_tariff = new_row[col("N")]
        self.ef_seasonal = str(new_row[col("O")].value) == "Seasonal"

        if commodity_code.ctype == xlrd.XL_CELL_NUMBER:
            self.item_id = str(int(commodity_code.value))
        else:
            self.item_id = str(commodity_code.value)

        if len(self.item_id) % 2 == 1:
            # If we have an odd number of digits its because
            # we lost a leading zero due to the numeric storage
            self.item_id = "0" + self.item_id

        # We need a full 10 digit code so padd with trailing zeroes
        assert len(self.item_id) % 2 == 0
        if len(self.item_id) == 8:
            self.item_id += "00"

        try:
            assert len(self.item_id) == 10
            self.goods_nomenclature = GoodsNomenclature.objects.as_at(BREXIT).get(
                item_id=self.item_id, suffix="80"
            )
        except GoodsNomenclature.DoesNotExist as ex:
            logger.warning("Failed to find goods nomenclature %s", self.item_id)
            self.goods_nomenclature = None


class GSPImporter(RowsImporter):
    def setup(self) -> Iterator[TrackedModel]:
        self.measure_types = {
            int(m.sid): m
            for m in [
                MeasureType.objects.get(sid="142"),
                MeasureType.objects.get(sid="145"),
            ]
        }
        self.measure_slicer = MeasureTypeSlicer[OldMeasureRow, NewRow](
            get_old_measure_type=lambda r: self.measure_types[r.measure_type],
            get_goods_nomenclature=lambda r: r.goods_nomenclature,
            default_measure_type=MeasureType.objects.get(sid="142"),
        )
        self.seasonal_rate_parser = SeasonalRateParser(BREXIT, LONDON)

        self.old_rows = NomenclatureTreeCollector[OldMeasureRow](
            lambda r: r.goods_nomenclature, BREXIT
        )
        self.new_rows = NomenclatureTreeCollector[NewRow](
            lambda r: r.goods_nomenclature, BREXIT
        )

        self.brexit_to_infinity = DateTimeTZRange(BREXIT, None)
        self.gsp_regulation_group = Group.objects.get(group_id="SPG")

        self.gf_geography = GeographicalArea.objects.get(area_id="2020")
        self.ldc_geography = GeographicalArea.objects.get(area_id="2005")
        self.ef_geography = GeographicalArea.objects.get(area_id="2027")
        self.geo_areas = {
            g.sid: g
            for g in [
                self.gf_geography,
                self.ldc_geography,
                self.ef_geography,
                GeographicalArea.objects.get(area_id="KH"),  # Cambodia
            ]
        }

        self.measure_ending = MeasureEndingPattern(
            workbasket=self.workbasket,
            measure_types=self.measure_types,
            geo_areas=self.geo_areas,
        )

        self.exclusion_areas = {
            "India": GeographicalArea.objects.get(area_id="IN"),
            "Indonesia": GeographicalArea.objects.get(area_id="ID"),
            "Kenya": GeographicalArea.objects.get(area_id="KE"),
        }

        self.gf4_footnote = Footnote.objects.get(
            footnote_id="547",
            footnote_type__footnote_type_id="TM",
        )
        # TODO: add end date to old footnote desc?
        yield FootnoteDescription(
            described_footnote=self.gf4_footnote,
            description="Application of regulation 14(2)(d) of the Trade Preference Scheme (EU Exit) Regulations 2020.",
            description_period_sid=self.counters["footnote_description"](),
            valid_between=self.brexit_to_infinity,
            workbasket=self.workbasket,
            update_type=UpdateType.CREATE,
        )

        self.seasonal_footnote = Footnote.objects.create(
            footnote_id="918",
            footnote_type=FootnoteType.objects.get(footnote_type_id="TM"),
            valid_between=self.brexit_to_infinity,
            workbasket=self.workbasket,
            update_type=UpdateType.CREATE,
        )
        yield self.seasonal_footnote
        yield FootnoteDescription(
            described_footnote=self.seasonal_footnote,
            description="Application of paragraph (5) of Schedule 5 of the Trade Preference Scheme (EU Exit) Regulations 2020.",
            description_period_sid=self.counters["footnote_description"](),
            valid_between=self.brexit_to_infinity,
            workbasket=self.workbasket,
            update_type=UpdateType.CREATE,
        )

        self.gsp_si, _ = Regulation.objects.get_or_create(
            regulation_id="C2100002",
            regulation_group=self.gsp_regulation_group,
            published_at=BREXIT,
            approved=False,
            valid_between=self.brexit_to_infinity,
            workbasket=self.workbasket,
            update_type=UpdateType.CREATE,
        )
        yield self.gsp_si

        self.n990 = Certificate.objects.get(
            sid="990",
            certificate_type=CertificateType.objects.get(sid="N"),
        )

        self.presentation_of_certificate = MeasureConditionCode.objects.get(
            code="B",
        )

        self.apply_mentioned_duty = MeasureAction.objects.get(
            code="27",
        )

        self.subheading_not_allowed = MeasureAction.objects.get(
            code="08",
        )

    def clean_duty_sentence(self, cell: Cell) -> str:
        if cell.ctype == xlrd.XL_CELL_NUMBER:
            # This is a percentage value that Excel has
            # represented as a number.
            return f"{cell.value * 100}%"
        else:
            # All other values will apear as text.
            return cell.value

    def handle_row(
        self,
        new_row: Optional[NewRow],
        old_row: Optional[OldMeasureRow],
    ) -> Iterator[List[TrackedModel]]:
        logger.debug(
            "Have old row: %s. Have new row: %s",
            old_row is not None,
            new_row is not None,
        )
        new_waiting = new_row is not None and not self.new_rows.maybe_push(new_row)
        if self.old_rows.subtree is None:
            self.old_rows.prefix = self.new_rows.prefix
            self.old_rows.subtree = self.new_rows.subtree
        old_waiting = old_row is not None and not self.old_rows.maybe_push(old_row)
        if self.new_rows.subtree is None:
            self.new_rows.prefix = self.old_rows.prefix
            self.new_rows.subtree = self.old_rows.subtree

        if old_waiting or new_waiting:
            # A row was rejected by the collector
            # The collector is full and we should process it
            logger.debug(
                f"Collector full with {len(self.old_rows.buffer)} old"
                f" and {len(self.new_rows.buffer)} new"
            )
            # We must always have an old row to detect the measure type
            if len(self.old_rows.buffer) == 0:
                logger.warning(
                    "No old rows for %s, assuming measure type 142",
                    self.new_rows.prefix.item_id,
                )

            # End date all the old rows in either case
            for row in self.old_rows.buffer:
                assert (
                    row.measure_type in self.measure_types
                ), f"{row.measure_type} not in {self.measure_types}"
                assert (
                    row.geo_sid in self.geo_areas
                ), f"{row.geo_sid} not in {self.geo_areas}"
                assert row.order_number is None
                yield list(self.measure_ending.end_date_measure(row, self.gsp_si))

            # Create measures either for the single measure type or a mix
            for measure_type, row, gn in self.measure_slicer.sliced_new_rows(
                self.old_rows.buffer, self.new_rows.buffer
            ):
                yield list(self.make_new_measure(row, measure_type, gn))

            self.old_rows.reset()
            self.new_rows.reset()
            for transaction in self.handle_row(
                new_row if new_waiting else None,
                old_row if old_waiting else None,
            ):
                yield transaction

        else:
            return iter([])

    def make_new_measure(
        self,
        new_row: NewRow,
        new_measure_type: MeasureType,
        goods_nomenclature: GoodsNomenclature,
    ) -> Iterator[TrackedModel]:
        assert new_row is not None

        # General framework
        if new_row.gf_regime not in [
            GeneralFrameworkRegime.IGNORE,
            GeneralFrameworkRegime.NONE,
        ]:
            footnotes = []
            if new_row.gf_seasonal:
                footnotes.append(self.seasonal_footnote)
            if new_row.gf4_footnote:
                footnotes.append(self.gf4_footnote)

            for model in self.make_gsp_measure(
                new_row.gf_tariff,
                self.gf_geography,
                new_row.gf_exclusion,
                goods_nomenclature,
                new_measure_type,
                footnotes,
            ):
                yield model

        # LDC framework
        if new_row.ldc_regime not in [LeastDevelopedCountryRegime.NONE]:
            for model in self.make_gsp_measure(
                new_row.ldc_tariff,
                self.ldc_geography,
                new_row.ldc_exclusion,
                goods_nomenclature,
                new_measure_type,
            ):
                yield model

        # EF framework
        if new_row.ef_regime not in [
            EnhancedFrameworkRegime.NONE,
            EnhancedFrameworkRegime.IGNORE,
        ]:
            footnotes = []
            if new_row.ef_seasonal:
                footnotes.append(self.seasonal_footnote)

            for model in self.make_gsp_measure(
                new_row.ef_tariff,
                self.ef_geography,
                "",
                goods_nomenclature,
                new_measure_type,
                footnotes,
            ):
                yield model

    def make_gsp_measure(
        self,
        tariff_cell: Cell,
        geography: GeographicalArea,
        geo_exclusion: Optional[str],
        goods_nomenclature: GoodsNomenclature,
        new_measure_type: MeasureType,
        footnotes: List[Footnote] = [],
    ):
        duty_exp = self.clean_duty_sentence(tariff_cell)
        exclusion = (
            self.exclusion_areas[geo_exclusion.strip()] if geo_exclusion else None
        )
        for rate, start, end in self.seasonal_rate_parser.detect_seasonal_rates(
            duty_exp
        ):
            actual_end = maybe_min(end, goods_nomenclature.valid_between.upper)
            new_measure = Measure(
                sid=self.counters["measure_sid_counter"](),
                measure_type=new_measure_type,
                geographical_area=geography,
                goods_nomenclature=goods_nomenclature,
                valid_between=DateTimeTZRange(start, actual_end),
                generating_regulation=self.gsp_si,
                terminating_regulation=(
                    self.gsp_si if actual_end is not None else None
                ),
                update_type=UpdateType.CREATE,
                workbasket=self.workbasket,
            )
            yield new_measure

            if exclusion:
                yield MeasureExcludedGeographicalArea(
                    modified_measure=new_measure,
                    excluded_geographical_area=exclusion,
                    update_type=UpdateType.CREATE,
                    workbasket=self.workbasket,
                )

            for footnote in footnotes:
                yield FootnoteAssociationMeasure(
                    footnoted_measure=new_measure,
                    associated_footnote=footnote,
                    update_type=UpdateType.CREATE,
                    workbasket=self.workbasket,
                )

            if end != actual_end:
                logger.warning(
                    "Measure {} end date capped by {} end date: {:%Y-%m-%d}".format(
                        new_measure.sid, goods_nomenclature.item_id, actual_end
                    )
                )

            # If this is a measure under authorised use, we need to add
            # some measure conditions with the N990 certificate.
            if new_measure_type == self.measure_types[145]:
                yield MeasureCondition(
                    sid=self.counters["measure_condition_sid_counter"](),
                    dependent_measure=new_measure,
                    component_sequence_number=1,
                    condition_code=self.presentation_of_certificate,
                    required_certificate=self.n990,
                    action=self.apply_mentioned_duty,
                    update_type=UpdateType.CREATE,
                    workbasket=self.workbasket,
                )
                yield MeasureCondition(
                    sid=self.counters["measure_condition_sid_counter"](),
                    dependent_measure=new_measure,
                    component_sequence_number=2,
                    condition_code=self.presentation_of_certificate,
                    action=self.subheading_not_allowed,
                    update_type=UpdateType.CREATE,
                    workbasket=self.workbasket,
                )

            try:
                components = self.duty_sentence_parser.parse(rate)
                for component in components:
                    component.component_measure = new_measure
                    component.update_type = UpdateType.CREATE
                    component.workbasket = self.workbasket
                    yield component
            except RuntimeError as ex:
                logger.error(f"Explosion parsing {rate}")
                raise ex


class GSPGeographicAreaImporter:
    def __init__(self, workbasket: WorkBasket, serializer: EnvelopeSerializer) -> None:
        self.workbasket = workbasket
        self.serializer = serializer
        self.gf_geography = GeographicalArea.objects.get(area_id="2020")
        self.ldc_geography = GeographicalArea.objects.get(area_id="2005")
        self.ef_geography = GeographicalArea.objects.get(area_id="2027")
        self.all_areas = GeographicalArea.objects.filter(
            area_code__in=[AreaCode.REGION, AreaCode.COUNTRY]
        ).as_at(BREXIT)
        self.areas = {
            area.get_description().description: area for area in self.all_areas
        }

    def import_sheet(self, sheet: Sheet):
        logger.debug("All: %s", sorted(self.areas.keys()))
        self.update_from_column(sheet.col(0, start_rowx=1), self.ldc_geography)
        self.update_from_column(sheet.col(1, start_rowx=1), self.gf_geography)
        self.update_from_column(sheet.col(2, start_rowx=1), self.ef_geography)
        logger.info("Update of geographical areas complete.")

    def update_from_column(self, column: List[Cell], geography: GeographicalArea):
        # There's no real need for streaming mode here, so let's just load everything
        # into memory and compare using sets
        assert geography.area_code == AreaCode.GROUP

        new_areas = cast(
            Set[GeographicalArea],
            set([self.areas[name.value] for name in column if name.value != ""]),
        )
        old_areas = cast(
            Set[GeographicalArea],
            set(
                map(
                    lambda gm: gm.member,
                    GeographicalMembership.objects.as_at(BREXIT)
                    .filter(geo_group=geography)
                    .all(),
                )
            ),
        )

        logger.debug(
            "Old: %s", list(map(lambda g: g.get_description().description, old_areas))
        )
        to_remove = old_areas - new_areas
        to_add = new_areas - old_areas
        logger.debug(
            "To remove: %s",
            list(map(lambda g: g.get_description().description, to_remove)),
        )
        logger.debug(
            "To add: %s", list(map(lambda g: g.get_description().description, to_add))
        )

        def make_removal(area: GeographicalArea) -> TrackedModel:
            assert area.area_code != AreaCode.GROUP
            membership = (
                GeographicalMembership.objects.as_at(BREXIT)
                .filter(
                    geo_group=geography,
                    member=area,
                )
                .get()
            )

            return GeographicalMembership(
                geo_group=geography,
                member=area,
                valid_between=DateTimeTZRange(
                    membership.valid_between.lower, BREXIT - timedelta(days=1)
                ),
                update_type=UpdateType.UPDATE,
                workbasket=self.workbasket,
            )

        def make_addition(area: GeographicalArea) -> TrackedModel:
            assert area.area_code != AreaCode.GROUP
            return GeographicalMembership(
                geo_group=geography,
                member=area,
                valid_between=DateTimeTZRange(BREXIT, None),
                update_type=UpdateType.CREATE,
                workbasket=self.workbasket,
            )

        self.serializer.render_transaction(list(map(make_removal, to_remove)))
        self.serializer.render_transaction(list(map(make_addition, to_add)))


class Command(BaseCommand):
    help = "Imports a GSP format spreadsheet"

    def add_arguments(self, parser):
        parser.add_argument(
            "new-spreadsheet",
            help="The XLSX file to be parsed.",
            type=str,
        )
        parser.add_argument(
            "--new-skip-rows",
            help="The number of rows from the spreadsheet to skip before importing data",
            type=int,
            default=0,
        )
        parser.add_argument(
            "old-spreadsheet",
            help="The XLSX file containing existing measures to be parsed.",
            type=str,
        )
        parser.add_argument(
            "--old-sheet",
            help="The sheet name in the XLSX containing the data",
            type=str,
            default="Sheet1",
        )
        parser.add_argument(
            "--old-skip-rows",
            help="The number of rows from the spreadsheet to skip before importing data",
            type=int,
            default=0,
        )
        parser.add_argument(
            "--measure-sid",
            help="The SID value to use for the first new measure",
            type=int,
            default=200000000,
        )
        parser.add_argument(
            "--footnote-description-sid",
            help="The SID value to use for the first new footnote description period",
            type=int,
            default=200400,
        )
        parser.add_argument(
            "--transaction-id",
            help="The ID value to use for the first transaction",
            type=int,
            default=140,
        )
        parser.add_argument(
            "--output", help="The filename to output to.", type=str, default="out.xml"
        )

    def handle(self, *args, **options):
        username = settings.DATA_IMPORT_USERNAME
        author = User.objects.get(username=username)

        new_workbook = xlrd.open_workbook(options["new-spreadsheet"])
        schedule_sheet = new_workbook.sheet_by_name("GSP 'continuity' tariffs ")
        geography_sheet = new_workbook.sheet_by_name("List")
        old_workbook = xlrd.open_workbook(options["old-spreadsheet"])
        old_worksheet = old_workbook.sheet_by_name(options["old_sheet"])

        workbasket, _ = WorkBasket.objects.get_or_create(
            title=f"Generalised System of Preferences",
            author=author,
            status=WorkflowStatus.PUBLISHED,
        )

        with open(options["output"], mode="w", encoding="UTF8") as output:
            with EnvelopeSerializer(
                output,
                200002,
                counter_generator(options["transaction_id"]),
            ) as env:
                logger.info(f"Importing from %s", geography_sheet.name)
                geog_importer = GSPGeographicAreaImporter(workbasket, env)
                geog_importer.import_sheet(geography_sheet)

                logger.info(f"Importing from %s", schedule_sheet.name)
                new_rows = schedule_sheet.get_rows()
                old_rows = old_worksheet.get_rows()
                for _ in range(options["new_skip_rows"]):
                    next(new_rows)
                for _ in range(options["old_skip_rows"]):
                    next(old_rows)

                importer = GSPImporter(workbasket, env)
                importer.counters["measure_sid_counter"] = counter_generator(
                    options["measure_sid"]
                )
                importer.counters["measure_condition_sid_counter"] = counter_generator(
                    options["measure_sid"]
                )
                importer.counters["footnote_description"] = counter_generator(
                    options["footnote_description_sid"]
                )
                importer.import_sheets(
                    (NewRow(row) for row in new_rows),
                    (OldMeasureRow(row) for row in old_rows),
                )
