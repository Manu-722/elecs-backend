from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cart_data = models.JSONField(default=list, blank=True)
    wishlist = models.JSONField(default=list, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    reset_code = models.CharField(max_length=6, blank=True, default='')

    def __str__(self):
        return self.user.username

    @classmethod
    def get_user_by_phone(cls, phone):
        try:
            return cls.objects.get(phone=phone).user
        except cls.DoesNotExist:
            return None
