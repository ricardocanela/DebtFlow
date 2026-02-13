from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["action", "content_type", "object_id", "user", "ip_address", "created_at"]
    list_filter = ["action", "content_type"]
    search_fields = ["object_id"]
    readonly_fields = ["user", "action", "content_type", "object_id", "changes", "ip_address", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
