from django.contrib import admin

from .models import SFTPImportJob


@admin.register(SFTPImportJob)
class SFTPImportJobAdmin(admin.ModelAdmin):
    list_display = ["file_name", "agency", "status", "total_records", "processed_ok", "processed_errors", "created_at"]
    list_filter = ["status", "agency"]
    search_fields = ["file_name"]
    readonly_fields = ["error_details"]
