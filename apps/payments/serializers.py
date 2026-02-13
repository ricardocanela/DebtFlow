"""DRF serializers for the payments app."""
import hashlib
import time

from rest_framework import serializers

from .models import Payment, PaymentProcessor


class PaymentProcessorSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentProcessor
        fields = ["id", "name", "slug", "api_base_url", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class PaymentSerializer(serializers.ModelSerializer):
    processor_name = serializers.CharField(source="processor.name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "account",
            "processor",
            "processor_name",
            "amount",
            "payment_method",
            "status",
            "processor_ref",
            "idempotency_key",
            "metadata",
            "created_at",
        ]
        read_only_fields = ["id", "status", "processor_ref", "idempotency_key", "metadata", "created_at"]


class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["account", "processor", "amount", "payment_method"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        return value

    def create(self, validated_data):
        # Generate idempotency key from account + amount + timestamp
        raw = f"{validated_data['account'].id}:{validated_data['amount']}:{time.time()}"
        validated_data["idempotency_key"] = hashlib.sha256(raw.encode()).hexdigest()
        return super().create(validated_data)


class RefundSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=False, default="Requested by agency admin")
