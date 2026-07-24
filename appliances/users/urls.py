from django.urls import path
from .views import (
    register_user, login_user, get_user_profile,
    update_profile, change_password,
    forgot_password_request, forgot_password_confirm,
)

urlpatterns = [
    path('auth/register/', register_user),
    path('auth/login/', login_user),
    path('user-profile/', get_user_profile),
    path('auth/update-profile/', update_profile),
    path('auth/change-password/', change_password),
    path('auth/forgot-password/', forgot_password_request),
    path('auth/forgot-password/confirm/', forgot_password_confirm),
]
