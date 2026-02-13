"""Analytics API views — read-only dashboard endpoints with optimized queries."""
from datetime import timedelta

from django.db.models import Avg, Count, DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncDay, TruncMonth, TruncWeek
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import Account
from apps.accounts.permissions import IsAgencyAdmin
from apps.payments.models import Payment


class DashboardView(APIView):
    """KPIs: total collected, collection rate, avg days to settle, accounts by status."""

    permission_classes = [IsAuthenticated, IsAgencyAdmin]

    def get(self, request):
        user = request.user
        collector = getattr(user, "collector_profile", None)
        accounts = Account.objects.all()
        if collector:
            accounts = accounts.filter(agency=collector.agency)

        total_accounts = accounts.count()
        settled = accounts.filter(status=Account.Status.SETTLED).count()
        collection_rate = (settled / total_accounts * 100) if total_accounts > 0 else 0

        total_collected = (
            Payment.objects.filter(
                account__in=accounts,
                status=Payment.Status.COMPLETED,
            ).aggregate(total=Coalesce(Sum("amount"), Value(0), output_field=DecimalField()))["total"]
        )

        # Average days from creation to settlement
        settled_accounts = accounts.filter(status=Account.Status.SETTLED)
        avg_days = settled_accounts.aggregate(
            avg_days=Avg(F("updated_at") - F("created_at"))
        )["avg_days"]
        avg_days_to_settle = avg_days.total_seconds() / 86400 if avg_days else 0

        # Accounts by status
        status_counts = dict(
            accounts.values_list("status").annotate(count=Count("id")).values_list("status", "count")
        )

        return Response(
            {
                "total_accounts": total_accounts,
                "total_collected": total_collected,
                "collection_rate": round(collection_rate, 2),
                "avg_days_to_settle": round(avg_days_to_settle, 1),
                "accounts_by_status": status_counts,
            }
        )


class CollectorPerformanceView(APIView):
    """Performance metrics per collector."""

    permission_classes = [IsAuthenticated, IsAgencyAdmin]

    def get(self, request):
        user = request.user
        collector = getattr(user, "collector_profile", None)
        accounts = Account.objects.all()
        if collector:
            accounts = accounts.filter(agency=collector.agency)

        results = (
            accounts.filter(assigned_to__isnull=False)
            .values("assigned_to__id", "assigned_to__user__first_name", "assigned_to__user__last_name")
            .annotate(
                total_accounts=Count("id"),
                settled_accounts=Count("id", filter=Q(status=Account.Status.SETTLED)),
                total_collected=Coalesce(
                    Sum("payments__amount", filter=Q(payments__status=Payment.Status.COMPLETED)),
                    Value(0),
                    output_field=DecimalField(),
                ),
            )
        )

        data = []
        for row in results:
            total = row["total_accounts"]
            settled = row["settled_accounts"]
            data.append(
                {
                    "collector_id": row["assigned_to__id"],
                    "collector_name": f"{row['assigned_to__user__first_name']} {row['assigned_to__user__last_name']}".strip(),
                    "total_accounts": total,
                    "total_collected": row["total_collected"],
                    "success_rate": round(settled / total * 100, 2) if total > 0 else 0,
                }
            )

        return Response(data)


class PaymentTrendsView(APIView):
    """Payment volume grouped by day, week, or month."""

    permission_classes = [IsAuthenticated, IsAgencyAdmin]

    def get(self, request):
        granularity = request.query_params.get("granularity", "day")
        days = int(request.query_params.get("days", 30))

        since = timezone.now() - timedelta(days=days)
        payments = Payment.objects.filter(status=Payment.Status.COMPLETED, created_at__gte=since)

        trunc_fn = {"day": TruncDay, "week": TruncWeek, "month": TruncMonth}.get(granularity, TruncDay)

        trends = (
            payments.annotate(period=trunc_fn("created_at"))
            .values("period")
            .annotate(
                total_amount=Sum("amount"),
                count=Count("id"),
            )
            .order_by("period")
        )

        return Response(
            [
                {
                    "period": row["period"].isoformat(),
                    "total_amount": row["total_amount"],
                    "count": row["count"],
                }
                for row in trends
            ]
        )


class AgingReportView(APIView):
    """Aging buckets: 0-30, 31-60, 61-90, 90+ days past due."""

    permission_classes = [IsAuthenticated, IsAgencyAdmin]

    def get(self, request):
        user = request.user
        collector = getattr(user, "collector_profile", None)
        accounts = Account.objects.exclude(status__in=[Account.Status.SETTLED, Account.Status.CLOSED])
        if collector:
            accounts = accounts.filter(agency=collector.agency)

        today = timezone.now().date()
        buckets = [
            ("0-30 days", 0, 30),
            ("31-60 days", 31, 60),
            ("61-90 days", 61, 90),
            ("90+ days", 91, None),
        ]

        results = []
        for label, min_days, max_days in buckets:
            qs = accounts.filter(due_date__isnull=False)
            min_date = today - timedelta(days=max_days) if max_days else None
            max_date = today - timedelta(days=min_days)

            if min_date:
                qs = qs.filter(due_date__gte=min_date, due_date__lte=max_date)
            else:
                qs = qs.filter(due_date__lte=max_date)

            agg = qs.aggregate(
                count=Count("id"),
                total_balance=Coalesce(Sum("current_balance"), Value(0), output_field=DecimalField()),
            )
            results.append(
                {
                    "bucket": label,
                    "count": agg["count"],
                    "total_balance": agg["total_balance"],
                }
            )

        return Response(results)
