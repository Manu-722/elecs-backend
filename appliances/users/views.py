from django.shortcuts import render

# Create your views here.
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.tokens import RefreshToken
User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    data = request.data
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password:
        return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    if len(password) < 8:
        return Response({'error': 'Password must be at least 8 characters'}, status=status.HTTP_400_BAD_REQUEST)
    
    if len(username) < 3:
        return Response({'error': 'Username must be at least 3 characters'}, status=status.HTTP_400_BAD_REQUEST)

    if email:
        try:
            validate_email(email)
        except ValidationError:
            return Response({'error': 'Invalid email address'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, password=password, email=email)
    return Response({'message': 'User registered successfully'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    data = request.data
    username = data.get('username')
    password = data.get('password')

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)  # optional for session login

        
        refresh = RefreshToken.for_user(user)

        return Response({
            "token": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            "username": user.username,
            "email": user.email
        }, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    user = request.user
    return Response({
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
    }, status=status.HTTP_200_OK)


class RequestPasswordResetEmail(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User with that email does not exist."}, status=status.HTTP_404_NOT_FOUND)

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        reset_link = f"{frontend_url}/reset/{uidb64}/{token}/"

        send_mail(
            subject="Reset your Cyman Wear password",
            message=f"Click the link below to reset your password:\n\n{reset_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({"message": "Password reset link sent to email."}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_by_identifier(request):
    data = request.data
    identifier = data.get("identifier")  # previous username or email
    new_username = data.get("username")
    new_password = data.get("password")
    confirm_password = data.get("confirm_password")

    if not identifier or not new_username or not new_password or not confirm_password:
        return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

    if new_password != confirm_password:
        return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.filter(username=identifier).first()
        if not user:
            user = User.objects.filter(email=identifier).first()
        if not user:
            return Response({"error": "No matching user found."}, status=status.HTTP_404_NOT_FOUND)

        user.username = new_username
        user.set_password(new_password)
        user.save()

        try:
            send_mail(
                subject="Your Cyman Wear credentials were reset",
                message=f"Hi {new_username}, your username and password have been updated successfully.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            print("Email error:", e)

        return Response({"message": "Credentials updated. Email confirmation sent."}, status=status.HTTP_200_OK)

    except Exception as e:
        print("Reset error:", e)
        return Response({"error": "Something went wrong during reset."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)