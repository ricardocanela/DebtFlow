#!/usr/bin/env python
"""Generate fake seed data for local development."""
import os
import sys
from decimal import Decimal
from pathlib import Path

import django

# Setup Django
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.contrib.auth.models import Group, User  # noqa: E402

from apps.accounts.models import Account, Activity, Agency, Collector, Debtor  # noqa: E402
from apps.payments.models import Payment, PaymentProcessor  # noqa: E402

try:
    from faker import Faker
except ImportError:
    print("Please install faker: pip install faker")
    sys.exit(1)

fake = Faker()


def create_groups():
    print("Creating groups...")
    Group.objects.get_or_create(name="agency_admin")
    Group.objects.get_or_create(name="collector")
    Group.objects.get_or_create(name="readonly")


def create_agencies(count=3):
    print(f"Creating {count} agencies...")
    agencies = []
    for i in range(count):
        agency, _ = Agency.objects.get_or_create(
            name=f"{fake.company()} Collections",
            defaults={"license_number": f"LIC-{fake.numerify('######')}", "is_active": True},
        )
        agencies.append(agency)
    return agencies


def create_users_and_collectors(agencies):
    print("Creating users and collectors...")
    admin_group = Group.objects.get(name="agency_admin")
    collector_group = Group.objects.get(name="collector")

    # Create admin for each agency
    for agency in agencies:
        admin_user, created = User.objects.get_or_create(
            username=f"admin_{agency.name[:10].lower().replace(' ', '_')}",
            defaults={
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": fake.email(),
                "is_staff": True,
            },
        )
        if created:
            admin_user.set_password("testpass123")
            admin_user.save()
            admin_user.groups.add(admin_group)
            Collector.objects.get_or_create(user=admin_user, agency=agency)

        # Create 3 collectors per agency
        for j in range(3):
            coll_user, created = User.objects.get_or_create(
                username=f"collector_{agency.name[:5].lower().replace(' ', '_')}_{j}",
                defaults={
                    "first_name": fake.first_name(),
                    "last_name": fake.last_name(),
                    "email": fake.email(),
                },
            )
            if created:
                coll_user.set_password("testpass123")
                coll_user.save()
                coll_user.groups.add(collector_group)
                Collector.objects.get_or_create(
                    user=coll_user,
                    agency=agency,
                    defaults={"commission_rate": Decimal(f"0.{fake.random_int(min=8, max=15):02d}")},
                )


def create_debtors(count=500):
    print(f"Creating {count} debtors...")
    debtors = []
    for i in range(count):
        debtor, _ = Debtor.objects.get_or_create(
            external_ref=f"DBT-{i:06d}",
            defaults={
                "full_name": fake.name(),
                "ssn_last4": fake.numerify("####"),
                "email": fake.email(),
                "phone": fake.phone_number()[:20],
                "address_line1": fake.street_address(),
                "address_city": fake.city(),
                "address_state": fake.state_abbr(),
                "address_zip": fake.zipcode(),
            },
        )
        debtors.append(debtor)
    return debtors


def create_accounts(agencies, debtors, count=1000):
    print(f"Creating {count} accounts...")
    collectors = list(Collector.objects.filter(is_active=True))
    statuses = [Account.Status.NEW, Account.Status.ASSIGNED, Account.Status.IN_CONTACT, Account.Status.NEGOTIATING, Account.Status.SETTLED]

    for i in range(count):
        agency = fake.random_element(agencies)
        debtor = fake.random_element(debtors)
        status = fake.random_element(statuses)
        amount = Decimal(str(fake.random_int(min=100, max=50000)))
        balance = amount if status != Account.Status.SETTLED else Decimal("0")

        agency_collectors = [c for c in collectors if c.agency_id == agency.id]
        assigned_to = fake.random_element(agency_collectors) if agency_collectors and status != Account.Status.NEW else None

        Account.objects.get_or_create(
            external_ref=f"ACC-{i:06d}",
            defaults={
                "agency": agency,
                "debtor": debtor,
                "assigned_to": assigned_to,
                "original_amount": amount,
                "current_balance": balance,
                "status": status,
                "priority": fake.random_int(min=0, max=10),
                "due_date": fake.date_between(start_date="-2y", end_date="-1m"),
            },
        )


def create_payment_processor():
    print("Creating payment processor...")
    processor, _ = PaymentProcessor.objects.get_or_create(
        slug="stripe",
        defaults={
            "name": "Stripe",
            "api_base_url": "https://api.stripe.com",
            "api_key_encrypted": "encrypted_sk_test_key",
            "webhook_secret": "whsec_test_secret",
            "is_active": True,
        },
    )
    return processor


def create_superuser():
    print("Creating superuser...")
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@debtflow.local", "admin123")
        print("  Superuser created: admin / admin123")


def main():
    print("=" * 50)
    print("DebtFlow — Seed Data Generator")
    print("=" * 50)

    create_groups()
    create_superuser()
    agencies = create_agencies()
    create_users_and_collectors(agencies)
    debtors = create_debtors()
    create_accounts(agencies, debtors)
    create_payment_processor()

    print()
    print("Seed data created successfully!")
    print(f"  Agencies: {Agency.objects.count()}")
    print(f"  Users: {User.objects.count()}")
    print(f"  Collectors: {Collector.objects.count()}")
    print(f"  Debtors: {Debtor.objects.count()}")
    print(f"  Accounts: {Account.objects.count()}")
    print(f"  Payment Processors: {PaymentProcessor.objects.count()}")


if __name__ == "__main__":
    main()
