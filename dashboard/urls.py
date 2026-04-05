from django.urls import path
from . import views

urlpatterns = [
    path('summary/', views.summary, name='dashboard-summary'),
    path('categories/', views.category_breakdown, name='dashboard-categories'),
    path('trends/', views.monthly_trends, name='dashboard-trends'),
    path('recent/', views.recent_activity, name='dashboard-recent'),
]
