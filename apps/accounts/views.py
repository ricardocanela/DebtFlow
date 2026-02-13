"""DRF ViewSets for the accounts app."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import AccountFilter
from .models import Account, Activity, Agency, Collector
from .permissions import IsAccountOwner, IsAgencyAdmin, IsAgencyAdminOrCollector
from .serializers import (
    AccountCreateSerializer,
    AccountDetailSerializer,
    AccountListSerializer,
    AccountUpdateSerializer,
    ActivitySerializer,
    AddNoteSerializer,
    AgencySerializer,
    AssignAccountSerializer,
    CollectorSerializer,
    TransitionSerializer,
)
from .services import AccountService


class AccountViewSet(viewsets.ModelViewSet):
    """CRUD + custom actions for debt accounts.

    - list: cursor-paginated with filters
    - retrieve: full detail with debtor, collector, recent activities
    - create: agency admin only
    - partial_update: admin or assigned collector
    - assign: assign to collector (admin only)
    - add_note: add text note to timeline
    - timeline: full activity list
    - transition: validated state machine transition
    """

    filterset_class = AccountFilter
    ordering_fields = ["created_at", "current_balance", "priority", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        qs = Account.objects.select_related("debtor", "assigned_to__user", "agency")
        user = self.request.user

        # Collectors can only see their agency's accounts assigned to them
        collector = getattr(user, "collector_profile", None)
        if collector and not user.groups.filter(name="agency_admin").exists():
            return qs.filter(agency=collector.agency, assigned_to=collector)

        # Agency admins see all accounts in their agency
        if collector:
            return qs.filter(agency=collector.agency)

        # Superusers see everything
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return AccountListSerializer
        if self.action == "retrieve":
            return AccountDetailSerializer
        if self.action == "create":
            return AccountCreateSerializer
        if self.action in ("update", "partial_update"):
            return AccountUpdateSerializer
        return AccountListSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsAgencyAdmin()]
        if self.action in ("update", "partial_update"):
            return [IsAuthenticated(), IsAgencyAdminOrCollector(), IsAccountOwner()]
        if self.action in ("assign", "export"):
            return [IsAuthenticated(), IsAgencyAdmin()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"], url_path="assign")
    def assign(self, request, pk=None):
        """Assign account to a collector."""
        account = self.get_object()
        serializer = AssignAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        collector = Collector.objects.get(id=serializer.validated_data["collector_id"])
        account = AccountService.assign_account(account, collector, request.user)
        return Response(AccountDetailSerializer(account).data)

    @action(detail=True, methods=["post"], url_path="add-note")
    def add_note(self, request, pk=None):
        """Add a note to the account timeline."""
        account = self.get_object()
        serializer = AddNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        activity = AccountService.add_note(account, request.user, serializer.validated_data["text"])
        return Response(ActivitySerializer(activity).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="timeline")
    def timeline(self, request, pk=None):
        """Full activity timeline for an account."""
        account = self.get_object()
        activities = Activity.objects.filter(account=account).select_related("user")
        page = self.paginate_queryset(activities)
        if page is not None:
            return self.get_paginated_response(ActivitySerializer(page, many=True).data)
        return Response(ActivitySerializer(activities, many=True).data)

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        """Validate and perform status transition."""
        account = self.get_object()
        serializer = TransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            account = AccountService.transition_status(
                account,
                serializer.validated_data["new_status"],
                request.user,
                serializer.validated_data.get("note", ""),
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(AccountDetailSerializer(account).data)

    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        """Trigger async CSV export via Celery."""
        from tasks.report_tasks import generate_account_export

        filters = {k: v for k, v in request.query_params.items() if k in ("status", "agency")}
        task = generate_account_export.delay(user_id=request.user.id, filters=filters)
        return Response({"task_id": task.id, "status": "processing"}, status=status.HTTP_202_ACCEPTED)


class AgencyViewSet(viewsets.ModelViewSet):
    """CRUD for agencies — admin only."""

    queryset = Agency.objects.all()
    serializer_class = AgencySerializer
    permission_classes = [IsAuthenticated, IsAgencyAdmin]

    def get_queryset(self):
        return Agency.objects.all()


class CollectorViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list of collectors within the user's agency."""

    serializer_class = CollectorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Collector.objects.all().select_related("user")
        collector = getattr(user, "collector_profile", None)
        if collector:
            return Collector.objects.filter(agency=collector.agency).select_related("user")
        return Collector.objects.none()
