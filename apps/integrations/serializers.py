"""DRF serializers for SFTP integration."""
from rest_framework import serializers

from .models import SFTPImportJob


class SFTPImportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = SFTPImportJob
        fields = [
            "id",
            "agency",
            "source_host",
            "file_name",
            "file_path_s3",
            "status",
            "total_records",
            "processed_ok",
            "processed_errors",
            "started_at",
            "completed_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "total_records",
            "processed_ok",
            "processed_errors",
            "started_at",
            "completed_at",
            "created_at",
        ]


class SFTPImportJobDetailSerializer(SFTPImportJobSerializer):
    class Meta(SFTPImportJobSerializer.Meta):
        fields = SFTPImportJobSerializer.Meta.fields + ["error_details"]


class ImportErrorSerializer(serializers.Serializer):
    line = serializers.IntegerField()
    error = serializers.CharField()
    data = serializers.DictField(required=False)
