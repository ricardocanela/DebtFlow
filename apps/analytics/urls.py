"""URL routing for analytics app."""
from django.urls import path

from .views import AgingReportView, CollectorPerformanceView, DashboardView, PaymentTrendsView

urlpatterns = [
    path("analytics/dashboard/", DashboardView.as_view(), name="analytics-dashboard"),
    path("analytics/collectors/", CollectorPerformanceView.as_view(), name="analytics-collectors"),
    path("analytics/payments/trends/", PaymentTrendsView.as_view(), name="analytics-payment-trends"),
    path("analytics/aging-report/", AgingReportView.as_view(), name="analytics-aging-report"),
]
