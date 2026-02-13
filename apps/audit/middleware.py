"""Audit middleware — automatically logs model changes."""
import logging

from django.contrib.contenttypes.models import ContentType

from .models import AuditLog

logger = logging.getLogger(__name__)

# Models to audit automatically
AUDITED_MODELS = {
    "accounts.Account",
    "accounts.Agency",
    "accounts.Collector",
    "payments.Payment",
    "payments.PaymentProcessor",
    "integrations.SFTPImportJob",
}


class AuditLogMiddleware:
    """Middleware that captures the request user and IP for audit logging.

    The actual audit entries are created via Django signals (post_save, post_delete)
    using the thread-local user info stored by this middleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store user and IP in thread-local for signal handlers
        _thread_local.user = getattr(request, "user", None)
        _thread_local.ip_address = self._get_client_ip(request)

        response = self.get_response(request)

        # Clean up
        _thread_local.user = None
        _thread_local.ip_address = None

        return response

    @staticmethod
    def _get_client_ip(request) -> str:
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")


import threading

_thread_local = threading.local()


def get_audit_user():
    return getattr(_thread_local, "user", None)


def get_audit_ip():
    return getattr(_thread_local, "ip_address", None)


def create_audit_log(instance, action: str, changes: dict | None = None):
    """Helper to create an audit log entry for a model instance."""
    model_label = f"{instance._meta.app_label}.{instance._meta.object_name}"
    if model_label not in AUDITED_MODELS:
        return

    user = get_audit_user()
    if user and not user.is_authenticated:
        user = None

    try:
        AuditLog.objects.create(
            user=user,
            action=action,
            content_type=ContentType.objects.get_for_model(instance),
            object_id=instance.pk,
            changes=changes or {},
            ip_address=get_audit_ip(),
        )
    except Exception:
        logger.exception("Failed to create audit log for %s %s", model_label, instance.pk)
