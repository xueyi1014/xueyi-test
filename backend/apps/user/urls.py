from django.urls import path, include
from rest_framework.routers import DefaultRouter
# 导入user APP的视图
from .views import UserViewSet

router = DefaultRouter()
router.register('', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]