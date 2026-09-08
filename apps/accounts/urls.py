from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import RegisterView, CustomLoginView, logout_view

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
]
