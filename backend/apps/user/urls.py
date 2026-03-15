from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    path('register/', views.Register.as_view()),
    path('token/', TokenObtainPairView.as_view()),
    path('info/', views.UserInfo.as_view()),
]