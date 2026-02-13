"""Tests for analytics API endpoints."""
import pytest
from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework import status

from apps.accounts.models import Account
from apps.accounts.tests.factories import AccountFactory, CollectorFactory
from apps.payments.tests.factories import PaymentFactory
from apps.payments.models import Payment


@pytest.mark.django_db
class TestDashboardAPI:
    def test_dashboard_returns_kpis(self, authenticated_admin_client, agency):
        AccountFactory.create_batch(5, agency=agency, status=Account.Status.NEW)
        AccountFactory.create_batch(3, agency=agency, status=Account.Status.SETTLED)

        response = authenticated_admin_client.get("/api/v1/analytics/dashboard/")
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert "total_accounts" in data
        assert "total_collected" in data
        assert "collection_rate" in data
        assert "accounts_by_status" in data
        assert data["total_accounts"] == 8

    def test_dashboard_collection_rate_accuracy(self, authenticated_admin_client, agency):
        """Verify collection rate = settled / total * 100."""
        AccountFactory.create_batch(7, agency=agency, status=Account.Status.NEW)
        AccountFactory.create_batch(3, agency=agency, status=Account.Status.SETTLED)

        response = authenticated_admin_client.get("/api/v1/analytics/dashboard/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["collection_rate"] == 30.0  # 3/10 * 100

    def test_dashboard_unauthenticated(self, api_client):
        response = api_client.get("/api/v1/analytics/dashboard/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_dashboard_total_collected_matches_payments(self, authenticated_admin_client, agency):
        """Aggregation consistency: total_collected should match sum of completed payments."""
        account = AccountFactory(agency=agency)
        PaymentFactory(account=account, amount=Decimal("500.00"), status=Payment.Status.COMPLETED)
        PaymentFactory(account=account, amount=Decimal("300.00"), status=Payment.Status.COMPLETED)
        PaymentFactory(account=account, amount=Decimal("200.00"), status=Payment.Status.FAILED)

        response = authenticated_admin_client.get("/api/v1/analytics/dashboard/")
        assert response.status_code == status.HTTP_200_OK
        assert Decimal(str(response.data["total_collected"])) == Decimal("800.00")


@pytest.mark.django_db
class TestCollectorPerformanceAPI:
    def test_collector_performance(self, authenticated_admin_client, agency):
        collector = CollectorFactory(agency=agency)
        AccountFactory.create_batch(3, agency=agency, assigned_to=collector, status=Account.Status.SETTLED)
        AccountFactory.create_batch(2, agency=agency, assigned_to=collector, status=Account.Status.NEW)

        response = authenticated_admin_client.get("/api/v1/analytics/collectors/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_collector_success_rate(self, authenticated_admin_client, agency):
        """Verify success_rate = settled / total * 100."""
        collector = CollectorFactory(agency=agency)
        AccountFactory.create_batch(4, agency=agency, assigned_to=collector, status=Account.Status.SETTLED)
        AccountFactory.create_batch(6, agency=agency, assigned_to=collector, status=Account.Status.NEW)

        response = authenticated_admin_client.get("/api/v1/analytics/collectors/")
        assert response.status_code == status.HTTP_200_OK
        perf = [r for r in response.data if str(r["collector_id"]) == str(collector.id)]
        assert len(perf) == 1
        assert perf[0]["success_rate"] == 40.0  # 4/10 * 100


@pytest.mark.django_db
class TestPaymentTrendsAPI:
    def test_payment_trends_by_day(self, authenticated_admin_client):
        now = timezone.now()
        for i in range(5):
            p = PaymentFactory(status=Payment.Status.COMPLETED)
            # auto_now_add prevents direct set, so use queryset update
            Payment.objects.filter(pk=p.pk).update(created_at=now - timedelta(days=i))

        response = authenticated_admin_client.get("/api/v1/analytics/payments/trends/?granularity=day&days=30")
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) > 0
        assert "period" in response.data[0]
        assert "total_amount" in response.data[0]
        assert "count" in response.data[0]

    def test_payment_trends_by_month(self, authenticated_admin_client):
        PaymentFactory(status=Payment.Status.COMPLETED)
        response = authenticated_admin_client.get("/api/v1/analytics/payments/trends/?granularity=month&days=90")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestAgingReportAPI:
    def test_aging_report(self, authenticated_admin_client, agency):
        AccountFactory(agency=agency, due_date=(timezone.now() - timedelta(days=15)).date(), status=Account.Status.NEW)
        AccountFactory(agency=agency, due_date=(timezone.now() - timedelta(days=45)).date(), status=Account.Status.ASSIGNED)
        AccountFactory(agency=agency, due_date=(timezone.now() - timedelta(days=100)).date(), status=Account.Status.IN_CONTACT)

        response = authenticated_admin_client.get("/api/v1/analytics/aging-report/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 4
        assert response.data[0]["bucket"] == "0-30 days"

    def test_aging_report_bucket_counts(self, authenticated_admin_client, agency):
        """Verify accounts are placed in correct aging buckets."""
        now = timezone.now()
        # 0-30 days bucket
        AccountFactory.create_batch(2, agency=agency, due_date=(now - timedelta(days=10)).date(), status=Account.Status.NEW)
        # 31-60 days bucket
        AccountFactory(agency=agency, due_date=(now - timedelta(days=40)).date(), status=Account.Status.ASSIGNED)
        # 90+ days bucket
        AccountFactory(agency=agency, due_date=(now - timedelta(days=120)).date(), status=Account.Status.IN_CONTACT)

        response = authenticated_admin_client.get("/api/v1/analytics/aging-report/")
        assert response.status_code == status.HTTP_200_OK
        buckets = {b["bucket"]: b["count"] for b in response.data}
        assert buckets["0-30 days"] == 2
        assert buckets["31-60 days"] == 1
        assert buckets["90+ days"] == 1
