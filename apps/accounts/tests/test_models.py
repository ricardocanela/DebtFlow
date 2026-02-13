"""Tests for accounts models."""
import pytest

from apps.accounts.models import Account

from .factories import AccountFactory, AgencyFactory, CollectorFactory, DebtorFactory


@pytest.mark.django_db
class TestAgency:
    def test_create_agency(self):
        agency = AgencyFactory()
        assert agency.name
        assert agency.is_active is True
        assert str(agency) == agency.name

    def test_agency_unique_name(self):
        AgencyFactory(name="Unique Agency")
        with pytest.raises(Exception):
            AgencyFactory(name="Unique Agency")


@pytest.mark.django_db
class TestDebtor:
    def test_create_debtor(self):
        debtor = DebtorFactory()
        assert debtor.external_ref
        assert debtor.full_name
        assert str(debtor) == f"{debtor.full_name} ({debtor.external_ref})"

    def test_debtor_unique_external_ref(self):
        DebtorFactory(external_ref="REF-001")
        with pytest.raises(Exception):
            DebtorFactory(external_ref="REF-001")


@pytest.mark.django_db
class TestAccount:
    def test_create_account(self):
        account = AccountFactory()
        assert account.status == Account.Status.NEW
        assert account.current_balance == account.original_amount

    def test_valid_transitions_from_new(self):
        account = AccountFactory(status=Account.Status.NEW)
        assert account.can_transition_to(Account.Status.ASSIGNED) is True
        assert account.can_transition_to(Account.Status.CLOSED) is True
        assert account.can_transition_to(Account.Status.SETTLED) is False
        assert account.can_transition_to(Account.Status.NEGOTIATING) is False

    def test_valid_transitions_from_assigned(self):
        account = AccountFactory(status=Account.Status.ASSIGNED)
        assert account.can_transition_to(Account.Status.IN_CONTACT) is True
        assert account.can_transition_to(Account.Status.CLOSED) is True
        assert account.can_transition_to(Account.Status.DISPUTED) is True
        assert account.can_transition_to(Account.Status.NEW) is False

    def test_valid_transitions_from_negotiating(self):
        account = AccountFactory(status=Account.Status.NEGOTIATING)
        assert account.can_transition_to(Account.Status.PAYMENT_PLAN) is True
        assert account.can_transition_to(Account.Status.SETTLED) is True
        assert account.can_transition_to(Account.Status.CLOSED) is True
        assert account.can_transition_to(Account.Status.NEW) is False

    def test_closed_has_no_transitions(self):
        account = AccountFactory(status=Account.Status.CLOSED)
        for s in Account.Status:
            assert account.can_transition_to(s) is False

    def test_str_representation(self):
        account = AccountFactory(external_ref="ACC-999", status=Account.Status.NEW)
        assert "ACC-999" in str(account)


@pytest.mark.django_db
class TestCollector:
    def test_create_collector(self):
        collector = CollectorFactory()
        assert collector.user
        assert collector.agency
        assert str(collector.agency.name) in str(collector)
