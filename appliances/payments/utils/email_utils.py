import random
import string
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_reset_email(user, reset_url, otp):
    """Send password reset email with OTP"""
    try:
        subject = "Reset your Cyman Wear password"
        message = f"""
Hi {user.username},

Your password reset OTP is: {otp}

Click the link below to reset your password:
{reset_url}

This OTP expires in 15 minutes.

Best regards,
Cyman Wear Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False