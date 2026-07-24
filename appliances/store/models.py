from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Sufurias & Cookware', 'Sufurias & Cookware'),
        ('Non-Stick Pans', 'Non-Stick Pans'),
        ('Induction Cookers', 'Induction Cookers'),
        ('Offers', 'Offers'),
    ]

    name = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    description = models.TextField(blank=True)
    in_stock = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='Sufurias')
    material = models.CharField(max_length=100, blank=True, default='')
    wattage = models.CharField(max_length=50, blank=True, default='')
    dimensions = models.CharField(max_length=100, blank=True, default='')
    weight = models.CharField(max_length=50, blank=True, default='')
    color = models.CharField(max_length=50, blank=True, default='')
    warranty = models.CharField(max_length=100, blank=True, default='')
    features = models.JSONField(default=list, blank=True)
    is_offer = models.BooleanField(default=False)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return self.product.price * self.quantity

    def discounted_price(self):
        return self.total_price() * 0.93 if self.quantity >= 2 else self.total_price()

    def __str__(self):
        return f"{self.quantity} × {self.product.name} for {self.user.username}"


class Order(models.Model):
    PAYMENT_CHOICES = [
        ('mpesa_paybill', 'M-Pesa Paybill'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    items = models.ManyToManyField(CartItem, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.TextField()
    phone = models.CharField(max_length=20, blank=True, default='')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='mpesa_paybill')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    paid = models.BooleanField(default=False)
    hawk_code = models.CharField(max_length=4, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} [{self.hawk_code}] by {self.user.username}"


class SlideItem(models.Model):
    title = models.CharField(max_length=150)
    subtitle = models.TextField(blank=True)
    image = models.ImageField(upload_to='slides/')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    badge = models.CharField(max_length=60, blank=True)
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title


class Offer(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='offers/')
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    badge = models.CharField(max_length=60, blank=True, default='OFFER')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5)  # 1-5
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')

    def __str__(self):
        return f"{self.user.username} — {self.product.name} ({self.rating}★)"
