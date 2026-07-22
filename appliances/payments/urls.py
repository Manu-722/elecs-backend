from django.urls import path
from . import views
from .views import UserTransactionsView, create_payment_intent

urlpatterns = [
    # M-Pesa endpoints
    path('checkout/', views.checkout_view, name='checkout'),
    path('initiate_stk_push/', views.initiate_stk_push, name='initiate_stk_push'),
    path('payments/callback/', views.mpesa_callback, name='mpesa_callback'),

    # Stripe integration
    path('create-payment-intent/', create_payment_intent, name='create-payment-intent'),

    # Placeholder endpoints (if still needed)
    path('process_payment/', views.process_payment, name='process-payment'),
    path('create_payment/', views.create_payment, name='create-payment'),

    # User transactions log
    path('user-transactions/', UserTransactionsView.as_view(), name='user-transactions'),
    # payments/urls.py

    path('request-password-reset/', views.request_password_reset, name='request-password-reset'),
]