"""Factory Boy factories for accounts app models."""
import factory
from django.contrib.auth.models import User

from apps.accounts.models import Account, Activity, Agency, Collector, Debtor


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@test.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")


class AgencyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Agency

    name = factory.Sequence(lambda n: f"Agency {n}")
    license_number = factory.Sequence(lambda n: f"LIC-{n:04d}")
    is_active = True


class DebtorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Debtor

    external_ref = factory.Sequence(lambda n: f"DBT-{n:06d}")
    full_name = factory.Faker("name")
    ssn_last4 = factory.Faker("numerify", text="####")
    email = factory.Faker("email")
    phone = factory.Faker("numerify", text="###-###-####")
    address_line1 = factory.Faker("street_address")
    address_city = factory.Faker("city")
    address_state = factory.Faker("state_abbr")
    address_zip = factory.Faker("zipcode")


class CollectorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Collector

    user = factory.SubFactory(UserFactory)
    agency = factory.SubFactory(AgencyFactory)
    commission_rate = factory.Faker("pydecimal", right_digits=4, min_value=0.05, max_value=0.20)
    is_active = True
    max_accounts = 200


class AccountFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Account

    agency = factory.SubFactory(AgencyFactory)
    debtor = factory.SubFactory(DebtorFactory)
    external_ref = factory.Sequence(lambda n: f"ACC-{n:06d}")
    original_amount = factory.Faker("pydecimal", left_digits=4, right_digits=2, min_value=100, max_value=9999)
    current_balance = factory.LazyAttribute(lambda o: o.original_amount)
    status = Account.Status.NEW
    priority = factory.Faker("random_int", min=0, max=10)
    due_date = factory.Faker("date_object")


class ActivityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Activity

    account = factory.SubFactory(AccountFactory)
    activity_type = Activity.ActivityType.NOTE
    description = factory.Faker("sentence")
