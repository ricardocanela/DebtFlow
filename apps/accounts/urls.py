"""URL routing for the accounts app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AccountViewSet, AgencyViewSet, CollectorViewSet

router = DefaultRouter()
router.register("accounts", AccountViewSet, basename="account")
router.register("agencies", AgencyViewSet, basename="agency")
router.register("collectors", CollectorViewSet, basename="collector")

urlpatterns = [
    path("", include(router.urls)),
]
