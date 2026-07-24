from django.urls import path
from .views import checkout_view, UserTransactionsView

urlpatterns = [
    path('checkout/', checkout_view, name='checkout'),
    path('user-transactions/', UserTransactionsView.as_view(), name='user-transactions'),
]
