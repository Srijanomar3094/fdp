from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'transaction_type', 'category', 'date', 'created_by', 'status']
    list_filter = ['transaction_type', 'category', 'status', 'date']
    search_fields = ['title', 'notes']
    date_hierarchy = 'date'
    ordering = ['-date']
    readonly_fields = ['created_at', 'updated_at']
