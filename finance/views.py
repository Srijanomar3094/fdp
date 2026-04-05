import json
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from users.decorators import login_required_json
from .models import Transaction


def _serialize_transaction(t):
    return {
        'id': t.id,
        'title': t.title,
        'amount': str(t.amount),
        'transaction_type': t.transaction_type,
        'category': t.category,
        'date': t.date.isoformat(),
        'notes': t.notes,
        'created_by': t.created_by.username if t.created_by else None,
        'created_at': t.created_at,
        'updated_at': t.updated_at,
    }


def _parse_date(date_str, field_name='date'):
    """Parse a YYYY-MM-DD string. Returns (date, error_str)."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date(), None
    except ValueError:
        return None, f'{field_name}: Invalid date format. Use YYYY-MM-DD'


@csrf_exempt
@login_required_json
def transactions_list(request):
    """
    GET  /api/finance/transactions/ — list transactions (all roles)
        Query params: type, category, start_date, end_date, search, page, per_page
    POST /api/finance/transactions/ — create transaction (admin, analyst)
    """
    if request.method == 'GET':
        qs = Transaction.objects.select_related('created_by')

        # --- filters ---
        txn_type = request.GET.get('type')
        if txn_type in [Transaction.INCOME, Transaction.EXPENSE]:
            qs = qs.filter(transaction_type=txn_type)

        category = request.GET.get('category')
        if category:
            if category not in Transaction.VALID_CATEGORIES:
                return JsonResponse(
                    {'error': f'Invalid category. Valid options: {Transaction.VALID_CATEGORIES}'},
                    status=400,
                )
            qs = qs.filter(category=category)

        start_date = request.GET.get('start_date')
        if start_date:
            d, err = _parse_date(start_date, 'start_date')
            if err:
                return JsonResponse({'error': err}, status=400)
            qs = qs.filter(date__gte=d)

        end_date = request.GET.get('end_date')
        if end_date:
            d, err = _parse_date(end_date, 'end_date')
            if err:
                return JsonResponse({'error': err}, status=400)
            qs = qs.filter(date__lte=d)

        search = request.GET.get('search', '').strip()
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(notes__icontains=search))

        # --- pagination ---
        try:
            page = max(int(request.GET.get('page', 1)), 1)
            per_page = min(int(request.GET.get('per_page', 20)), 100)
        except ValueError:
            return JsonResponse({'error': 'page and per_page must be integers'}, status=400)

        total = qs.count()
        offset = (page - 1) * per_page
        transactions = [_serialize_transaction(t) for t in qs[offset: offset + per_page]]

        return JsonResponse({
            'transactions': transactions,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total,
                'total_pages': max(1, -(-total // per_page)),  # ceiling division
            },
        })

    if request.method == 'POST':
        if request.user.role not in ['admin', 'analyst']:
            return JsonResponse(
                {'error': 'Only admin and analyst roles can create transactions', 'code': 'FORBIDDEN'},
                status=403,
            )

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        errors = {}

        title = data.get('title', '').strip()
        if not title:
            errors['title'] = 'This field is required'

        raw_amount = data.get('amount')
        amount = None
        if raw_amount is None:
            errors['amount'] = 'This field is required'
        else:
            try:
                amount = Decimal(str(raw_amount))
                if amount <= 0:
                    errors['amount'] = 'Amount must be a positive number'
            except InvalidOperation:
                errors['amount'] = 'Invalid amount value'

        txn_type = data.get('transaction_type', '').strip()
        if txn_type not in [Transaction.INCOME, Transaction.EXPENSE]:
            errors['transaction_type'] = 'Must be "income" or "expense"'

        category = data.get('category', '').strip()
        if category not in Transaction.VALID_CATEGORIES:
            errors['category'] = f'Invalid category. Valid options: {Transaction.VALID_CATEGORIES}'

        date_str = data.get('date', '').strip()
        txn_date = None
        if not date_str:
            errors['date'] = 'This field is required'
        else:
            txn_date, err = _parse_date(date_str)
            if err:
                errors['date'] = 'Invalid date format. Use YYYY-MM-DD'

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        transaction = Transaction.objects.create(
            title=title,
            amount=amount,
            transaction_type=txn_type,
            category=category,
            date=txn_date,
            notes=data.get('notes', ''),
            created_by=request.user,
        )
        return JsonResponse(
            {'message': 'Transaction created successfully', 'transaction': _serialize_transaction(transaction)},
            status=201,
        )

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@login_required_json
def transaction_detail(request, transaction_id):
    """
    GET    /api/finance/transactions/<id>/ — get transaction (all roles)
    PUT    /api/finance/transactions/<id>/ — update transaction (admin, analyst)
    DELETE /api/finance/transactions/<id>/ — soft delete transaction (admin only)
    """
    try:
        transaction = Transaction.objects.select_related('created_by').get(id=transaction_id)
    except Transaction.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'transaction': _serialize_transaction(transaction)})

    if request.method == 'PUT':
        if request.user.role not in ['admin', 'analyst']:
            return JsonResponse(
                {'error': 'Only admin and analyst roles can update transactions', 'code': 'FORBIDDEN'},
                status=403,
            )

        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        errors = {}

        if 'title' in data:
            title = data['title'].strip()
            if not title:
                errors['title'] = 'Title cannot be empty'
            else:
                transaction.title = title

        if 'amount' in data:
            try:
                amount = Decimal(str(data['amount']))
                if amount <= 0:
                    errors['amount'] = 'Amount must be a positive number'
                else:
                    transaction.amount = amount
            except InvalidOperation:
                errors['amount'] = 'Invalid amount value'

        if 'transaction_type' in data:
            if data['transaction_type'] not in [Transaction.INCOME, Transaction.EXPENSE]:
                errors['transaction_type'] = 'Must be "income" or "expense"'
            else:
                transaction.transaction_type = data['transaction_type']

        if 'category' in data:
            if data['category'] not in Transaction.VALID_CATEGORIES:
                errors['category'] = f'Invalid category. Valid options: {Transaction.VALID_CATEGORIES}'
            else:
                transaction.category = data['category']

        if 'date' in data:
            d, err = _parse_date(data['date'])
            if err:
                errors['date'] = 'Invalid date format. Use YYYY-MM-DD'
            else:
                transaction.date = d

        if 'notes' in data:
            transaction.notes = data['notes']

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        transaction.save()
        return JsonResponse({
            'message': 'Transaction updated successfully',
            'transaction': _serialize_transaction(transaction),
        })

    if request.method == 'DELETE':
        if request.user.role != 'admin':
            return JsonResponse(
                {'error': 'Only admins can delete transactions', 'code': 'FORBIDDEN'},
                status=403,
            )
        transaction.soft_delete()
        return JsonResponse({'message': f'Transaction "{transaction.title}" has been deleted'})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@login_required_json
def categories_list(request):
    """GET /api/finance/categories/ — return valid categories and types."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    return JsonResponse({
        'categories': [{'value': v, 'label': l} for v, l in Transaction.CATEGORY_CHOICES],
        'transaction_types': [{'value': v, 'label': l} for v, l in Transaction.TYPE_CHOICES],
    })
