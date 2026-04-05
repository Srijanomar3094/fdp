from datetime import date
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from finance.models import Transaction
from users.decorators import login_required_json, role_required


@csrf_exempt
@login_required_json
def summary(request):
    """
    GET /api/dashboard/summary/
    Returns total income, total expenses, net balance, and transaction count.
    Accessible by all roles.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    qs = Transaction.objects.all()

    agg = qs.aggregate(
        total_income=Sum('amount', filter=Q(transaction_type='income')),
        total_expense=Sum('amount', filter=Q(transaction_type='expense')),
        total_count=Count('id'),
    )

    total_income = agg['total_income'] or Decimal('0')
    total_expense = agg['total_expense'] or Decimal('0')
    net_balance = total_income - total_expense

    return JsonResponse({
        'summary': {
            'total_income': str(total_income),
            'total_expense': str(total_expense),
            'net_balance': str(net_balance),
            'transaction_count': agg['total_count'],
        }
    })


@csrf_exempt
@login_required_json
def category_breakdown(request):
    """
    GET /api/dashboard/categories/
    Returns totals grouped by category and transaction type.
    Optional query param: ?type=income or ?type=expense
    Accessible by all roles.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    qs = Transaction.objects.all()

    txn_type = request.GET.get('type')
    if txn_type in [Transaction.INCOME, Transaction.EXPENSE]:
        qs = qs.filter(transaction_type=txn_type)

    breakdown = (
        qs.values('category', 'transaction_type')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('transaction_type', '-total')
    )

    result = [
        {
            'category': item['category'],
            'transaction_type': item['transaction_type'],
            'total': str(item['total']),
            'count': item['count'],
        }
        for item in breakdown
    ]

    return JsonResponse({'category_breakdown': result, 'count': len(result)})


@csrf_exempt
@role_required('admin', 'analyst')
def monthly_trends(request):
    """
    GET /api/dashboard/trends/
    Returns monthly income and expense totals for the past 12 months.
    Accessible by admin and analyst only.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    today = date.today()
    # Start from the same month last year
    start_date = date(today.year - 1, today.month, 1)

    monthly = (
        Transaction.objects.filter(date__gte=start_date)
        .annotate(month=TruncMonth('date'))
        .values('month', 'transaction_type')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('month', 'transaction_type')
    )

    result = [
        {
            'month': item['month'].strftime('%Y-%m'),
            'transaction_type': item['transaction_type'],
            'total': str(item['total']),
            'count': item['count'],
        }
        for item in monthly
    ]

    return JsonResponse({'monthly_trends': result, 'period': f'{start_date.strftime("%Y-%m")} to {today.strftime("%Y-%m")}'})


@csrf_exempt
@login_required_json
def recent_activity(request):
    """
    GET /api/dashboard/recent/
    Returns the most recent transactions.
    Optional query param: ?limit=10 (max 50)
    Accessible by all roles.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        limit = min(int(request.GET.get('limit', 10)), 50)
        if limit < 1:
            limit = 10
    except ValueError:
        return JsonResponse({'error': 'limit must be a positive integer'}, status=400)

    transactions = Transaction.objects.select_related('created_by').order_by('-created_at')[:limit]

    result = [
        {
            'id': t.id,
            'title': t.title,
            'amount': str(t.amount),
            'transaction_type': t.transaction_type,
            'category': t.category,
            'date': t.date.isoformat(),
            'created_by': t.created_by.username if t.created_by else None,
            'created_at': t.created_at,
        }
        for t in transactions
    ]

    return JsonResponse({'recent_activity': result, 'count': len(result)})
