"""Custom permissions for the accounts app."""
from rest_framework.permissions import BasePermission


class IsAgencyAdmin(BasePermission):
    """Only agency admins (users in the 'agency_admin' group) or superusers are allowed."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name="agency_admin").exists()


class IsCollector(BasePermission):
    """Only collectors (users in the 'collector' group) are allowed."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="collector").exists()
        )


class IsAgencyAdminOrCollector(BasePermission):
    """Agency admins or collectors are allowed."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name__in=["agency_admin", "collector"]).exists()


class IsAccountOwner(BasePermission):
    """Collector can only access accounts assigned to them within their agency."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if request.user.groups.filter(name="agency_admin").exists():
            collector = getattr(request.user, "collector_profile", None)
            if collector:
                return obj.agency_id == collector.agency_id
            return True

        collector = getattr(request.user, "collector_profile", None)
        if not collector:
            return False
        return obj.agency_id == collector.agency_id and obj.assigned_to_id == collector.id
