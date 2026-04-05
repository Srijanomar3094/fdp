import json

from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .decorators import login_required_json, role_required
from .models import User


def _serialize_user(user):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role,
        'is_active': user.is_active,
        'date_joined': user.date_joined,
    }


@csrf_exempt
def login_view(request):
    """POST /api/auth/login/ — obtain a session cookie."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return JsonResponse({'error': 'username and password are required'}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

    if not user.is_active:
        return JsonResponse({'error': 'This account has been deactivated'}, status=403)

    login(request, user)
    return JsonResponse({'message': 'Login successful', 'user': _serialize_user(user)})


@csrf_exempt
@login_required_json
def logout_view(request):
    """POST /api/auth/logout/ — invalidate the session."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    logout(request)
    return JsonResponse({'message': 'Logout successful'})


@csrf_exempt
@login_required_json
def me_view(request):
    """GET /api/auth/me/ — return current authenticated user's profile."""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    return JsonResponse({'user': _serialize_user(request.user)})


@csrf_exempt
@role_required('admin')
def users_list(request):
    """
    GET  /api/users/ — list all users (admin only)
    POST /api/users/ — create a new user (admin only)
    """
    if request.method == 'GET':
        users = list(
            User.objects.all().values(
                'id', 'username', 'email', 'first_name', 'last_name',
                'role', 'is_active', 'date_joined',
            )
        )
        return JsonResponse({'users': users, 'count': len(users)})

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        errors = {}
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        role = data.get('role', User.VIEWER)
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()

        if not username:
            errors['username'] = 'This field is required'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'A user with this username already exists'

        if not email:
            errors['email'] = 'This field is required'
        elif User.objects.filter(email=email).exists():
            errors['email'] = 'A user with this email already exists'

        if not password:
            errors['password'] = 'This field is required'
        elif len(password) < 6:
            errors['password'] = 'Password must be at least 6 characters'

        if role not in [User.ADMIN, User.ANALYST, User.VIEWER]:
            errors['role'] = f'Invalid role. Choose from: admin, analyst, viewer'

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name,
        )
        return JsonResponse(
            {'message': 'User created successfully', 'user': _serialize_user(user)},
            status=201,
        )

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
@role_required('admin')
def user_detail(request, user_id):
    """
    GET    /api/users/<id>/ — get user (admin only)
    PUT    /api/users/<id>/ — update user (admin only)
    DELETE /api/users/<id>/ — soft delete / deactivate user (admin only)
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse({'user': _serialize_user(user)})

    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': 'Invalid JSON body'}, status=400)

        errors = {}

        if 'email' in data:
            email = data['email'].strip()
            if not email:
                errors['email'] = 'Email cannot be empty'
            elif User.objects.filter(email=email).exclude(id=user_id).exists():
                errors['email'] = 'A user with this email already exists'
            else:
                user.email = email

        if 'role' in data:
            if data['role'] not in [User.ADMIN, User.ANALYST, User.VIEWER]:
                errors['role'] = 'Invalid role. Choose from: admin, analyst, viewer'
            else:
                user.role = data['role']

        if 'first_name' in data:
            user.first_name = data['first_name'].strip()

        if 'last_name' in data:
            user.last_name = data['last_name'].strip()

        if 'is_active' in data:
            if not isinstance(data['is_active'], bool):
                errors['is_active'] = 'Must be a boolean'
            else:
                user.is_active = data['is_active']

        if 'password' in data:
            password = data['password'].strip()
            if password:
                if len(password) < 6:
                    errors['password'] = 'Password must be at least 6 characters'
                else:
                    user.set_password(password)

        if errors:
            return JsonResponse({'errors': errors}, status=400)

        user.save()
        return JsonResponse({'message': 'User updated successfully', 'user': _serialize_user(user)})

    if request.method == 'DELETE':
        if user.id == request.user.id:
            return JsonResponse({'error': 'You cannot deactivate your own account'}, status=400)
        user.soft_delete()
        return JsonResponse({'message': f'User "{user.username}" has been deactivated'})

    return JsonResponse({'error': 'Method not allowed'}, status=405)
