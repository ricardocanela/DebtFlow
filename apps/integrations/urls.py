"""URL routing for integrations app."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ImportJobViewSet

router = DefaultRouter()
router.register("imports", ImportJobViewSet, basename="import-job")

urlpatterns = [
    path("", include(router.urls)),
]
