"""
Management command to seed the database with sample data for testing.

Usage:
    python manage.py seed_data
    python manage.py seed_data --clear   # clears existing data first
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from finance.models import Transaction
from users.models import User


SAMPLE_TRANSACTIONS = [
    ('Monthly Salary', 'income', 'salary', Decimal('85000.00')),
    ('Freelance Project - Web App', 'income', 'freelance', Decimal('25000.00')),
    ('Stock Dividends', 'income', 'investment', Decimal('4500.00')),
    ('Apartment Rent', 'expense', 'rent', Decimal('18000.00')),
    ('Electricity Bill', 'expense', 'utilities', Decimal('2200.00')),
    ('Internet & Phone', 'expense', 'utilities', Decimal('1500.00')),
    ('Grocery Shopping', 'expense', 'food', Decimal('6500.00')),
    ('Restaurant Dining', 'expense', 'food', Decimal('3200.00')),
    ('Uber Rides', 'expense', 'transport', Decimal('2800.00')),
    ('Metro Pass', 'expense', 'transport', Decimal('500.00')),
    ('Doctor Consultation', 'expense', 'healthcare', Decimal('1200.00')),
    ('Movie & OTT Subscriptions', 'expense', 'entertainment', Decimal('1800.00')),
    ('Freelance Design Work', 'income', 'freelance', Decimal('15000.00')),
    ('Mutual Fund Returns', 'income', 'investment', Decimal('8200.00')),
    ('Water Bill', 'expense', 'utilities', Decimal('400.00')),
    ('Grocery - Weekend', 'expense', 'food', Decimal('4100.00')),
    ('Gym Membership', 'expense', 'entertainment', Decimal('2500.00')),
    ('Online Course', 'expense', 'other', Decimal('3000.00')),
    ('Bonus Payment', 'income', 'salary', Decimal('20000.00')),
    ('Taxi - Airport', 'expense', 'transport', Decimal('1200.00')),
]


class Command(BaseCommand):
    help = 'Seed the database with sample users and transactions for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Transaction.all_objects.all().delete()
            User.objects.filter(username__in=['admin', 'analyst', 'viewer']).delete()
            self.stdout.write(self.style.WARNING('Existing data cleared.'))

        # --- Create users ---
        admin_user = self._create_user(
            username='admin',
            email='admin@finance.local',
            password='admin123',
            role=User.ADMIN,
            first_name='Alice',
            last_name='Admin',
        )
        analyst_user = self._create_user(
            username='analyst',
            email='analyst@finance.local',
            password='analyst123',
            role=User.ANALYST,
            first_name='Bob',
            last_name='Analyst',
        )
        self._create_user(
            username='viewer',
            email='viewer@finance.local',
            password='viewer123',
            role=User.VIEWER,
            first_name='Carol',
            last_name='Viewer',
        )

        # --- Create transactions ---
        created = 0
        today = date.today()
        creators = [admin_user, analyst_user]

        for i, (title, txn_type, category, amount) in enumerate(SAMPLE_TRANSACTIONS):
            days_ago = random.randint(0, 180)
            txn_date = today - timedelta(days=days_ago)
            Transaction.objects.create(
                title=title,
                amount=amount,
                transaction_type=txn_type,
                category=category,
                date=txn_date,
                notes=f'Sample transaction: {title}',
                created_by=creators[i % 2],
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nSeed complete!\n'
            f'  Users created: admin, analyst, viewer\n'
            f'  Transactions created: {created}\n\n'
            f'Login credentials:\n'
            f'  admin    / admin123    (full access)\n'
            f'  analyst  / analyst123  (read + create/update records)\n'
            f'  viewer   / viewer123   (read-only)\n'
        ))

    def _create_user(self, username, email, password, role, first_name, last_name):
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            self.stdout.write(f'  User "{username}" already exists — skipping')
            return user

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name,
        )
        self.stdout.write(f'  Created user: {username} ({role})')
        return user
