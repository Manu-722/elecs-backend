from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cart_data = models.JSONField(default=list, blank=True)
    wishlist = models.JSONField(default=list, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.user.username
    
    @classmethod
    def get_user_by_phone(cls, phone):
        """Helper method to find user by phone number"""
        try:
            profile = cls.objects.get(phone=phone)
            return profile.user
        except cls.DoesNotExist:
            return None