from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.utils import override_settings

from common.tests import factories
from importer.management.commands.import_taric_file import import_taric_file
from importer.tests.management.commands.base import TestCommandBase

pytestmark = pytest.mark.django_db


#  TODO Fix these tests
class TestImportTaricFileCommand(TestCommandBase):
    TARGET_COMMAND = "import_taric_file"

    @override_settings(
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_ALWAYS_EAGER=True,
        BROKER_BACKEND="memory",
    )
    @patch(
        "importer.management.commands.import_taric_file.import_taric_file.setup_batch",
    )
    # @patch("importer.management.commands.import_taric_file.chunk_taric")
    # @patch("importer.management.commands.import_taric_file.run_batch")
    def test_dry_run(
        self,
        example_goods_taric_file_location,
        setup_batch,
        chunk_taric,
        run_batch,
    ):
        user = factories.UserFactory.create(
            email="test.mctest@trade.gov.uk",  # /PS-IGNORE
            first_name="Test",
            last_name="McTest",
        )
        with open(f"{example_goods_taric_file_location}", "rb") as f:
            content = f.read()
        taric_file = SimpleUploadedFile("goods.xml", content, content_type="text/xml")
        import_taric_file(taric_file, user)
        assert setup_batch.assert_called_once()
        # assert chunk_taric.assert_called_once()
        # assert run_batch.assert_called_once()

    # @pytest.mark.parametrize(
    #     "args,exception_type,error_msg",
    #     [
    #         (
    #             [],
    #             pytest.raises(CommandError),
    #             "Error: the following arguments are required: taric_file, user_email",
    #         ),
    #         (
    #             ["foo"],
    #             pytest.raises(CommandError),
    #             "Error: the following arguments are required: user_email",
    #         ),
    #         (
    #             ["foo", "bar"],
    #             pytest.raises(FileNotFoundError),
    #             "No such file or directory",
    #         ),
    #     ],
    # )
    # def test_dry_run_args_errors(self, args, exception_type, error_msg):
    #     with exception_type as ex:
    #         self.call_command_test(*args)

    #     assert error_msg in str(ex.value)

    # def test_help(self, capsys):
    #     get_command_help_text(capsys, self.TARGET_COMMAND, import_taric_file.Command)

    #     out = capsys.readouterr().out

    #     assert "taric_file" in out
    #     assert "Import data from a TARIC XML file into TaMaTo" in out

    #     assert "taric_file           The TARIC3 file to be parsed." in out
    #     assert (
    #         "name                  The name of the batch, the Envelope ID is recommended."
    #         in out
    #     )
    #     assert "-u USERNAME, --username USERNAME" in out
    #     assert "The username to use for the owner of the workbaskets" in out
    #     assert (
    #         "-S {ARCHIVED,EDITING,QUEUED,PUBLISHED,ERRORED}, "
    #         "--status {ARCHIVED,EDITING,QUEUED,PUBLISHED,ERRORED}" in out
    #     )
    #     assert "The status of the workbaskets containing the import" in out
    #     assert (
    #         "-p {SEED_FIRST,SEED_ONLY,REVISION_ONLY}, --partition-scheme {SEED_FIRST,SEED_ONLY,REVISION_ONLY}"
    #         in out
    #     )
    #     assert "Partition to place transactions in approved" in out
    #     assert "-s, --split-codes     Split the file based on record codes" in out
    #     assert "-d DEPENDENCIES, --dependencies DEPENDENCIES" in out
    #     assert "List of batches that need to finish before the current" in out
    #     assert "-c, --commodities     Only import commodities" in out
