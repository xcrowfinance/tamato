import os
from datetime import date

import pandas as pd
from django.core.management import BaseCommand

from reference_documents.models import PreferentialQuota
from reference_documents.models import PreferentialRate
from reference_documents.models import ReferenceDocument
from reference_documents.models import ReferenceDocumentVersion
from reference_documents.models import ReferenceDocumentVersionStatus


class Command(BaseCommand):
    help = "Basic HELP .. todo"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "duties_csv_path",
            type=str,
            help="The absolute path to the duties csv file to import",
        )
        parser.add_argument(
            "quotas_csv_path",
            type=str,
            help="The absolute path to the quotas csv file to import",
        )

        return super().add_arguments(parser)

    def handle(self, *args, **options):
        # TODO: remove all ref doc data - temp while testing
        PreferentialQuota.objects.all().delete()
        PreferentialRate.objects.all().delete()
        ReferenceDocumentVersion.objects.all().delete()
        ReferenceDocument.objects.all().delete()

        # verify each file exists
        if not os.path.isfile(options["duties_csv_path"]):
            raise FileNotFoundError(options["duties_csv_path"])

        if not os.path.isfile(options["quotas_csv_path"]):
            raise FileNotFoundError(options["duties_csv_path"])

        self.duties_csv_path = options["duties_csv_path"]
        self.quotas_csv_path = options["quotas_csv_path"]

        self.quotas_df = self.load_quotas_csv()
        self.duties_df = self.load_duties_csv()

        self.create_ref_docs_and_versions()

    def load_duties_csv(self):
        df = pd.read_csv(
            self.duties_csv_path,
            dtype={
                "Standardised Commodity Code": "object",
                "Valid From": "object",
                "Valid To": "object",
            },
        )
        return df

    def load_quotas_csv(self):
        df = pd.read_csv(
            self.quotas_csv_path,
            dtype={
                "Standardised Commodity Code": "object",
            },
        )
        return df

    def add_pt_quota_if_no_exists(
        self,
        df_row,
        order,
        order_number,
        reference_document_version,
    ):
        if len(order_number) != 6:
            print(f"skipping wonky order number : -{order_number}-")
            return

        comm_code = df_row["Standardised Commodity Code"]
        comm_code = comm_code + ("0" * (len(comm_code) - 10))

        quota_duty_rate = df_row["Quota Duty Rate"]

        volume = df_row["Quota Volume"].replace(",", "")

        units = df_row["Units"]

        quota = reference_document_version.preferential_quotas.filter(
            commodity_code=comm_code,
            quota_order_number=order_number,
        ).first()

        if not quota:
            # add a new one
            quota = PreferentialQuota.objects.create(
                commodity_code=comm_code,
                quota_order_number=order_number,
                quota_duty_rate=quota_duty_rate,
                order=order,
                reference_document_version=reference_document_version,
                volume=volume,
                valid_between=None,
                measurement=units,
            )

            quota.save()

    def add_pt_duty_if_no_exist(self, df_row, df_row_index, reference_document_version):
        # 'Commodity Code', 'Preferential Duty Rate', 'Staging', 'Validity',
        # 'Notes', 'description', 'area_id', 'sid',
        # 'TAP_measure__geographical_area__description',
        # 'measure__geographical_area__sid', 'Document Date', 'Document Version',
        # 'Date Processed', 'Standardised Commodity Code', 'Valid From',
        # 'Valid To', 'Valid Date Difference'

        # check for existing entry for comm code
        comm_code = df_row["Standardised Commodity Code"]
        comm_code = comm_code + ("0" * (len(comm_code) - 10))

        pref_rate = reference_document_version.preferential_rates.filter(
            commodity_code=comm_code,
        ).first()

        if not pref_rate:
            # add a new one
            pref_rate = PreferentialRate.objects.create(
                commodity_code=comm_code,
                duty_rate=df_row["Preferential Duty Rate"],
                order=df_row_index,
                reference_document_version=reference_document_version,
                valid_between=None,
            )

            pref_rate.save()

    # Create base documents
    # Load duties, get unique countries and create base document for each

    def create_ref_docs_and_versions(self):
        areas = pd.unique(self.duties_df["area_id"].values)

        for area in areas:
            # # isolating mexico
            # if area != 'MX':
            #     continue

            print(area)
            ref_doc = (
                ReferenceDocument.objects.all()
                .filter(
                    title=f"Reference document for {area}",
                    area_id=area,
                )
                .first()
            )
            # Create records

            if not ref_doc:
                ref_doc = ReferenceDocument.objects.create(
                    title=f"Reference document for {area}",
                    area_id=area,
                )
                ref_doc.save()

            versions = pd.unique(
                self.duties_df[self.duties_df["area_id"] == area][
                    "Document Version"
                ].values,
            )

            for version in versions:
                print(f" -- {version}")
                # try and find existing
                ref_doc_version = ref_doc.reference_document_versions.filter(
                    version=float(version),
                ).first()
                if (
                    self.duties_df[self.duties_df["area_id"] == area][
                        "Document Date"
                    ].values[0]
                    == "empty_cell"
                ):
                    document_publish_date = None
                else:
                    doc_date_string = str(
                        self.duties_df[self.duties_df["area_id"] == area][
                            "Document Date"
                        ].values[0],
                    )
                    document_publish_date = date(
                        int(doc_date_string[:4]),
                        int(doc_date_string[4:6]),
                        int(doc_date_string[6:]),
                    )

                if not ref_doc_version:
                    # Create version
                    ref_doc_version = ReferenceDocumentVersion.objects.create(
                        reference_document=ref_doc,
                        version=float(version),
                        published_date=document_publish_date,
                        entry_into_force_date=None,
                        status=ReferenceDocumentVersionStatus.EDITING,
                    )

                    ref_doc_version.save()

                # Add duties

                # get duties for area
                df_area_duties = self.duties_df.loc[self.duties_df["area_id"] == area]
                for index, row in df_area_duties.iterrows():
                    print(f' -- -- {row["Standardised Commodity Code"]}')
                    self.add_pt_duty_if_no_exist(row, index, ref_doc_version)

                # Quotas

                # Filter by area_id and document version
                quotas_df = self.quotas_df[self.quotas_df["area_id"] == area]
                quotas_df = self.quotas_df[
                    self.quotas_df["Document Version"] == version
                ]

                add_to_index = 1
                for index, row in quotas_df.iterrows():
                    # split order numbers
                    order_number = row["Quota Number"]
                    order_number = order_number.replace(".", "")

                    if len(order_number) > 6:
                        order_numbers = order_number.split(" ")
                    else:
                        order_numbers = [order_number]

                    for on in order_numbers:
                        print(f' -- -- {on} - {row["Standardised Commodity Code"]}')
                        self.add_pt_quota_if_no_exists(
                            row,
                            index + add_to_index,
                            on,
                            ref_doc_version,
                        )
                        add_to_index += 1
