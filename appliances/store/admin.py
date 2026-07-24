from django.contrib import admin
from .models import Product, CartItem, Order
from django.utils.html import format_html


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'in_stock', 'created_at', 'image_preview']
    search_fields = ['name', 'category']
    list_filter = ['in_stock', 'category']
    fields = ['name', 'price', 'category', 'material', 'wattage', 'dimensions',
              'weight', 'color', 'warranty', 'features', 'image', 'description', 'in_stock', 'created_at']
    readonly_fields = ['created_at', 'image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" style="object-fit:cover;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = "Image"


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'quantity', 'added_at']
    list_filter = ['added_at']
    search_fields = ['user__username', 'product__name']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total', 'payment_method', 'paid', 'status', 'created_at']
    list_filter = ['payment_method', 'paid', 'status']
    search_fields = ['user__username']
    readonly_fields = ['total', 'created_at']
