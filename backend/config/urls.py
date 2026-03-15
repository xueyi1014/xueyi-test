from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/user/', include('apps.user.urls')),
    path('api/activity/', include('apps.activity.urls')),
    path('api/reg/', include('apps.registration.urls')),
]