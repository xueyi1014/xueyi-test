from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # 关键：匹配你的APP名user
    path('api/user/', include('user.urls')),
    # 关键：匹配你的APP名activity
    path('api/', include('activity.urls')),
]