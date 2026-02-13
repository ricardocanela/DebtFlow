from django.contrib import admin

from .models import Account, Activity, Agency, Collector, Debtor


@admin.register(Agency)
class AgencyAdmin(admin.ModelAdmin):
    list_display = ["name", "license_number", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "license_number"]


@admin.register(Debtor)
class DebtorAdmin(admin.ModelAdmin):
    list_display = ["full_name", "external_ref", "email", "phone", "created_at"]
    search_fields = ["full_name", "external_ref", "email"]


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["external_ref", "agency", "debtor", "status", "current_balance", "assigned_to", "created_at"]
    list_filter = ["status", "agency"]
    search_fields = ["external_ref", "debtor__full_name"]
    raw_id_fields = ["debtor", "assigned_to"]


@admin.register(Collector)
class CollectorAdmin(admin.ModelAdmin):
    list_display = ["user", "agency", "commission_rate", "is_active", "max_accounts"]
    list_filter = ["is_active", "agency"]
    raw_id_fields = ["user"]


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ["activity_type", "account", "user", "created_at"]
    list_filter = ["activity_type"]
    raw_id_fields = ["account", "user"]
