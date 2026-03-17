from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ActivityViewSet, BatchViewSet, ViolationViewSet, BlacklistAppealViewSet, ExportViewSet, PosterViewSet, RatingViewSet, AttendanceViewSet

router = DefaultRouter()
router.register('activity', ActivityViewSet, basename='activity')
router.register('batch', BatchViewSet, basename='batch')
router.register('violation', ViolationViewSet, basename='violation')
router.register('appeal', BlacklistAppealViewSet, basename='appeal')
router.register('export', ExportViewSet, basename='export')
router.register('poster', PosterViewSet, basename='poster')
router.register('rating', RatingViewSet, basename='rating')
router.register('attendance', AttendanceViewSet, basename='attendance')

urlpatterns = [
    path('', include(router.urls)),
]