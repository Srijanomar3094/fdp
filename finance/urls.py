from django.urls import path
from . import views

urlpatterns = [
    path('transactions/', views.transactions_list, name='transactions-list'),
    path('transactions/<int:transaction_id>/', views.transaction_detail, name='transaction-detail'),
    path('categories/', views.categories_list, name='categories-list'),
]
