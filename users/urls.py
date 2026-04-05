from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('auth/login/', views.login_view, name='auth-login'),
    path('auth/logout/', views.logout_view, name='auth-logout'),
    path('auth/me/', views.me_view, name='auth-me'),

    # User management (admin only)
    path('users/', views.users_list, name='users-list'),
    path('users/<int:user_id>/', views.user_detail, name='user-detail'),
]
