from typing import Iterable
from unittest.mock import patch

import pytest
from django_fsm import TransitionNotAllowed

from common.models import TrackedModel
from common.models.transactions import Transaction
from common.models.transactions import TransactionPartition
from common.tests import factories
from common.tests.factories import ApprovedTransactionFactory
from common.tests.factories import SeedFileTransactionFactory
from common.tests.factories import TransactionFactory
from common.tests.factories import WorkBasketFactory
from common.tests.util import assert_transaction_order
from common.validators import UpdateType
from workbaskets.models import REVISION_ONLY
from workbaskets.models import SEED_FIRST
from workbaskets.models import SEED_ONLY
from workbaskets.models import TRANSACTION_PARTITION_SCHEMES
from workbaskets.models import TransactionPartitionScheme
from workbaskets.models import UserTransactionPartitionScheme
from workbaskets.models import get_partition_scheme
from workbaskets.validators import WorkflowStatus

pytestmark = pytest.mark.django_db


def test_workbasket_transactions():
    workbasket = factories.WorkBasketFactory.create()
    tx1 = workbasket.new_transaction(composite_key="test1")

    with tx1:
        measure = factories.MeasureFactory.create()

    assert measure.transaction == tx1
    assert workbasket.transactions.count() == 1

    tx2 = workbasket.new_transaction(composite_key="test2")
    assert workbasket.transactions.first() == tx1

    with tx2:
        assoc = factories.FootnoteAssociationMeasureFactory.create(
            footnoted_measure=measure,
        )

    assert assoc.transaction == tx2
    assert assoc.associated_footnote.transaction == tx2
    assert workbasket.transactions.count() == 2


@patch("exporter.tasks.upload_workbaskets")
def test_workbasket_transition(upload, workbasket, transition, valid_user):
    """Tests all combinations of initial workbasket status and transition,
    testing that valid transitions do not error, and invalid transitions raise
    TransitionNotAllowed."""

    transition_args = [valid_user, SEED_FIRST] if transition.name == "approve" else []

    try:
        getattr(workbasket, transition.name)(*transition_args)
        assert workbasket.status == transition.target.value
    except TransitionNotAllowed:
        assert transition.name not in [
            t.name for t in workbasket.get_available_status_transitions()
        ]


def test_get_tracked_models(new_workbasket):
    for _ in range(2):
        factories.FootnoteFactory.create()

    assert TrackedModel.objects.count() > 2
    assert new_workbasket.tracked_models.count() == 2


@patch("exporter.tasks.upload_workbaskets")
def test_workbasket_accepted_updates_current_tracked_models(
    upload,
    new_workbasket,
    valid_user,
):
    original_footnote = factories.FootnoteFactory.create()
    new_footnote = original_footnote.new_version(
        workbasket=new_workbasket,
        update_type=UpdateType.UPDATE,
    )

    assert new_footnote.version_group.current_version.pk == original_footnote.pk

    new_workbasket.submit_for_approval()
    new_footnote.refresh_from_db()
    assert new_footnote.version_group.current_version.pk == original_footnote.pk
    new_workbasket.approve(valid_user, SEED_FIRST)
    new_footnote.refresh_from_db()
    assert new_footnote.version_group.current_version.pk == new_footnote.pk


@patch("exporter.tasks.upload_workbaskets")
def test_workbasket_errored_updates_tracked_models(
    upload,
    new_workbasket,
    valid_user,
    settings,
):
    settings.TRANSACTION_SCHEMA = "workbaskets.models.SEED_FIRST"
    original_footnote = factories.FootnoteFactory.create()
    new_footnote = original_footnote.new_version(
        workbasket=new_workbasket,
        update_type=UpdateType.UPDATE,
    )
    assert new_footnote.version_group.current_version.pk == original_footnote.pk

    new_workbasket.submit_for_approval()
    new_footnote.refresh_from_db()
    assert new_footnote.version_group.current_version.pk == original_footnote.pk
    new_workbasket.approve(valid_user, SEED_FIRST)
    new_footnote.refresh_from_db()
    assert new_footnote.version_group.current_version.pk == new_footnote.pk
    new_workbasket.export_to_cds()
    new_footnote.refresh_from_db()
    assert new_footnote.version_group.current_version.pk == new_footnote.pk
    new_workbasket.cds_error()
    new_footnote.refresh_from_db()
    assert new_footnote.version_group.current_version.pk == original_footnote.pk


@pytest.mark.parametrize("status", [WorkflowStatus.EDITING, WorkflowStatus.PROPOSED])
def test_draft_status_as_transaction_partition_draft_no_first_seed(
    status,
):
    """When first_partition_is_seed is False, draft workbaskets should generate
    a DRAFT transaction partition value."""
    partition_scheme = SEED_FIRST
    assert isinstance(partition_scheme, TransactionPartitionScheme)

    partition = partition_scheme.get_partition(status)

    assert partition == TransactionPartition.DRAFT


@pytest.mark.parametrize("status", WorkflowStatus.approved_statuses())
@pytest.mark.parametrize(
    "partition_scheme,expected_partition",
    [
        (
            UserTransactionPartitionScheme(TransactionPartition.SEED_FILE, "test text"),
            TransactionPartition.SEED_FILE,
        ),
        (
            UserTransactionPartitionScheme(TransactionPartition.REVISION, "test text"),
            TransactionPartition.REVISION,
        ),
    ],
)
def test_user_partition_scheme_passes_approved_workbaskets(
    status,
    partition_scheme,
    expected_partition,
):
    """UserTransactionPartitionScheme get_partition should return its
    approved_partition on being passed an approved workbasket."""
    partition_result = partition_scheme.get_partition(status)
    assert partition_result == partition_scheme.get_approved_partition()
    assert partition_result == expected_partition


@pytest.mark.parametrize(
    "partition_scheme,expected_partition,command_line_name",
    [
        (SEED_ONLY, TransactionPartition.SEED_FILE, "SEED_ONLY"),
        (REVISION_ONLY, TransactionPartition.REVISION, "REVISION_ONLY"),
    ],
)
def test_user_partitions_have_expected_values(
    partition_scheme,
    expected_partition,
    command_line_name,
):
    """Verify UserTransactionPartitionScheme constants and fields contain
    expected values."""
    assert isinstance(partition_scheme, UserTransactionPartitionScheme)
    assert partition_scheme.approved_partition == expected_partition
    assert (
        partition_scheme.approved_partition == partition_scheme.get_approved_partition()
    )
    assert (
        command_line_name in TRANSACTION_PARTITION_SCHEMES
    ), f"Could not find {command_line_name} in {TRANSACTION_PARTITION_SCHEMES}"
    assert TRANSACTION_PARTITION_SCHEMES[command_line_name] is partition_scheme


def test_user_partition_scheme_does_not_accept_draft_as_approved_partition():
    """Verify that UserTransactionPartitionScheme get_partition return its
    approved_partition on being passed an approved workbasket."""
    with pytest.raises(ValueError):
        UserTransactionPartitionScheme(TransactionPartition.DRAFT, "test text")


@pytest.mark.parametrize(
    "transaction_factories",
    [
        (ApprovedTransactionFactory,),
        (SeedFileTransactionFactory, ApprovedTransactionFactory),
    ],
)
def test_user_partition_scheme_get_approved_partition_does_not_allow_seed_after_revision(
    transaction_factories: Iterable[TransactionFactory],
):
    """Verify that UserPartitionScheme won't allow a SEED transaction if there a
    REVISION transaction already exists (as this may effect global ordering)"""
    for factory in transaction_factories:
        factory.create()

    with pytest.raises(ValueError):
        SEED_ONLY.get_approved_partition()


@pytest.mark.parametrize(
    "transaction_factories",
    [
        (ApprovedTransactionFactory,),
        (SeedFileTransactionFactory, ApprovedTransactionFactory),
    ],
)
@pytest.mark.parametrize("status", WorkflowStatus.approved_statuses())
def test_user_partition_scheme_get_partition_does_not_allow_seed_after_revision(
    transaction_factories: Iterable[TransactionFactory],
    status: WorkflowStatus,
):
    """Verify that UserPartitionScheme won't allow a SEED transaction if there a
    REVISION transaction already exists (as this may effect global ordering)"""
    for factory in transaction_factories:
        factory.create()

    with pytest.raises(ValueError):
        SEED_ONLY.get_partition(status)


# FIXME synthetic-record-order:
#        Factories named here have fields containing TrackedModels, prior to TP-841 these would have each
#        been in their own transaction.
#        This hides an issue where synthetic fields (those generated by templates such as description) are
#        only relative to their own tracked_model, failing under certain circumstances, as exposed by
#        TP-841 aimed to unify a factories output under one transaction.
EXCLUDE_MULTI_TRANSACTION_FACTORIES = [
    "AdditionalCodeTypeMeasureTypeFactory",
    "AmendmentFactory",
    "ExtensionFactory",
    "FootnoteAssociationMeasureFactory",
    "GeographicalMembershipFactory",
    "MeasureComponentFactory",
    "MeasureConditionComponentFactory",
    "MeasureConditionFactory",
    "MeasureExcludedGeographicalAreaFactory",
    "MeasureFactory",
    "MeasurementFactory",
    "MeasureTypeFactory",
    "QuotaAssociationFactory",
    "QuotaBlockingFactory",
    "QuotaDefinitionFactory",
    "QuotaEventFactory",
    "QuotaOrderNumberFactory",
    "QuotaOrderNumberOriginExclusionFactory",
    "QuotaOrderNumberOriginFactory",
    "QuotaSuspensionFactory",
    "ReplacementFactory",
    "SuspensionFactory",
    "TerminationFactory",
]
FACTORIES = [
    factory
    for factory in factories.TrackedModelMixin.__subclasses__()
    if factory.__name__ not in EXCLUDE_MULTI_TRANSACTION_FACTORIES
]


@pytest.mark.parametrize(
    "factory",
    FACTORIES,
    ids=(f.__name__ for f in FACTORIES),
)
def test_nested_factories_dont_create_extra_transactions(factory):
    """
    To verify the seed_first transaction scheme it's important to have control
    over when transactions are created.

    If a TrackedModel is a field of another TrackedModels factory and it implicitly
    creates a Transaction this can break tests of the seed first scheme as it is
    no longer possible to know which transactions should be created.

    This test verifies calls each factory specifying a transaction and fails
    if new transactions were created.

    Factories that cause this test to fail should be updated to ensure
    transactions are passed to their SubFactories and RelatedFactories.
    """
    tx = TransactionFactory.create()

    # Verify the initial assumption that there is one transaction.
    assert [*Transaction.objects.all()] == [tx]

    factory.create(transaction=tx)
    assert [*Transaction.objects.all()] == [tx], (
        f"{factory} created more than one transaction,"
        " check that it passes its transaction to any tracked_models it creates."
    )


@pytest.mark.parametrize(
    "partition_setting,expected_partition",
    [
        ("workbaskets.models.REVISION_ONLY", TransactionPartition.REVISION),
        ("workbaskets.models.SEED_ONLY", TransactionPartition.SEED_FILE),
        ("workbaskets.models.SEED_FIRST", TransactionPartition.SEED_FILE),
    ],
)
def test_workbasket_approval_updates_transactions(
    settings,
    valid_user,
    partition_setting,
    expected_partition,
):
    """Verify that approving a PROPOSED workbasket moves its DRAFT transactions
    to SEED_FILE or REVISION as specified by the partition scheme, and that the
    transaction order is updated to start at the end of the specified
    partition."""
    # This test is good at finding issues with factories that implicitly create transactions
    # in the wrong order.
    settings.TRANSACTION_SCHEMA = partition_setting
    partition_scheme = get_partition_scheme()

    # Sanity check result of get_partition_scheme before continuing
    assert isinstance(partition_scheme, TransactionPartitionScheme)
    if isinstance(partition_scheme, UserTransactionPartitionScheme):
        assert partition_scheme.approved_partition == expected_partition

    new_workbasket = WorkBasketFactory.create(status=WorkflowStatus.PROPOSED)

    with new_workbasket.new_transaction() as tx:
        factories.FootnoteFactory.create(transaction=tx)

    # Before approving the workbasket check the ground truth that it contains some draft transactions.
    # assert new_workbasket.tracked_models.exists()
    assert [TransactionPartition.DRAFT] == list(
        new_workbasket.transactions.distinct("partition").values_list(
            "partition",
            flat=True,
        ),
    )
    with patch("exporter.tasks.upload_workbaskets") as upload:
        new_workbasket.approve(valid_user, partition_scheme)

        upload.delay.assert_called_with()

    assert [expected_partition] == list(
        new_workbasket.transactions.distinct("partition").values_list(
            "partition",
            flat=True,
        ),
    )

    assert_transaction_order(Transaction.objects.all())
