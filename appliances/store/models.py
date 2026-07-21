from django.db import models

# Create your models here.
from django.contrib.auth.models import User

class Shoe(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.ImageField(upload_to='shoes/')
    description = models.TextField(blank=True)
    in_stock = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    CATEGORY_CHOICES = [
        ('Sneakers', 'Sneakers'),
        ('Boots', 'Boots'),
        ('Sandals', 'Sandals'),
        ('Loafers', 'Loafers'),
        ('Formal', 'Formal'),
        ('Heels', 'Heels'),  
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Sneakers')

    SECTION_CHOICES = [  
        ('Men', 'Men'),
        ('Ladies', 'Ladies'),
        ('Kids', 'Kids'),
    ]
    section = models.CharField(max_length=20, choices=SECTION_CHOICES, default='Men')

    sizes = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.name


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    shoe = models.ForeignKey(Shoe, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return self.shoe.price * self.quantity

    def discounted_price(self):
        return self.total_price() * 0.93 if self.quantity >= 2 else self.total_price()

    def __str__(self):
        return f"{self.quantity} × {self.shoe.name} for {self.user.username}"


class Order(models.Model):
    PAYMENT_CHOICES = [
        ('mpesa', 'M-Pesa'),
        ('card', 'Card'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(CartItem)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.TextField()
    payment_method = models.CharField(max_length=10, choices=PAYMENT_CHOICES)
    status = models.CharField(max_length=20, default='Pending')
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"