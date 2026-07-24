from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import json

from .models import PaymentTransaction

User = get_user_model()


@csrf_exempt
def checkout_view(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
        print("Order received:", json.dumps(data, indent=2))

        # Log a payment transaction record
        user = request.user if request.user.is_authenticated else None
        PaymentTransaction.objects.create(
            user=user,
            phone=data.get('phone', ''),
            amount=data.get('total', 0),
            transaction_id=f"PAYBILL-{data.get('phone', 'unknown')}",
            checkout_request_id='paybill',
            result_code=0,
            result_description='Paybill 522522 — awaiting confirmation',
        )
        return JsonResponse({'message': 'Order received successfully'}, status=200)
    except Exception as e:
        print("Checkout Error:", str(e))
        return JsonResponse({'error': 'Invalid data'}, status=400)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class UserTransactionsView(View):
    def get(self, request):
        transactions = PaymentTransaction.objects.filter(user=request.user).order_by('-timestamp')
        data = [
            {
                'transaction_id': tx.transaction_id,
                'amount': tx.amount,
                'phone': tx.phone,
                'date': tx.timestamp.strftime('%Y-%m-%d %H:%M'),
                'status': 'Success' if tx.result_code == 0 else 'Failed',
            }
            for tx in transactions
        ]
        return JsonResponse({'transactions': data}, status=200)
