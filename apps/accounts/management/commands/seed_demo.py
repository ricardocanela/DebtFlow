"""Populate the database with realistic demo data for DebtFlow."""
import hashlib
import random
import uuid
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import Account, Activity, Agency, Collector, Debtor
from apps.integrations.models import SFTPImportJob
from apps.payments.models import Payment, PaymentProcessor

# ---------------------------------------------------------------------------
# Realistic data pools
# ---------------------------------------------------------------------------

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
    "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Christopher", "Karen",
    "Charles", "Lisa", "Daniel", "Nancy", "Matthew", "Betty", "Anthony",
    "Margaret", "Mark", "Sandra", "Donald", "Ashley", "Steven", "Kimberly",
    "Andrew", "Emily", "Paul", "Donna", "Joshua", "Michelle", "Kenneth",
    "Carol", "Kevin", "Amanda", "Brian", "Dorothy", "George", "Melissa",
    "Timothy", "Deborah",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts",
]

STREETS = [
    "Main St", "Oak Ave", "Elm St", "Park Blvd", "Cedar Ln",
    "Maple Dr", "Pine St", "Washington Ave", "Lake Rd", "River Dr",
    "Highland Ave", "Sunset Blvd", "Broadway", "Market St", "Church St",
    "Walnut St", "Spring St", "Forest Dr", "Meadow Ln", "Valley Rd",
]

CITIES_STATES = [
    ("New York", "NY", "10001"), ("Los Angeles", "CA", "90001"),
    ("Chicago", "IL", "60601"), ("Houston", "TX", "77001"),
    ("Phoenix", "AZ", "85001"), ("Philadelphia", "PA", "19101"),
    ("San Antonio", "TX", "78201"), ("San Diego", "CA", "92101"),
    ("Dallas", "TX", "75201"), ("Austin", "TX", "73301"),
    ("Jacksonville", "FL", "32099"), ("San Jose", "CA", "95101"),
    ("Columbus", "OH", "43085"), ("Charlotte", "NC", "28201"),
    ("Indianapolis", "IN", "46201"), ("Denver", "CO", "80201"),
    ("Seattle", "WA", "98101"), ("Nashville", "TN", "37201"),
    ("Portland", "OR", "97201"), ("Las Vegas", "NV", "89101"),
    ("Miami", "FL", "33101"), ("Atlanta", "GA", "30301"),
    ("Tampa", "FL", "33601"), ("Orlando", "FL", "32801"),
    ("Minneapolis", "MN", "55401"), ("Cleveland", "OH", "44101"),
    ("Raleigh", "NC", "27601"), ("Salt Lake City", "UT", "84101"),
    ("Richmond", "VA", "23218"), ("Birmingham", "AL", "35201"),
]

NOTE_TEMPLATES = [
    "Left voicemail requesting callback regarding outstanding balance.",
    "Spoke with debtor. They acknowledged the debt and requested payment options.",
    "Sent follow-up email with payment plan details.",
    "Debtor requested 30-day extension. Approved per agency policy.",
    "Called debtor — no answer. Will retry in 48 hours.",
    "Debtor agreed to monthly payment plan of ${amount}/mo starting next month.",
    "Received partial payment. Updated balance accordingly.",
    "Debtor disputes the amount. Requested validation letter be sent.",
    "Sent debt validation letter via certified mail.",
    "Debtor confirmed receipt of validation letter. Proceeding with collection.",
    "Debtor's employer confirmed employment status for wage garnishment assessment.",
    "Negotiated settlement at {pct}% of original balance. Awaiting payment.",
    "Debtor requested hardship review. Documentation submitted.",
    "Skip trace completed — updated phone number and address on file.",
    "Debtor moved to new address. Updated records from skip trace.",
    "Payment arrangement confirmed. First payment due on the 15th.",
    "Account reviewed for compliance. All documentation in order.",
    "Debtor called to discuss payment options. Provided 3 plan options.",
    "Second notice sent. Account approaching escalation threshold.",
    "Successful contact — debtor committed to resolving balance within 60 days.",
]

IMPORT_FILES = [
    "client_accounts_batch_2026Q1.csv",
    "new_placements_january_2026.csv",
    "monthly_update_feb_2026.csv",
    "portfolio_transfer_ABC_corp.csv",
    "supplemental_data_march_2026.csv",
    "quarterly_refresh_Q1_2026.csv",
]

COLLECTOR_DATA = [
    ("sarah.mitchell", "Sarah", "Mitchell", 0.12),
    ("james.carter", "James", "Carter", 0.10),
    ("maria.gonzalez", "Maria", "Gonzalez", 0.11),
    ("david.thompson", "David", "Thompson", 0.10),
]


class Command(BaseCommand):
    help = "Seed the database with realistic demo data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing demo data before seeding",
        )

    def handle(self, *args, **options):
        now = timezone.now()

        if options["clear"]:
            self.stdout.write("Clearing existing data...")
            Payment.objects.all().delete()
            Activity.objects.all().delete()
            Account.objects.all().delete()
            SFTPImportJob.objects.all().delete()
            Debtor.objects.all().delete()
            Collector.objects.all().delete()
            Agency.objects.filter(name="Apex Recovery Solutions").delete()
            PaymentProcessor.objects.filter(slug="stripe").delete()
            User.objects.filter(username__in=[
                "demo.admin", *[c[0] for c in COLLECTOR_DATA]
            ]).delete()
            self.stdout.write(self.style.SUCCESS("Cleared."))

        # ----- 1. Agency -----
        agency, _ = Agency.objects.get_or_create(
            name="Apex Recovery Solutions",
            defaults={
                "license_number": "DCA-2024-08812",
                "settings": {
                    "timezone": "America/New_York",
                    "currency": "USD",
                    "auto_assign": True,
                    "max_contact_attempts": 5,
                    "escalation_days": 45,
                },
            },
        )
        self.stdout.write(f"Agency: {agency.name}")

        # ----- 2. Demo admin user -----
        demo_user, created = User.objects.get_or_create(
            username="demo.admin",
            defaults={
                "email": "demo@apexrecovery.com",
                "first_name": "Demo",
                "last_name": "Admin",
                "is_staff": True,
            },
        )
        if created:
            demo_user.set_password("Demo@2026")
            demo_user.save()
        self.stdout.write(f"Demo admin: demo.admin / Demo@2026")

        # ----- 3. Payment processor -----
        processor, _ = PaymentProcessor.objects.get_or_create(
            slug="stripe",
            defaults={
                "name": "Stripe",
                "api_base_url": "https://api.stripe.com/v1",
                "api_key_encrypted": "encrypted_sk_test_placeholder",
                "webhook_secret": "encrypted_whsec_placeholder",
            },
        )

        # ----- 4. Collectors -----
        collectors = []
        for username, first, last, rate in COLLECTOR_DATA:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": f"{username}@apexrecovery.com",
                    "first_name": first,
                    "last_name": last,
                },
            )
            if created:
                user.set_password("Collector@2026")
                user.save()
            collector, _ = Collector.objects.get_or_create(
                user=user,
                defaults={
                    "agency": agency,
                    "commission_rate": Decimal(str(rate)),
                    "max_accounts": 200,
                },
            )
            collectors.append(collector)
        self.stdout.write(f"Collectors: {len(collectors)} created")

        # ----- 5. Debtors -----
        used_names = set()
        debtors = []
        for i in range(85):
            while True:
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
                full = f"{first} {last}"
                if full not in used_names:
                    used_names.add(full)
                    break

            city, state, zipcode = random.choice(CITIES_STATES)
            debtor = Debtor(
                external_ref=f"DBT-{10000 + i}",
                full_name=full,
                ssn_last4=f"{random.randint(1000, 9999)}",
                email=f"{first.lower()}.{last.lower()}@{'gmail.com' if random.random() > 0.4 else 'yahoo.com'}",
                phone=f"+1{random.randint(200, 999)}{random.randint(1000000, 9999999)}",
                address_line1=f"{random.randint(100, 9999)} {random.choice(STREETS)}",
                address_city=city,
                address_state=state,
                address_zip=zipcode,
            )
            debtors.append(debtor)
        Debtor.objects.bulk_create(debtors, ignore_conflicts=True)
        debtors = list(Debtor.objects.filter(external_ref__startswith="DBT-1"))
        self.stdout.write(f"Debtors: {len(debtors)} created")

        # ----- 6. Accounts with realistic distribution -----
        # Status distribution: mirrors a real agency portfolio
        status_weights = [
            (Account.Status.NEW, 8),
            (Account.Status.ASSIGNED, 12),
            (Account.Status.IN_CONTACT, 18),
            (Account.Status.NEGOTIATING, 15),
            (Account.Status.PAYMENT_PLAN, 20),
            (Account.Status.SETTLED, 12),
            (Account.Status.CLOSED, 10),
            (Account.Status.DISPUTED, 5),
        ]
        statuses = []
        for status, weight in status_weights:
            statuses.extend([status] * weight)

        accounts = []
        for i, debtor in enumerate(debtors):
            status = random.choice(statuses)
            original = Decimal(str(random.randint(500, 25000))) + Decimal(
                str(random.randint(0, 99))
            ) / 100

            # Current balance depends on status
            if status == Account.Status.SETTLED:
                current = Decimal("0.00")
            elif status == Account.Status.CLOSED:
                current = Decimal("0.00") if random.random() > 0.3 else original
            elif status in (Account.Status.PAYMENT_PLAN, Account.Status.NEGOTIATING):
                pct = Decimal(str(random.uniform(0.2, 0.85)))
                current = (original * pct).quantize(Decimal("0.01"))
            else:
                current = original

            # Assign collector for non-new statuses
            assigned = None
            if status not in (Account.Status.NEW, Account.Status.CLOSED):
                assigned = random.choice(collectors)

            days_ago = random.randint(5, 180)
            last_contact = None
            if status not in (Account.Status.NEW,):
                last_contact = now - timedelta(
                    days=random.randint(0, min(days_ago, 30))
                )

            due_date = (now - timedelta(days=days_ago - random.randint(-30, 60))).date()

            accounts.append(
                Account(
                    agency=agency,
                    debtor=debtor,
                    assigned_to=assigned,
                    external_ref=f"ACC-{20000 + i}",
                    original_amount=original,
                    current_balance=current,
                    status=status,
                    priority=random.choices(
                        [0, 1, 2, 3], weights=[20, 40, 30, 10]
                    )[0],
                    due_date=due_date,
                    last_contact_at=last_contact,
                )
            )
        Account.objects.bulk_create(accounts, ignore_conflicts=True)
        accounts = list(
            Account.objects.filter(external_ref__startswith="ACC-2").select_related(
                "assigned_to", "debtor"
            )
        )
        self.stdout.write(f"Accounts: {len(accounts)} created")

        # ----- 7. Activities -----
        activities = []
        for acct in accounts:
            if acct.status == Account.Status.NEW:
                # New accounts: just an import activity
                activities.append(
                    Activity(
                        account=acct,
                        activity_type=Activity.ActivityType.IMPORT,
                        description=f"Account imported from SFTP file. Original amount: ${acct.original_amount}",
                        metadata={"source": "sftp", "file": "client_accounts_batch_2026Q1.csv"},
                    )
                )
                continue

            # Import activity (oldest)
            activities.append(
                Activity(
                    account=acct,
                    activity_type=Activity.ActivityType.IMPORT,
                    description=f"Account imported from SFTP file. Original amount: ${acct.original_amount}",
                    metadata={"source": "sftp"},
                )
            )

            # Assignment activity
            if acct.assigned_to:
                collector_name = acct.assigned_to.user.get_full_name()
                activities.append(
                    Activity(
                        account=acct,
                        user=acct.assigned_to.user,
                        activity_type=Activity.ActivityType.ASSIGNMENT,
                        description=f"Account assigned to {collector_name}.",
                    )
                )

            # Status change activities
            if acct.status in (
                Account.Status.IN_CONTACT,
                Account.Status.NEGOTIATING,
                Account.Status.PAYMENT_PLAN,
                Account.Status.SETTLED,
            ):
                activities.append(
                    Activity(
                        account=acct,
                        user=acct.assigned_to.user if acct.assigned_to else None,
                        activity_type=Activity.ActivityType.STATUS_CHANGE,
                        description=f"Status changed to {acct.get_status_display()}.",
                        metadata={"new_status": acct.status},
                    )
                )

            # Notes (1-4 per active account)
            num_notes = random.randint(1, 4)
            for _ in range(num_notes):
                note = random.choice(NOTE_TEMPLATES)
                note = note.replace("${amount}", str(random.randint(100, 500)))
                note = note.replace("{pct}", str(random.randint(40, 75)))
                activities.append(
                    Activity(
                        account=acct,
                        user=acct.assigned_to.user if acct.assigned_to else demo_user,
                        activity_type=Activity.ActivityType.NOTE,
                        description=note,
                    )
                )

            # Payment activities for settled/payment_plan accounts
            if acct.status in (Account.Status.SETTLED, Account.Status.PAYMENT_PLAN):
                paid = acct.original_amount - acct.current_balance
                if paid > 0:
                    activities.append(
                        Activity(
                            account=acct,
                            activity_type=Activity.ActivityType.PAYMENT,
                            description=f"Payment of ${paid} received and applied to balance.",
                        )
                    )

        Activity.objects.bulk_create(activities, ignore_conflicts=True)
        self.stdout.write(f"Activities: {len(activities)} created")

        # ----- 8. Payments -----
        payments = []
        payment_methods = [
            Payment.Method.CARD,
            Payment.Method.BANK_TRANSFER,
            Payment.Method.CHECK,
        ]
        for acct in accounts:
            if acct.status not in (
                Account.Status.PAYMENT_PLAN,
                Account.Status.SETTLED,
                Account.Status.NEGOTIATING,
            ):
                continue

            paid_total = acct.original_amount - acct.current_balance
            if paid_total <= 0:
                continue

            # Split into 1-5 payments
            num_payments = random.randint(1, min(5, max(1, int(paid_total / 100))))
            remaining = paid_total
            for j in range(num_payments):
                if j == num_payments - 1:
                    amount = remaining
                else:
                    amount = (paid_total / num_payments).quantize(Decimal("0.01"))
                    remaining -= amount

                if amount <= 0:
                    continue

                days_ago = random.randint(1, 90)
                idem_key = hashlib.sha256(
                    f"{acct.id}:{amount}:{j}:{uuid.uuid4()}".encode()
                ).hexdigest()

                payments.append(
                    Payment(
                        account=acct,
                        processor=processor,
                        amount=amount,
                        payment_method=random.choice(payment_methods),
                        status=Payment.Status.COMPLETED,
                        processor_ref=f"pi_{uuid.uuid4().hex[:24]}",
                        idempotency_key=idem_key,
                        metadata={
                            "stripe_payment_intent": f"pi_{uuid.uuid4().hex[:24]}",
                            "last4": f"{random.randint(1000, 9999)}",
                        },
                    )
                )

        # Add a few pending/failed payments for realism
        active_accounts = [
            a for a in accounts if a.status in (
                Account.Status.IN_CONTACT,
                Account.Status.NEGOTIATING,
                Account.Status.PAYMENT_PLAN,
            )
        ]
        for acct in random.sample(active_accounts, min(5, len(active_accounts))):
            amount = Decimal(str(random.randint(50, 500)))
            idem_key = hashlib.sha256(
                f"pending:{acct.id}:{uuid.uuid4()}".encode()
            ).hexdigest()
            payments.append(
                Payment(
                    account=acct,
                    processor=processor,
                    amount=amount,
                    payment_method=Payment.Method.CARD,
                    status=random.choice([Payment.Status.PENDING, Payment.Status.FAILED]),
                    processor_ref=f"pi_{uuid.uuid4().hex[:24]}",
                    idempotency_key=idem_key,
                    metadata={"note": "Demo payment"},
                )
            )

        Payment.objects.bulk_create(payments, ignore_conflicts=True)
        self.stdout.write(f"Payments: {len(payments)} created")

        # ----- 9. Import Jobs -----
        import_jobs = []
        for i, fname in enumerate(IMPORT_FILES):
            days_ago = (len(IMPORT_FILES) - i) * 15 + random.randint(0, 10)
            started = now - timedelta(days=days_ago)
            total = random.randint(20, 120)
            errors = random.randint(0, max(1, total // 10))
            ok = total - errors

            status = SFTPImportJob.Status.COMPLETED
            completed = started + timedelta(minutes=random.randint(2, 15))

            error_details = []
            for e in range(errors):
                error_details.append({
                    "row": random.randint(2, total),
                    "field": random.choice(["external_ref", "amount", "email", "phone"]),
                    "error": random.choice([
                        "Duplicate external_ref",
                        "Invalid amount format",
                        "Missing required field",
                        "Email format invalid",
                    ]),
                })

            import_jobs.append(
                SFTPImportJob(
                    agency=agency,
                    source_host="sftp.clientdata.com",
                    file_name=fname,
                    file_path_s3=f"s3://debtflow-files/imports/{agency.id}/{fname}",
                    status=status,
                    total_records=total,
                    processed_ok=ok,
                    processed_errors=errors,
                    error_details=error_details,
                    started_at=started,
                    completed_at=completed,
                )
            )

        # One processing job for realism
        import_jobs.append(
            SFTPImportJob(
                agency=agency,
                source_host="sftp.clientdata.com",
                file_name="incoming_accounts_feb15.csv",
                status=SFTPImportJob.Status.PROCESSING,
                total_records=45,
                processed_ok=32,
                processed_errors=0,
                started_at=now - timedelta(minutes=3),
            )
        )

        SFTPImportJob.objects.bulk_create(import_jobs, ignore_conflicts=True)
        self.stdout.write(f"Import jobs: {len(import_jobs)} created")

        # ----- Summary -----
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("  Demo data seeded successfully!"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write("")
        self.stdout.write(f"  Agency:       {agency.name}")
        self.stdout.write(f"  Debtors:      {len(debtors)}")
        self.stdout.write(f"  Accounts:     {len(accounts)}")
        self.stdout.write(f"  Payments:     {len(payments)}")
        self.stdout.write(f"  Activities:   {len(activities)}")
        self.stdout.write(f"  Import Jobs:  {len(import_jobs)}")
        self.stdout.write(f"  Collectors:   {len(collectors)}")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("  Login credentials:"))
        self.stdout.write(f"    Admin:     demo.admin / Demo@2026")
        self.stdout.write(f"    Collector: sarah.mitchell / Collector@2026")
        self.stdout.write("")
