

# Create your views here.
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.utils import timezone

import json, requests, datetime, base64, stripe
from .models import PaymentTransaction, PasswordResetOTP
from .utils.daraja import get_access_token
from .utils.email_utils import generate_otp, send_reset_email

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY


def normalize_phone(phone):
    phone = str(phone).strip().replace(' ', '').replace('-', '')
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    elif phone.startswith('+254'):
        phone = phone[1:]
    elif phone.startswith('254'):
        phone = phone
    else:
        phone = '254' + phone
    
    # Validate phone number format
    if not phone.startswith('254') or len(phone) != 12:
        return None
    return phone


@csrf_exempt
def checkout_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Order received:", json.dumps(data, indent=2))
            return JsonResponse({'message': 'Order received successfully'}, status=200)
        except Exception as e:
            print("Checkout Error:", str(e))
            return JsonResponse({'error': 'Invalid data'}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def initiate_stk_push(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        body = json.loads(request.body)
        phone = normalize_phone(body.get('phone'))
        amount = int(body.get('amount'))

        if not phone:
            return JsonResponse({'error': 'Invalid phone number format. Use 07XXXXXXXX or 254XXXXXXXXX'}, status=400)
        if not amount or amount < 1:
            return JsonResponse({'error': 'Amount must be greater than 0'}, status=400)

        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        shortcode = settings.MPESA_SHORTCODE
        passkey = settings.MPESA_PASSKEY
        password = base64.b64encode(f'{shortcode}{passkey}{timestamp}'.encode()).decode()

        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": shortcode,
            "PhoneNumber": phone,
            "CallBackURL": "https://mydomain.com/api/payments/callback/",
            "AccountReference": "CymanOrder",
            "TransactionDesc": "Cyman Wear Payment"
        }

        token = get_access_token()
        if not token:
            return JsonResponse({'error': 'Failed to retrieve access token'}, status=500)

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
            json=payload,
            headers=headers,
            timeout=30
        )
        
        response_data = response.json()
        print(f"M-Pesa STK Response: {response_data}")
        
        # Check if request was successful
        if response.status_code == 200 and response_data.get('ResponseCode') == '0':
            return JsonResponse({
                'success': True,
                'message': 'STK push sent successfully',
                'CheckoutRequestID': response_data.get('CheckoutRequestID'),
                'MerchantRequestID': response_data.get('MerchantRequestID')
            })
        else:
            error_msg = response_data.get('ResponseDescription', 'STK push failed')
            return JsonResponse({
                'success': False,
                'error': error_msg,
                'ResponseCode': response_data.get('ResponseCode')
            }, status=400)

    except Exception as e:
        print("STK Push Error:", str(e))
        return JsonResponse({'error': 'Failed to initiate payment'}, status=500)


@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            print("M-Pesa Callback received:", json.dumps(body, indent=2))

            stk = body.get('Body', {}).get('stkCallback', {})
            result_code = stk.get('ResultCode')
            result_desc = stk.get('ResultDesc')
            checkout_request_id = stk.get('CheckoutRequestID')
            metadata = stk.get('CallbackMetadata', {}).get('Item', [])
            transaction_data = {item['Name']: item.get('Value') for item in metadata}

            phone = normalize_phone(transaction_data.get('PhoneNumber'))
            from users.models import Profile
            matched_user = Profile.get_user_by_phone(phone)

            PaymentTransaction.objects.create(
                user=matched_user,
                phone=phone,
                amount=transaction_data.get('Amount', 0),
                transaction_id=transaction_data.get('MpesaReceiptNumber') or f"FAILED-{checkout_request_id}",
                checkout_request_id=checkout_request_id,
                result_code=result_code,
                result_description=result_desc
            )

            if result_code == 0:
                return JsonResponse({'message': 'Payment successful'})
            else:
                return JsonResponse({'message': 'Payment failed', 'description': result_desc})

        except Exception as e:
            print("Callback Error:", str(e))
            return JsonResponse({'error': 'Invalid callback data'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class UserTransactionsView(View):
    def get(self, request):
        transactions = PaymentTransaction.objects.filter(user=request.user).order_by('-timestamp')
        data = [
            {
                "transaction_id": tx.transaction_id,
                "amount": tx.amount,
                "phone": tx.phone,
                "date": tx.timestamp.strftime('%Y-%m-%d %H:%M'),
                "status": "Success" if tx.result_code == 0 else "Failed"
            }
            for tx in transactions
        ]
        return JsonResponse({"transactions": data}, status=200)


@csrf_exempt
def create_payment_intent(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = int(data.get('amount', 0)) * 100

            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='kes',
                payment_method_types=["card"]
            )

            return JsonResponse({'clientSecret': intent.client_secret})
        except Exception as e:
            print("Stripe Error:", str(e))
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def request_password_reset(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            user = User.objects.filter(email=email).first()
            if not user:
                return JsonResponse({'error': 'User not found'}, status=404)

            if PasswordResetOTP.daily_count(user) >= 5:
                return JsonResponse({'error': 'Reset limit exceeded'}, status=429)

            otp = generate_otp()
            PasswordResetOTP.objects.create(user=user, otp_code=otp)

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"https://cymanwear.com/reset/{uid}/{token}/"

            send_reset_email(user, reset_url, otp)
            return JsonResponse({'message': 'Reset email sent'})
        except Exception as e:
            print("Reset Request Error:", str(e))
            return JsonResponse({'error': 'Failed to send email'}, status=500)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def confirm_password_reset(request, uidb64, token):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    try:
        data = json.loads(request.body)
        otp = data.get('otp')
        new_password = data.get('password')

        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

        if not default_token_generator.check_token(user, token):
            return JsonResponse({'error': 'Invalid or expired token'}, status=400)

        otp_entry = PasswordResetOTP.objects.filter(user=user, otp_code=otp, used=False).order_by('-created_at').first()
        if not otp_entry or otp_entry.is_expired():
            return JsonResponse({'error': 'Invalid or expired OTP'}, status=400)

        user.password = make_password(new_password)
        user.save()
        otp_entry.used = True
        otp_entry.save()

        return JsonResponse({'message': 'Password reset successful'})
    except Exception as e:
        print("Reset Confirm Error:", str(e))
        return JsonResponse({'error': 'Unable to reset password'}, status=500)


@csrf_exempt
def process_payment(request):
    return JsonResponse({'message': 'Process payment placeholder'})


@csrf_exempt
def create_payment(request):
    return JsonResponse({'message': 'Stripe simulation placeholder'})

@csrf_exempt
def confirm_card_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            intent_id = data.get('intent_id')
            amount = data.get('amount')

            if not intent_id or not amount:
                return JsonResponse({'error': 'Missing intent ID or amount'}, status=400)

            # Optionally fetch PaymentIntent from Stripe to verify status
            intent = stripe.PaymentIntent.retrieve(intent_id)

            if intent.status != 'succeeded':
                return JsonResponse({'error': 'Payment not successful'}, status=400)

            PaymentTransaction.objects.create(
                user=request.user if request.user.is_authenticated else None,
                phone='N/A',
                amount=amount,
                transaction_id=intent_id,
                checkout_request_id='card',
                result_code=0,
                result_description='Card payment confirmed via Stripe',
            )

            return JsonResponse({'message': 'Payment confirmed and logged'})
        except Exception as e:
            print("Card Payment Confirmation Error:", str(e))
            return JsonResponse({'error': 'Failed to confirm card payment'}, status=500)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
