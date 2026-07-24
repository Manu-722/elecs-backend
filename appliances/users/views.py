import random, string
from django.contrib.auth import authenticate, login, get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Profile

User = get_user_model()

ADMIN_EMAILS = ['admin1@induction.com', 'admin2@induction.com']


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    data = request.data
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return Response({'error': 'Email and password are required'}, status=400)
    try:
        validate_email(email)
    except ValidationError:
        return Response({'error': 'Invalid email address'}, status=400)
    if len(password) < 6:
        return Response({'error': 'Password must be at least 6 characters'}, status=400)
    if User.objects.filter(email__iexact=email).exists():
        return Response({'error': 'Email already registered'}, status=400)

    username = email.split('@')[0]
    base = username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base}{counter}"
        counter += 1

    User.objects.create_user(username=username, email=email, password=password)
    return Response({'message': 'Account created successfully'}, status=201)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password', '')

    if not email or not password:
        return Response({'error': 'Email and password are required'}, status=400)

    try:
        user_obj = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return Response({'error': 'Invalid credentials'}, status=401)

    user = authenticate(request, username=user_obj.username, password=password)
    if user is None:
        return Response({'error': 'Invalid credentials'}, status=401)

    login(request, user)
    refresh = RefreshToken.for_user(user)
    is_admin = email in ADMIN_EMAILS

    profile, _ = Profile.objects.get_or_create(user=user)
    avatar_url = request.build_absolute_uri(profile.avatar.url) if profile.avatar else None

    return Response({
        'token': {'access': str(refresh.access_token), 'refresh': str(refresh)},
        'username': user.username,
        'email': user.email,
        'is_admin': is_admin,
        'avatar': avatar_url,
    }, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    user = request.user
    is_admin = user.email.lower() in ADMIN_EMAILS
    profile, _ = Profile.objects.get_or_create(user=user)
    avatar_url = request.build_absolute_uri(profile.avatar.url) if profile.avatar else None
    return Response({
        'username': user.username,
        'email': user.email,
        'is_admin': is_admin,
        'avatar': avatar_url,
    }, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_profile(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)
    if 'avatar' in request.FILES:
        profile.avatar = request.FILES['avatar']
        profile.save()
    if 'username' in request.data:
        new_username = request.data['username'].strip()
        if new_username and new_username != user.username:
            if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                return Response({'error': 'Username already taken'}, status=400)
            user.username = new_username
            user.save()
    avatar_url = request.build_absolute_uri(profile.avatar.url) if profile.avatar else None
    return Response({'message': 'Profile updated', 'username': user.username, 'avatar': avatar_url})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    old_password = request.data.get('old_password', '')
    new_password = request.data.get('new_password', '')
    if not old_password or not new_password:
        return Response({'error': 'Both fields are required'}, status=400)
    if not request.user.check_password(old_password):
        return Response({'error': 'Current password is incorrect'}, status=400)
    if len(new_password) < 6:
        return Response({'error': 'Password must be at least 6 characters'}, status=400)
    request.user.set_password(new_password)
    request.user.save()
    return Response({'message': 'Password updated successfully'})


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_request(request):
    email = request.data.get('email', '').strip().lower()
    if not email:
        return Response({'error': 'Email is required'}, status=400)
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        # Don't reveal if email exists
        return Response({'message': 'If that email exists, a reset code has been sent.'})

    code = ''.join(random.choices(string.digits, k=6))
    profile, _ = Profile.objects.get_or_create(user=user)
    profile.reset_code = code
    profile.save()

    try:
        send_mail(
            subject='Hawk Life Solutions — Password Reset Code',
            message=f"""Hello {user.username},

You requested a password reset for your Hawk Life Solutions account.

Your reset code is:

    {code}

Enter this code on the reset page to set a new password.
This code expires in 15 minutes.

If you did not request this, please ignore this email.

— Hawk Life Solutions
no-reply@hawklifesolutions.com
""",
            from_email='no-reply@hawklifesolutions.com',
            recipient_list=[email],
            fail_silently=False,
        )
    except Exception as e:
        print("Reset email error:", e)

    return Response({'message': 'If that email exists, a reset code has been sent.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_confirm(request):
    email = request.data.get('email', '').strip().lower()
    code = request.data.get('code', '').strip()
    new_password = request.data.get('new_password', '')
    confirm_password = request.data.get('confirm_password', '')

    if not all([email, code, new_password, confirm_password]):
        return Response({'error': 'All fields are required'}, status=400)
    if new_password != confirm_password:
        return Response({'error': 'Passwords do not match'}, status=400)
    if len(new_password) < 6:
        return Response({'error': 'Password must be at least 6 characters'}, status=400)

    try:
        user = User.objects.get(email__iexact=email)
        profile = Profile.objects.get(user=user)
    except (User.DoesNotExist, Profile.DoesNotExist):
        return Response({'error': 'Invalid email or code'}, status=400)

    if profile.reset_code != code:
        return Response({'error': 'Invalid or expired reset code'}, status=400)

    user.set_password(new_password)
    user.save()
    profile.reset_code = ''
    profile.save()

    return Response({'message': 'Password reset successfully. You can now log in.'})
