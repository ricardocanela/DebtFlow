"""DRF ViewSets for the payments app."""
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.permissions import IsAgencyAdmin

from .models import Payment, PaymentProcessor
from .serializers import PaymentCreateSerializer, PaymentProcessorSerializer, PaymentSerializer, RefundSerializer
from .services import PaymentService, ServiceUnavailableError


class PaymentViewSet(viewsets.ModelViewSet):
    """CRUD for payments + refund action."""

    permission_classes = [IsAuthenticated]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Payment.objects.select_related("account", "processor").all()

    def get_serializer_class(self):
        if self.action == "create":
            return PaymentCreateSerializer
        return PaymentSerializer

    def perform_create(self, serializer):
        payment = serializer.save()
        service = PaymentService()
        try:
            service.create_payment(payment)
        except ServiceUnavailableError:
            pass  # Payment saved as failed — client can retry
        except Exception:
            pass  # Payment saved as failed

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAgencyAdmin])
    def refund(self, request, pk=None):
        """Initiate a refund for a completed payment."""
        payment = self.get_object()
        serializer = RefundSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = PaymentService()
        try:
            payment = service.refund_payment(payment, serializer.validated_data.get("reason", ""))
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ServiceUnavailableError as e:
            return Response({"detail": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(PaymentSerializer(payment).data)


class PaymentProcessorViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list of configured payment processors."""

    queryset = PaymentProcessor.objects.filter(is_active=True)
    serializer_class = PaymentProcessorSerializer
    permission_classes = [IsAuthenticated]
