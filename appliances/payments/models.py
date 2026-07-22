from django.db import models

# Create your models here.
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

# M-Pesa & Card Transaction Log
class PaymentTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True)
    checkout_request_id = models.CharField(max_length=100)
    result_code = models.IntegerField()
    result_description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user or 'Anonymous'} - {self.transaction_id}"

# Track Password Reset Attempts with OTP
class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.created_at + timezone.timedelta(minutes=15)

    @staticmethod
    def daily_count(user):
        today = timezone.now().date()
        return PasswordResetOTP.objects.filter(user=user, created_at__date=today).count()

    def __str__(self):
        return f"OTP for {self.user.email} - {'Used' if self.used else 'Unused'}"