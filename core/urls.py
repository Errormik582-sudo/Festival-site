"""URL-маршруты HTML-страниц."""
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('events/', views.events_list, name='events_list'),
    path('locations/<int:pk>/', views.location_detail, name='location_detail'),
    path('booking/', views.booking_view, name='booking'),
    path('groups/', views.groups_view, name='groups'),
    path('manage/', views.manage_view, name='manage'),
    path('users/', views.users_view, name='users'),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]