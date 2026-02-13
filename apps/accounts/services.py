"""Business logic services for the accounts app."""
from django.db import transaction
from django.utils import timezone

from .models import Account, Activity, Collector


class AccountService:
    """Encapsulates account business logic — assign, transition, add note."""

    @staticmethod
    @transaction.atomic
    def assign_account(account: Account, collector: Collector, assigned_by_user) -> Account:
        """Assign an account to a collector."""
        old_collector = account.assigned_to
        account.assigned_to = collector
        if account.status == Account.Status.NEW:
            account.status = Account.Status.ASSIGNED
        account.save(update_fields=["assigned_to", "status", "updated_at"])

        old_name = old_collector.user.get_full_name() if old_collector else "Unassigned"
        new_name = collector.user.get_full_name()

        Activity.objects.create(
            account=account,
            user=assigned_by_user,
            activity_type=Activity.ActivityType.ASSIGNMENT,
            description=f"Account reassigned from {old_name} to {new_name}",
            metadata={
                "old_collector_id": str(old_collector.id) if old_collector else None,
                "new_collector_id": str(collector.id),
            },
        )
        return account

    @staticmethod
    @transaction.atomic
    def transition_status(account: Account, new_status: str, user, note: str = "") -> Account:
        """Transition account to a new status with state machine validation."""
        old_status = account.status
        if not account.can_transition_to(new_status):
            raise ValueError(
                f"Invalid transition from '{old_status}' to '{new_status}'. "
                f"Valid transitions: {Account.VALID_TRANSITIONS.get(old_status, [])}"
            )

        account.status = new_status
        account.save(update_fields=["status", "updated_at"])

        description = f"Status changed from {old_status} to {new_status}"
        if note:
            description += f" — {note}"

        Activity.objects.create(
            account=account,
            user=user,
            activity_type=Activity.ActivityType.STATUS_CHANGE,
            description=description,
            metadata={"old_status": old_status, "new_status": new_status},
        )
        return account

    @staticmethod
    def add_note(account: Account, user, text: str) -> Activity:
        """Add a text note to the account timeline."""
        account.last_contact_at = timezone.now()
        account.save(update_fields=["last_contact_at", "updated_at"])

        return Activity.objects.create(
            account=account,
            user=user,
            activity_type=Activity.ActivityType.NOTE,
            description=text,
        )
