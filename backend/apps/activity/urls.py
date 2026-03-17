from django.urls import path, include
from rest_framework.routers import DefaultRouter
# 导入activity APP的视图
from .views import ActivityViewSet

router = DefaultRouter()
router.register('activity', ActivityViewSet, basename='activity')

urlpatterns = [
    path('', include(router.urls)),
]