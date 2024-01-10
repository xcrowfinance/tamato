import pytest

# note : need to import these objects to make them available to the parser
from common.tests.util import preload_import
from quotas.models import QuotaEvent
from taric_parsers.parsers.measure_parser import *
from taric_parsers.parsers.quota_parser import *

pytestmark = pytest.mark.django_db


@pytest.mark.importer_v2
class TestQuotaClosedAndTransferredEventParserV2:
    """
    Could be one of any of the below:

    .. code:: XML


        <xs:element name="quota.closed.and.transferred.event" substitutionGroup="abstract.record">
            <xs:complexType>
                <xs:sequence>
                    <xs:element name="quota.definition.sid" type="SID"/>
                    <xs:element name="occurrence.timestamp" type="Timestamp"/>
                    <!-- QTM148 CUSTD00029679 03/08/2013 CUST-DEV2  -->
                    <!--    <xs:element name="closing.date" type="Date"/> -->
                    <xs:element name="transfer.date" type="Date"/>
                    <xs:element name="quota.closed" type="QuotaClosedCode"/>
                    <!-- CUSTD00029679 - end -->
                    <xs:element name="transferred.amount" type="QuotaAmount"/>
                    <xs:element name="target.quota.definition.sid" type="SID"/>
                </xs:sequence>
            </xs:complexType>
        </xs:element>
    """

    target_parser_class = QuotaClosedAndTransferredEventParserV2

    def test_it_handles_population_from_expected_data_structure_quota_balance_event(
        self,
    ):
        expected_data_example = {
            "quota_definition_sid": "123",
            "occurrence_timestamp": "2020-09-25T14:58:58",
            "transfer_date": "2021-07-04",
            "quota_closed": "zzz",
            "transferred_amount": "19000",
            "target_quota_definition_sid": "123123",
        }

        target = self.target_parser_class()

        target.populate(
            1,  # transaction id
            target.record_code,
            target.subrecord_code,
            1,  # sequence number
            expected_data_example,
        )

        # verify all properties
        assert target.occurrence_timestamp == datetime(2020, 9, 25, 14, 58, 58)
        assert target.quota_definition__sid == 123
        assert target.transfer_date == "2021-07-04"
        assert target.quota_closed == "zzz"
        assert target.transferred_amount == "19000"
        assert target.target_quota_definition_sid == "123123"

        assert (
            target.data
            == '{"quota.closed": "zzz", "transferred.amount": "19000", "transfer.date": "2021-07-04", '
            '"target.quota.definition.sid": "123123"}'
        )

    def test_import(self, superuser):
        importer = preload_import(
            "quota_closed_and_transferred_event_CREATE.xml",
            __file__,
        )

        assert len(importer.parsed_transactions) == 6
        assert len(importer.parsed_transactions[5].parsed_messages) == 1

        target_message = importer.parsed_transactions[5].parsed_messages[0]

        assert target_message.record_code == self.target_parser_class.record_code
        assert target_message.subrecord_code == self.target_parser_class.subrecord_code
        assert type(target_message.taric_object) == self.target_parser_class

        target = target_message.taric_object

        assert target.quota_definition__sid == 100
        assert target.occurrence_timestamp == datetime(2020, 9, 25, 14, 58, 58)

        assert target.transfer_date == "2021-01-01"
        assert target.quota_closed == "ZZZ"
        assert target.transferred_amount == "123.77"
        assert target.target_quota_definition_sid == "56"

        assert (
            target.data == '{"quota.closed": "ZZZ", "transferred.amount": "123.77", '
            '"transfer.date": "2021-01-01", "target.quota.definition.sid": "56"}'
        )

        assert len(importer.issues()) == 0

        assert (
            QuotaEvent.objects.all()
            .filter(subrecord_code=self.target_parser_class.subrecord_code)
            .count()
            == 1
        )

    def test_import_update(self, superuser):
        preload_import(
            "quota_closed_and_transferred_event_CREATE.xml",
            __file__,
            True,
        )
        importer = preload_import(
            "quota_closed_and_transferred_event_UPDATE.xml",
            __file__,
        )

        assert len(importer.issues()) == 1

        assert "Taric objects of type QuotaEvent can't be updated" in str(
            importer.issues()[0],
        )

    def test_import_delete(self, superuser):
        preload_import(
            "quota_closed_and_transferred_event_CREATE.xml",
            __file__,
            True,
        )
        importer = preload_import(
            "quota_closed_and_transferred_event_DELETE.xml",
            __file__,
        )

        assert len(importer.issues()) == 0

        assert QuotaEvent.objects.all().count() == 2
