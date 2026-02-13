"""Tests for audit middleware and automatic audit logging via signals."""
import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory

from apps.accounts.models import Account, Agency
from apps.accounts.tests.factories import AccountFactory, AgencyFactory, DebtorFactory
from apps.audit.middleware import AuditLogMiddleware, get_audit_ip, get_audit_user
from apps.audit.models import AuditLog


@pytest.mark.django_db
class TestAuditLogMiddleware:
    def test_middleware_stores_user_in_thread_local(self):
        user = User.objects.create_user(username="audit_test", password="pass")
        factory = RequestFactory()
        request = factory.get("/api/v1/accounts/")
        request.user = user

        middleware = AuditLogMiddleware(lambda r: r)
        # During the middleware call, thread-local should have user
        def check_and_respond(req):
            assert get_audit_user() == user
            assert get_audit_ip() is not None
            return req

        middleware = AuditLogMiddleware(check_and_respond)
        middleware(request)

        # After middleware completes, thread-local should be cleaned up
        assert get_audit_user() is None
        assert get_audit_ip() is None

    def test_middleware_extracts_ip_from_remote_addr(self):
        factory = RequestFactory()
        request = factory.get("/", REMOTE_ADDR="192.168.1.100")
        request.user = User.objects.create_user(username="ip_test", password="pass")

        captured_ip = None

        def capture_ip(req):
            nonlocal captured_ip
            captured_ip = get_audit_ip()
            return req

        middleware = AuditLogMiddleware(capture_ip)
        middleware(request)
        assert captured_ip == "192.168.1.100"

    def test_middleware_extracts_ip_from_x_forwarded_for(self):
        factory = RequestFactory()
        request = factory.get("/", HTTP_X_FORWARDED_FOR="10.0.0.1, 10.0.0.2", REMOTE_ADDR="192.168.1.1")
        request.user = User.objects.create_user(username="xff_test", password="pass")

        captured_ip = None

        def capture_ip(req):
            nonlocal captured_ip
            captured_ip = get_audit_ip()
            return req

        middleware = AuditLogMiddleware(capture_ip)
        middleware(request)
        assert captured_ip == "10.0.0.1"


@pytest.mark.django_db
class TestAuditSignals:
    """Test that model save/delete triggers audit log entries via signals."""

    def test_create_agency_creates_audit_log(self):
        agency = Agency.objects.create(name="Signal Test Agency")
        log = AuditLog.objects.filter(object_id=agency.pk, action="create").first()
        assert log is not None
        assert log.action == "create"

    def test_update_agency_creates_audit_log(self):
        agency = Agency.objects.create(name="Before Update")
        AuditLog.objects.all().delete()  # Clear create log

        agency.name = "After Update"
        agency.save()

        log = AuditLog.objects.filter(object_id=agency.pk, action="update").first()
        assert log is not None
        assert "name" in log.changes
        assert log.changes["name"]["old"] == "Before Update"
        assert log.changes["name"]["new"] == "After Update"

    def test_delete_agency_creates_audit_log(self):
        agency = Agency.objects.create(name="To Delete")
        agency_pk = agency.pk
        agency.delete()

        log = AuditLog.objects.filter(object_id=agency_pk, action="delete").first()
        assert log is not None
        assert "deleted" in log.changes

    def test_account_changes_audited(self):
        account = AccountFactory()
        log = AuditLog.objects.filter(object_id=account.pk, action="create").first()
        assert log is not None

    def test_non_audited_model_not_logged(self):
        """Models not in AUDITED_MODELS should not generate audit logs."""
        initial_count = AuditLog.objects.count()
        User.objects.create_user(username="no_audit", password="pass")
        assert AuditLog.objects.count() == initial_count
