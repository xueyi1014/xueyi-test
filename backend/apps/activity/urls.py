from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ActivityViewSet, BatchViewSet, ViolationViewSet, BlacklistAppealViewSet, 
    ExportViewSet, PosterViewSet, RatingViewSet, AttendanceViewSet,
    StatisticsViewSet, HoursManagementViewSet, ApplicationManagementViewSet, AppealManagementViewSet
)

router = DefaultRouter()
router.register('activity', ActivityViewSet, basename='activity')
router.register('batch', BatchViewSet, basename='batch')
router.register('violation', ViolationViewSet, basename='violation')
router.register('appeal', BlacklistAppealViewSet, basename='appeal')
router.register('export', ExportViewSet, basename='export')
router.register('poster', PosterViewSet, basename='poster')
router.register('rating', RatingViewSet, basename='rating')
router.register('attendance', AttendanceViewSet, basename='attendance')
router.register('statistics', StatisticsViewSet, basename='statistics')
router.register('hours', HoursManagementViewSet, basename='hours')
router.register('application', ApplicationManagementViewSet, basename='application')
router.register('appeal-management', AppealManagementViewSet, basename='appeal-management')

urlpatterns = [
    path('', include(router.urls)),
]