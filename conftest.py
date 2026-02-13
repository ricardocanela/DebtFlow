"""Root pytest conftest — shared fixtures for all tests."""
import pytest
from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient

from apps.accounts.models import Agency, Collector


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def agency(db):
    return Agency.objects.create(name="Test Agency", license_number="LIC-001")


@pytest.fixture
def agency_admin_group(db):
    group, _ = Group.objects.get_or_create(name="agency_admin")
    return group


@pytest.fixture
def collector_group(db):
    group, _ = Group.objects.get_or_create(name="collector")
    return group


@pytest.fixture
def admin_user(db, agency, agency_admin_group):
    user = User.objects.create_user(
        username="admin",
        password="testpass123",
        first_name="Admin",
        last_name="User",
        email="admin@test.com",
    )
    user.groups.add(agency_admin_group)
    Collector.objects.create(user=user, agency=agency)
    return user


@pytest.fixture
def collector_user(db, agency, collector_group):
    user = User.objects.create_user(
        username="collector1",
        password="testpass123",
        first_name="John",
        last_name="Collector",
        email="collector@test.com",
    )
    user.groups.add(collector_group)
    Collector.objects.create(user=user, agency=agency)
    return user


@pytest.fixture
def authenticated_admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def authenticated_collector_client(api_client, collector_user):
    api_client.force_authenticate(user=collector_user)
    return api_client
