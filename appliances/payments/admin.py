from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import PaymentTransaction

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'phone', 'amount', 'result_code', 'timestamp')
    search_fields = ('transaction_id', 'phone')
    list_filter = ('result_code',)