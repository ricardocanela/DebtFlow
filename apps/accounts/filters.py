"""Django-filter FilterSets for accounts."""
from django.db import models
from django_filters import rest_framework as filters

from .models import Account


class AccountFilter(filters.FilterSet):
    """FilterSet for Account list endpoint."""

    status = filters.ChoiceFilter(choices=Account.Status.choices)
    collector = filters.UUIDFilter(field_name="assigned_to_id")
    agency = filters.UUIDFilter(field_name="agency_id")
    min_balance = filters.NumberFilter(field_name="current_balance", lookup_expr="gte")
    max_balance = filters.NumberFilter(field_name="current_balance", lookup_expr="lte")
    created_after = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    created_before = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")
    due_after = filters.DateFilter(field_name="due_date", lookup_expr="gte")
    due_before = filters.DateFilter(field_name="due_date", lookup_expr="lte")
    priority = filters.NumberFilter()
    search = filters.CharFilter(method="search_filter")

    class Meta:
        model = Account
        fields = [
            "status",
            "collector",
            "agency",
            "min_balance",
            "max_balance",
            "created_after",
            "created_before",
            "priority",
        ]

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            models.Q(external_ref__icontains=value)
            | models.Q(debtor__full_name__icontains=value)
            | models.Q(debtor__email__icontains=value)
        )
