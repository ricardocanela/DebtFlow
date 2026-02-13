"""Django signals for automatic audit logging on model save/delete."""
import logging
from decimal import Decimal

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .middleware import AUDITED_MODELS, create_audit_log

logger = logging.getLogger(__name__)

# Cache original field values before save
_original_values = {}


def _get_model_label(instance) -> str:
    return f"{instance._meta.app_label}.{instance._meta.object_name}"


def _get_field_values(instance) -> dict:
    """Get current field values as a dict (excluding relations)."""
    result = {}
    for field in instance._meta.concrete_fields:
        value = getattr(instance, field.attname, None)
        # Convert non-JSON-serializable types to string
        if isinstance(value, Decimal):
            value = str(value)
        elif hasattr(value, "isoformat"):
            value = value.isoformat()
        elif hasattr(value, "hex"):
            value = str(value)
        result[field.attname] = value
    return result


@receiver(pre_save)
def capture_pre_save(sender, instance, **kwargs):
    """Capture field values before save for change diff."""
    model_label = _get_model_label(instance)
    if model_label not in AUDITED_MODELS:
        return

    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            _original_values[instance.pk] = _get_field_values(old_instance)
        except sender.DoesNotExist:
            pass


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    """Create audit log entry after model save."""
    model_label = _get_model_label(instance)
    if model_label not in AUDITED_MODELS:
        return

    if created:
        create_audit_log(instance, "create", {"new": _get_field_values(instance)})
    else:
        old_values = _original_values.pop(instance.pk, {})
        new_values = _get_field_values(instance)
        changes = {}
        for key in new_values:
            old_val = old_values.get(key)
            new_val = new_values[key]
            if str(old_val) != str(new_val):
                changes[key] = {"old": old_val, "new": new_val}
        if changes:
            create_audit_log(instance, "update", changes)


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    """Create audit log entry after model delete."""
    model_label = _get_model_label(instance)
    if model_label not in AUDITED_MODELS:
        return

    create_audit_log(instance, "delete", {"deleted": _get_field_values(instance)})
