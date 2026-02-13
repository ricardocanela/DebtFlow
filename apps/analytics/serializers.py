"""Response serializers for analytics endpoints."""
from rest_framework import serializers


class DashboardSerializer(serializers.Serializer):
    total_accounts = serializers.IntegerField()
    total_collected = serializers.DecimalField(max_digits=14, decimal_places=2)
    collection_rate = serializers.FloatField()
    avg_days_to_settle = serializers.FloatField()
    accounts_by_status = serializers.DictField(child=serializers.IntegerField())


class CollectorPerformanceSerializer(serializers.Serializer):
    collector_id = serializers.UUIDField()
    collector_name = serializers.CharField()
    total_accounts = serializers.IntegerField()
    total_collected = serializers.DecimalField(max_digits=14, decimal_places=2)
    success_rate = serializers.FloatField()


class PaymentTrendSerializer(serializers.Serializer):
    period = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    count = serializers.IntegerField()


class AgingBucketSerializer(serializers.Serializer):
    bucket = serializers.CharField()
    count = serializers.IntegerField()
    total_balance = serializers.DecimalField(max_digits=14, decimal_places=2)
