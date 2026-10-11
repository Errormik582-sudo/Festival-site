"""URL-маршруты для API."""
from rest_framework.routers import DefaultRouter
from .views import (
    FestivalViewSet, LocationViewSet, EventViewSet,
    InfoStandViewSet, RoadViewSet, CampViewSet, BookingViewSet,
    GroupViewSet, FestivalParticipantViewSet, UserViewSet,
)

router = DefaultRouter()
router.register('festivals', FestivalViewSet, basename='festival')
router.register('locations', LocationViewSet, basename='location')
router.register('events', EventViewSet, basename='event')
router.register('infostands', InfoStandViewSet, basename='infostand')
router.register('roads', RoadViewSet, basename='road')
router.register('camps', CampViewSet, basename='camp')
router.register('bookings', BookingViewSet, basename='booking')
router.register('groups', GroupViewSet, basename='group')
router.register('participants', FestivalParticipantViewSet, basename='participant')
router.register('users', UserViewSet, basename='user')

urlpatterns = router.urls