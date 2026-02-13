"""Integration tests for accounts API endpoints."""
import pytest
from django.contrib.auth.models import Group
from rest_framework import status

from apps.accounts.models import Account

from .factories import AccountFactory, CollectorFactory, DebtorFactory


@pytest.mark.django_db
class TestAccountListAPI:
    def test_list_accounts_authenticated(self, authenticated_admin_client, agency):
        AccountFactory.create_batch(5, agency=agency)
        response = authenticated_admin_client.get("/api/v1/accounts/")
        assert response.status_code == status.HTTP_200_OK

    def test_list_accounts_unauthenticated(self, api_client):
        response = api_client.get("/api/v1/accounts/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_filter_by_status(self, authenticated_admin_client, agency):
        AccountFactory.create_batch(3, agency=agency, status=Account.Status.NEW)
        AccountFactory.create_batch(2, agency=agency, status=Account.Status.SETTLED)
        response = authenticated_admin_client.get("/api/v1/accounts/?status=new")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestAccountDetailAPI:
    def test_retrieve_account(self, authenticated_admin_client, agency):
        account = AccountFactory(agency=agency)
        response = authenticated_admin_client.get(f"/api/v1/accounts/{account.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["external_ref"] == account.external_ref


@pytest.mark.django_db
class TestAccountCreateAPI:
    def test_create_account_as_admin(self, authenticated_admin_client, agency):
        debtor = DebtorFactory()
        data = {
            "agency": str(agency.id),
            "debtor": str(debtor.id),
            "external_ref": "NEW-ACC-001",
            "original_amount": "1500.00",
            "current_balance": "1500.00",
        }
        response = authenticated_admin_client.post("/api/v1/accounts/", data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_account_as_collector_denied(self, authenticated_collector_client):
        debtor = DebtorFactory()
        data = {
            "external_ref": "NEW-ACC-002",
            "debtor": str(debtor.id),
            "original_amount": "1000.00",
        }
        response = authenticated_collector_client.post("/api/v1/accounts/", data)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestAccountAssignAPI:
    def test_assign_account(self, authenticated_admin_client, agency):
        account = AccountFactory(agency=agency, status=Account.Status.NEW)
        collector = CollectorFactory(agency=agency)
        response = authenticated_admin_client.post(
            f"/api/v1/accounts/{account.id}/assign/",
            {"collector_id": str(collector.id)},
        )
        assert response.status_code == status.HTTP_200_OK
        account.refresh_from_db()
        assert account.assigned_to == collector
        assert account.status == Account.Status.ASSIGNED


@pytest.mark.django_db
class TestAccountTransitionAPI:
    def test_valid_transition(self, authenticated_admin_client, agency):
        account = AccountFactory(agency=agency, status=Account.Status.NEW)
        response = authenticated_admin_client.post(
            f"/api/v1/accounts/{account.id}/transition/",
            {"new_status": "assigned", "note": "Ready for collection"},
        )
        assert response.status_code == status.HTTP_200_OK
        account.refresh_from_db()
        assert account.status == Account.Status.ASSIGNED

    def test_invalid_transition(self, authenticated_admin_client, agency):
        account = AccountFactory(agency=agency, status=Account.Status.NEW)
        response = authenticated_admin_client.post(
            f"/api/v1/accounts/{account.id}/transition/",
            {"new_status": "settled"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestAccountAddNoteAPI:
    def test_add_note(self, authenticated_admin_client, agency):
        account = AccountFactory(agency=agency)
        response = authenticated_admin_client.post(
            f"/api/v1/accounts/{account.id}/add-note/",
            {"text": "Called debtor, left voicemail"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["activity_type"] == "note"


@pytest.mark.django_db
class TestAccountTimelineAPI:
    def test_timeline(self, authenticated_admin_client, agency):
        account = AccountFactory(agency=agency)
        # Create some activities via service
        from apps.accounts.services import AccountService
        from .factories import UserFactory

        user = UserFactory()
        AccountService.add_note(account, user, "Note 1")
        AccountService.add_note(account, user, "Note 2")

        response = authenticated_admin_client.get(f"/api/v1/accounts/{account.id}/timeline/")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestCollectorCrossAgencyAccess:
    """Verify collectors cannot access accounts from another agency."""

    def test_collector_cannot_see_other_agency_accounts(self, db):
        from django.contrib.auth.models import Group
        from rest_framework.test import APIClient

        # Create two agencies
        from .factories import AgencyFactory, AccountFactory, CollectorFactory, UserFactory

        agency_a = AgencyFactory(name="Agency A")
        agency_b = AgencyFactory(name="Agency B")

        # Create collector in agency A
        collector_group, _ = Group.objects.get_or_create(name="collector")
        user = UserFactory()
        user.groups.add(collector_group)
        collector = CollectorFactory(user=user, agency=agency_a)

        # Create accounts in both agencies
        account_a = AccountFactory(agency=agency_a, assigned_to=collector)
        account_b = AccountFactory(agency=agency_b)

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/v1/accounts/")
        assert response.status_code == status.HTTP_200_OK

        # Collector should only see their own agency's assigned accounts
        account_ids = [r["id"] for r in response.data.get("results", response.data) if isinstance(r, dict)]
        assert str(account_b.id) not in account_ids
