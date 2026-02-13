"""DRF views for SFTP import management."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAgencyAdmin

from .models import SFTPImportJob
from .serializers import ImportErrorSerializer, SFTPImportJobDetailSerializer, SFTPImportJobSerializer


class ImportJobViewSet(viewsets.ReadOnlyModelViewSet):
    """List and detail SFTP import jobs. Trigger manual imports."""

    permission_classes = [IsAuthenticated, IsAgencyAdmin]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return SFTPImportJob.objects.all()
        collector = getattr(user, "collector_profile", None)
        if collector:
            return SFTPImportJob.objects.filter(agency=collector.agency)
        return SFTPImportJob.objects.none()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SFTPImportJobDetailSerializer
        return SFTPImportJobSerializer

    @action(detail=False, methods=["post"], url_path="trigger")
    def trigger(self, request):
        """Manually trigger an SFTP import outside the normal schedule."""
        from tasks.sftp_tasks import sftp_poll_all_agencies

        task = sftp_poll_all_agencies.delay()
        return Response(
            {"task_id": task.id, "status": "triggered"},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["get"], url_path="errors")
    def errors(self, request, pk=None):
        """Paginated error list for a specific import job."""
        job = self.get_object()
        errors = job.error_details or []
        # Simple pagination
        page_size = 50
        page = int(request.query_params.get("page", 1))
        start = (page - 1) * page_size
        end = start + page_size
        paginated = errors[start:end]
        return Response(
            {
                "count": len(errors),
                "page": page,
                "page_size": page_size,
                "results": ImportErrorSerializer(paginated, many=True).data,
            }
        )
