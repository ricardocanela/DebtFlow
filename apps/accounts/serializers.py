"""DRF serializers for the accounts app."""
from rest_framework import serializers

from .models import Account, Activity, Agency, Collector, Debtor


class AgencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Agency
        fields = ["id", "name", "license_number", "settings", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class DebtorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debtor
        fields = [
            "id",
            "external_ref",
            "full_name",
            "ssn_last4",
            "email",
            "phone",
            "address_line1",
            "address_city",
            "address_state",
            "address_zip",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class CollectorSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Collector
        fields = ["id", "username", "full_name", "agency", "commission_rate", "is_active", "max_accounts"]
        read_only_fields = ["id"]


class ActivitySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True, default="System")

    class Meta:
        model = Activity
        fields = ["id", "activity_type", "description", "metadata", "user_name", "created_at"]
        read_only_fields = ["id", "created_at"]


class AccountListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    debtor_name = serializers.CharField(source="debtor.full_name", read_only=True)
    collector_name = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            "id",
            "external_ref",
            "debtor_name",
            "status",
            "original_amount",
            "current_balance",
            "priority",
            "collector_name",
            "due_date",
            "last_contact_at",
            "created_at",
        ]

    def get_collector_name(self, obj) -> str | None:
        if obj.assigned_to:
            return obj.assigned_to.user.get_full_name()
        return None


class AccountDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail views, includes nested debtor and recent activities."""

    debtor = DebtorSerializer(read_only=True)
    assigned_to = CollectorSerializer(read_only=True)
    agency = AgencySerializer(read_only=True)
    recent_activities = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = [
            "id",
            "agency",
            "debtor",
            "assigned_to",
            "external_ref",
            "original_amount",
            "current_balance",
            "status",
            "priority",
            "due_date",
            "last_contact_at",
            "created_at",
            "updated_at",
            "recent_activities",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_recent_activities(self, obj) -> list:
        activities = obj.activities.all()[:10]
        return ActivitySerializer(activities, many=True).data


class AccountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating accounts."""

    class Meta:
        model = Account
        fields = [
            "agency",
            "debtor",
            "external_ref",
            "original_amount",
            "current_balance",
            "status",
            "priority",
            "due_date",
        ]

    def validate(self, attrs):
        if "current_balance" not in attrs:
            attrs["current_balance"] = attrs.get("original_amount", 0)
        return attrs


class AccountUpdateSerializer(serializers.ModelSerializer):
    """Serializer for partial updates."""

    class Meta:
        model = Account
        fields = ["current_balance", "priority", "due_date", "last_contact_at"]


class AssignAccountSerializer(serializers.Serializer):
    collector_id = serializers.UUIDField()

    def validate_collector_id(self, value):
        try:
            Collector.objects.get(id=value, is_active=True)
        except Collector.DoesNotExist:
            raise serializers.ValidationError("Collector not found or inactive.")
        return value


class TransitionSerializer(serializers.Serializer):
    new_status = serializers.ChoiceField(choices=Account.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True, default="")


class AddNoteSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=5000)
