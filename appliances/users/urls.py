from django.urls import path
from .views import (
    register_user,
    login_user,
    get_user_profile,
    RequestPasswordResetEmail,
    # reset_by_phone,
    reset_by_identifier,
)

urlpatterns = [
    path('auth/register/', register_user),
    path('auth/login/', login_user),
    path('user-profile/', get_user_profile),
    path('auth/request-password-reset/', RequestPasswordResetEmail.as_view(), name='request-password-reset'),
    # path('auth/reset-by-phone/', reset_by_phone, name='reset-by-phone'),
    path('auth/reset-identity/', reset_by_identifier, name='reset-by-identifier'),

]