"""Custom JWT authentication for DebtFlow frontend."""
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extend JWT claims with user role, agency, and collector info."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # User info
        token["username"] = user.username
        token["email"] = user.email
        token["first_name"] = user.first_name
        token["last_name"] = user.last_name
        token["is_superuser"] = user.is_superuser

        # Groups/roles
        groups = list(user.groups.values_list("name", flat=True))
        token["groups"] = groups

        # Collector and agency info
        collector = getattr(user, "collector_profile", None)
        if collector:
            token["collector_id"] = str(collector.id)
            token["agency_id"] = str(collector.agency_id)
        else:
            token["collector_id"] = None
            token["agency_id"] = None

        return token


class UserProfileSerializer(serializers.Serializer):
    """Serializer for the /auth/me/ endpoint."""

    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    is_superuser = serializers.BooleanField()
    groups = serializers.ListField(child=serializers.CharField())
    collector_id = serializers.UUIDField(allow_null=True)
    agency_id = serializers.UUIDField(allow_null=True)


class UserProfileView(APIView):
    """GET /api/v1/auth/me/ — Returns the authenticated user's profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        collector = getattr(user, "collector_profile", None)
        groups = list(user.groups.values_list("name", flat=True))

        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_superuser": user.is_superuser,
            "groups": groups,
            "collector_id": collector.id if collector else None,
            "agency_id": collector.agency_id if collector else None,
        }

        serializer = UserProfileSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
