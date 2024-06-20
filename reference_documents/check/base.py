from datetime import date
from datetime import timedelta

from commodities.models import GoodsNomenclature
from commodities.models.dc import CommodityCollectionLoader
from commodities.models.dc import CommodityTreeSnapshot
from commodities.models.dc import SnapshotMoment
from common.models import Transaction
from common.util import TaricDateRange
from geo_areas.models import GeographicalArea
from geo_areas.models import GeographicalAreaDescription
from measures.models import Measure
from quotas.models import QuotaDefinition, QuotaAssociation
from quotas.models import QuotaOrderNumber
from reference_documents.models import RefQuotaDefinition, RefQuotaSuspension
from reference_documents.models import RefOrderNumber
from reference_documents.models import RefRate


class BaseCheck:
    name = 'Base check'

    def __init__(self):
        self.dependent_on_passing_check = None

    def run_check(self):
        raise NotImplemented("Please implement on child classes")


class BasePreferentialQuotaCheck(BaseCheck):
    name = 'Base preferential quota check'

    def __init__(self, ref_quota_definition: RefQuotaDefinition):
        super().__init__()
        self.ref_quota_definition = ref_quota_definition
        self.ref_order_number = (
            self.ref_quota_definition.ref_order_number
        )
        self.reference_document_version = (
            self.ref_order_number.reference_document_version
        )
        self.reference_document = self.reference_document_version.reference_document

    def order_number(self):
        """Finds order number in TAP for a given preferential quota."""
        try:
            order_number = QuotaOrderNumber.objects.all().get(
                order_number=self.ref_order_number.order_number,
                valid_between=self.ref_order_number.valid_between,
            )
            return order_number
        except QuotaOrderNumber.DoesNotExist:
            return None

    def geo_area(self):
        """Finds the geo area in TAP for a given preferential quota."""
        geo_area = (
            GeographicalArea.objects.latest_approved()
            .filter(
                area_id=self.reference_document_version.reference_document.area_id,
            )
            .first()
        )
        return geo_area

    def geo_area_description(self):
        """Gets the geo area description for a given preferential quota."""
        geo_area_desc = (
            GeographicalAreaDescription.objects.latest_approved()
            .filter(described_geographicalarea=self.geo_area())
            .last()
        )
        return geo_area_desc.description

    def commodity_code(self):
        """Finds the latest approved version of a commodity code in TAP of a
        given preferential quota."""
        goods = GoodsNomenclature.objects.latest_approved().filter(
            item_id=self.ref_quota_definition.commodity_code,
            valid_between__contains=self.reference_document_version.entry_into_force_date,
            suffix=80,
        )

        if len(goods) == 0:
            return None
        return goods.first()

    def quota_definition(self):
        """Searches for the quota definition period in TAP of a given
        preferential quota."""
        # TODO: Some kind of filtering by measurement / unit
        # TODO: Consider the possibility there could be two valid contiguous quota definitions instead of one
        volume = float(self.ref_quota_definition.volume)
        order_number = self.order_number()
        try:
            quota_definition = QuotaDefinition.objects.all().get(
                order_number=order_number,
                initial_volume=volume,
                valid_between=self.ref_quota_definition.valid_between,
            )
        except QuotaDefinition.DoesNotExist:
            quota_definition = None
        return quota_definition

    def measure(self):
        """
        Looks for a measure(s) in TAP for a given preferential quota.

        It may find more than one if the original measure was end dated and a
        new one was created.
        """
        measures = (
            Measure.objects.all()
            .latest_approved()
            .filter(
                order_number=self.order_number(),
                goods_nomenclature=self.commodity_code(),
                geographical_area=self.geo_area(),
                measure_type__sid__in=[
                    142,
                    143,
                ],
            )
            .order_by("valid_between")
        )
        return self.check_measure_validity(measures)

    def check_measure_validity(self, measures):
        """
        Checks the validity period of the measure(s).

        If there is more than one measure it checks that they are contiguous. It
        then checks that the validity period of the quota order number spans the
        validity period of the measure (ON9).
        """
        if len(measures) == 0:
            return None
        if len(measures) == 1:
            start_date = measures[0].valid_between.lower
            end_date = measures[0].valid_between.upper
            measure_span_period = TaricDateRange(start_date, end_date)
        else:
            for index in range(len(measures) - 1):
                # Check the dates are contiguous and when one measure ends the next one begins
                measure1_end_date = measures[index].valid_between.upper
                measure2_start_date = measures[index + 1].valid_between.lower
                if measure1_end_date + timedelta(days=1) != measure2_start_date:
                    return None
            # Getting start date of first measure and final end date of last measure to get the full validity span
            start_date = measures[0].valid_between.lower
            last_item = len(measures) - 1
            end_date = measures[last_item].valid_between.upper
            measure_span_period = TaricDateRange(start_date, end_date)
        # Check that the validity period of the measure is within the validity period of the order number 0N9
        if not self.validity_period_contains(
                outer_period=self.order_number().valid_between,
                inner_period=measure_span_period,
        ):
            return False
        return measures

    @staticmethod
    def validity_period_contains(outer_period, inner_period):
        """Checks that the inner validity period is within the outer validity
        period."""
        if outer_period.upper:
            if (
                    outer_period.upper >= inner_period.upper
                    and outer_period.lower <= inner_period.lower
            ):
                return True
        elif outer_period.lower <= inner_period.lower:
            return True
        return False


class BasePreferentialQuotaOrderNumberCheck(BaseCheck):
    name = 'Base preferential quota order number check'

    def __init__(self, ref_order_number: RefOrderNumber):
        super().__init__()
        self.ref_order_number = ref_order_number

    def order_number(self):

        kwargs = {}
        kwargs['order_number'] = self.ref_order_number.order_number
        kwargs['valid_between__startswith__lte'] = self.ref_order_number.valid_between.lower

        if self.ref_order_number.valid_between.upper:
            kwargs['valid_between__endswith'] = self.ref_order_number.valid_between.upper
        else:
            kwargs['valid_between__endswith'] = None

        try:
            order_number = QuotaOrderNumber.objects.all().get(
                **kwargs
            )
            return order_number
        except QuotaOrderNumber.DoesNotExist:
            return None

    def main_quota_matches(self):
        order_number = self.order_number()
        # There should be only one association
        associations = QuotaAssociation.objects.latest_approved().filter(
            sub_quota=order_number,
            main_quota__order_number=self.ref_order_number.main_order_number.order_number
        )

        return associations.count() > 0


    def coefficient_matches(self):

        order_number = self.order_number()


class BasePreferentialSuspensionCheck(BaseCheck):

    def __init__(self, ref_quota_suspension: RefQuotaSuspension):
        super().__init__()
        self.ref_quota_suspension = ref_quota_suspension

    def quota_definition(self):
        """Searches for the quota definition period in TAP of a given
        preferential quota."""
        volume = float(self.ref_quota_suspension.ref_quota_definition.volume)
        order_number = self.ref_quota_suspension.ref_quota_definition.ref_order_number.order_number
        try:
            quota_definition = QuotaDefinition.objects.all().get(
                order_number=order_number,
                initial_volume=volume,
                valid_between=self.ref_quota_suspension.ref_quota_definition.valid_between,
            )
        except QuotaDefinition.DoesNotExist:
            quota_definition = None
        return quota_definition

    def order_number(self):
        """Finds order number in TAP for a given preferential quota."""
        try:
            order_number = QuotaOrderNumber.objects.all().get(
                order_number=self.ref_quota_suspension.ref_quota_definition.ref_order_number.order_number,
                valid_between=self.ref_quota_suspension.ref_quota_definition.ref_order_number.valid_between,
            )
            return order_number
        except QuotaOrderNumber.DoesNotExist:
            return None

    def suspension(self):

        quota_definition = self.quota_definition()

        suspensions = quota_definition.quotasuspension_set.latest_approved().filter(
            valid_between=self.ref_quota_suspension.valid_between
        )

        if len(suspensions) == 0:
            return None

        return suspensions.first()


class BasePreferentialRateCheck(BaseCheck):
    name = 'Base preferential rate check'

    def __init__(self, preferential_rate: RefRate):
        super().__init__()
        self.preferential_rate = preferential_rate

    def get_snapshot(self) -> CommodityTreeSnapshot:
        # not liking having to use CommodityTreeSnapshot, but it does to the job
        item_id = self.comm_code().item_id
        while item_id[-2:] == "00":
            item_id = item_id[0: len(item_id) - 2]

        commodities_collection = CommodityCollectionLoader(
            prefix=item_id,
        ).load(current_only=True)

        latest_transaction = Transaction.objects.order_by("created_at").last()

        snapshot = CommodityTreeSnapshot(
            commodities=commodities_collection.commodities,
            moment=SnapshotMoment(transaction=latest_transaction),
        )

        return snapshot

    def comm_code(self):
        goods = GoodsNomenclature.objects.latest_approved().filter(
            item_id=self.preferential_rate.commodity_code,
            valid_between__contains=self.ref_doc_version_eif_date(),
            suffix=80,
        )

        if len(goods) == 0:
            return None

        return goods.first()

    def geo_area(self):
        return (
            GeographicalArea.objects.latest_approved()
            .filter(
                area_id=self.preferential_rate.reference_document_version.reference_document.area_id,
            )
            .first()
        )

    def geo_area_description(self):
        geo_area_desc = (
            GeographicalAreaDescription.objects.latest_approved()
            .filter(described_geographicalarea=self.geo_area())
            .last()
        )
        return geo_area_desc.description

    def ref_doc_version_eif_date(self):
        eif_date = (
            self.preferential_rate.reference_document_version.entry_into_force_date
        )

        # todo : make sure EIf dates are all populated correctly - and remove this
        if eif_date is None:
            eif_date = date.today()

        return eif_date

    def related_measures(self, comm_code_item_id=None):
        if comm_code_item_id:
            good = GoodsNomenclature.objects.latest_approved().filter(
                item_id=comm_code_item_id,
                valid_between__contains=self.ref_doc_version_eif_date(),
                suffix=80,
            )

            if len(good) == 1:
                return (
                    good.first()
                    .measures.latest_approved()
                    .filter(
                        geographical_area=self.geo_area(),
                        valid_between__contains=self.ref_doc_version_eif_date(),
                        measure_type__sid__in=[
                            142,
                        ],  # note : these are the measure types used to identify preferential tariffs
                    )
                )
            else:
                return []
        else:
            return (
                self.comm_code()
                .measures.latest_approved()
                .filter(
                    geographical_area=self.geo_area(),
                    valid_between__contains=self.ref_doc_version_eif_date(),
                    measure_type__sid__in=[
                        142,
                    ],  # note : these are the measure types used to identify preferential tariffs
                )
            )

    def recursive_comm_code_check(
            self,
            snapshot: CommodityTreeSnapshot,
            parent_item_id,
            parent_item_suffix,
            level=1,
    ):
        # find comm code from snapshot
        child_commodities = []
        for commodity in snapshot.commodities:
            if (
                    commodity.item_id == parent_item_id
                    and commodity.suffix == parent_item_suffix
            ):
                child_commodities = snapshot.get_children(commodity)
                break

        if len(child_commodities) == 0:
            print(f'{"-" * level} no more children')
            return False

        results = []
        for child_commodity in child_commodities:
            related_measures = self.related_measures(child_commodity.item_id)

            if len(related_measures) == 0:
                print(f'{"-" * level} FAIL : {child_commodity.item_id}')
                results.append(
                    self.recursive_comm_code_check(
                        snapshot,
                        child_commodity.item_id,
                        child_commodity.suffix,
                        level + 1,
                    ),
                )
            elif len(related_measures) == 1:
                print(f'{"-" * level} PASS : {child_commodity.item_id}')
                results.append(True)
            else:
                # Multiple measures
                print(f'{"-" * level} PASS : multiple : {child_commodity.item_id}')
                results.append(True)

        return False in results

    def run_check(self):
        raise NotImplementedError("Please implement on child classes")
