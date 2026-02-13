from django.contrib import admin

from .models import Payment, PaymentProcessor


@admin.register(PaymentProcessor)
class PaymentProcessorAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "created_at"]
    list_filter = ["is_active"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "account", "amount", "payment_method", "status", "processor", "created_at"]
    list_filter = ["status", "payment_method", "processor"]
    search_fields = ["processor_ref", "idempotency_key"]
    raw_id_fields = ["account"]
