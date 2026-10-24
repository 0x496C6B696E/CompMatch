from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MatchView, ProfessionViewSet, ProgramViewSet, SettingsView

router = DefaultRouter()
router.register("professions", ProfessionViewSet, basename="profession")
router.register("programs", ProgramViewSet, basename="program")

urlpatterns = [
    path("match/", MatchView.as_view(), name="match"),
    path("settings/", SettingsView.as_view(), name="settings"),
    path("", include(router.urls)),
]
