from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/', include('users.urls')),  # 用户模块接口
    path('api/', include('activities.urls')),  # 活动模块接口
]