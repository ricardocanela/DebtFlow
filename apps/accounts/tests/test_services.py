"""Tests for account business logic services."""
import pytest

from apps.accounts.models import Account, Activity
from apps.accounts.services import AccountService

from .factories import AccountFactory, CollectorFactory, UserFactory


@pytest.mark.django_db
class TestAccountServiceAssign:
    def test_assign_account(self):
        account = AccountFactory(status=Account.Status.NEW)
        collector = CollectorFactory(agency=account.agency)
        user = UserFactory()

        result = AccountService.assign_account(account, collector, user)

        assert result.assigned_to == collector
        assert result.status == Account.Status.ASSIGNED
        assert Activity.objects.filter(
            account=account, activity_type=Activity.ActivityType.ASSIGNMENT
        ).exists()

    def test_reassign_account(self):
        collector1 = CollectorFactory()
        collector2 = CollectorFactory(agency=collector1.agency)
        account = AccountFactory(
            agency=collector1.agency,
            assigned_to=collector1,
            status=Account.Status.ASSIGNED,
        )
        user = UserFactory()

        result = AccountService.assign_account(account, collector2, user)

        assert result.assigned_to == collector2
        activity = Activity.objects.filter(account=account, activity_type=Activity.ActivityType.ASSIGNMENT).last()
        assert str(collector1.id) in str(activity.metadata["old_collector_id"])


@pytest.mark.django_db
class TestAccountServiceTransition:
    def test_valid_transition(self):
        account = AccountFactory(status=Account.Status.NEW)
        user = UserFactory()

        result = AccountService.transition_status(account, Account.Status.ASSIGNED, user, note="Test transition")

        assert result.status == Account.Status.ASSIGNED
        activity = Activity.objects.filter(
            account=account, activity_type=Activity.ActivityType.STATUS_CHANGE
        ).last()
        assert "new" in activity.metadata["old_status"]
        assert "assigned" in activity.metadata["new_status"]

    def test_invalid_transition_raises(self):
        account = AccountFactory(status=Account.Status.NEW)
        user = UserFactory()

        with pytest.raises(ValueError, match="Invalid transition"):
            AccountService.transition_status(account, Account.Status.SETTLED, user)

    def test_transition_creates_activity(self):
        account = AccountFactory(status=Account.Status.ASSIGNED)
        user = UserFactory()

        AccountService.transition_status(account, Account.Status.IN_CONTACT, user)

        assert Activity.objects.filter(
            account=account, activity_type=Activity.ActivityType.STATUS_CHANGE
        ).count() == 1


@pytest.mark.django_db
class TestAccountServiceAddNote:
    def test_add_note(self):
        account = AccountFactory()
        user = UserFactory()

        activity = AccountService.add_note(account, user, "Called debtor, no answer")

        assert activity.activity_type == Activity.ActivityType.NOTE
        assert activity.description == "Called debtor, no answer"
        account.refresh_from_db()
        assert account.last_contact_at is not None
