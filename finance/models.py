from django.db import models
from core.models import BaseModel


class Transaction(BaseModel):
    INCOME = 'income'
    EXPENSE = 'expense'

    TYPE_CHOICES = [
        (INCOME, 'Income'),
        (EXPENSE, 'Expense'),
    ]

    CATEGORY_CHOICES = [
        ('salary', 'Salary'),
        ('freelance', 'Freelance'),
        ('investment', 'Investment'),
        ('rent', 'Rent'),
        ('utilities', 'Utilities'),
        ('food', 'Food'),
        ('transport', 'Transport'),
        ('healthcare', 'Healthcare'),
        ('entertainment', 'Entertainment'),
        ('other', 'Other'),
    ]

    VALID_CATEGORIES = [c[0] for c in CATEGORY_CHOICES]

    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    date = models.DateField()
    notes = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions',
    )

    class Meta:
        db_table = 'transactions'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'{self.title} ({self.transaction_type}: {self.amount})'
