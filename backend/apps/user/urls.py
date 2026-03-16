from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter()
router.register('', UserViewSet, basename='user')  # 空前缀，接口路径为 /api/user/xxx/

urlpatterns = [
    path('', include(router.urls)),
]