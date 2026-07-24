from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from .models import Product, CartItem, Order, Review, SlideItem, Offer
from users.models import Profile
import json, random, string
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes
from rest_framework import status


def landing(request):
    return HttpResponse("Welcome to Hawk Life Solutions API!")


def generate_hawk_code():
    return ''.join(random.choices(string.digits, k=4))


@api_view(['GET'])
@permission_classes([AllowAny])
def get_products(request):
    products = Product.objects.all().order_by('-created_at')
    data = [{
        'id': p.id,
        'name': p.name,
        'price': float(p.price),
        'image': str(p.image),
        'description': p.description,
        'in_stock': p.in_stock,
        'created_at': p.created_at.isoformat(),
        'category': p.category,
        'material': p.material,
        'wattage': p.wattage,
        'dimensions': p.dimensions,
        'weight': p.weight,
        'color': p.color,
        'warranty': p.warranty,
        'features': p.features,
        'is_offer': p.is_offer,
        'offer_price': float(p.offer_price) if p.offer_price else None,
        'updated_at': p.updated_at.isoformat(),
    } for p in products]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser])
def add_product(request):
    data = request.data
    image = request.FILES.get('image')
    if not image:
        return Response({'error': 'Image is required'}, status=status.HTTP_400_BAD_REQUEST)

    features_raw = data.get('features', '[]')
    try:
        features = json.loads(features_raw) if isinstance(features_raw, str) and features_raw.startswith('[') else [f.strip() for f in features_raw.split(',') if f.strip()]
    except Exception:
        features = []

    product = Product.objects.create(
        name=data.get('name', ''),
        price=data.get('price', 0),
        image=image,
        description=data.get('description', ''),
        in_stock=data.get('in_stock', 'true').lower() == 'true',
        category=data.get('category', 'Sufurias'),
        material=data.get('material', ''),
        wattage=data.get('wattage', ''),
        dimensions=data.get('dimensions', ''),
        weight=data.get('weight', ''),
        color=data.get('color', ''),
        warranty=data.get('warranty', ''),
        features=features,
        is_offer=data.get('is_offer', 'false').lower() == 'true',
        offer_price=data.get('offer_price') or None,
    )
    return Response({'message': 'Product added', 'id': product.id}, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser])
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    data = request.data

    for field in ['name', 'description', 'category', 'material', 'wattage', 'dimensions', 'weight', 'color', 'warranty']:
        if field in data:
            setattr(product, field, data[field])

    if 'price' in data:
        product.price = data['price']
    if 'offer_price' in data:
        product.offer_price = data['offer_price'] or None
    if 'is_offer' in data:
        product.is_offer = str(data['is_offer']).lower() == 'true'
    if 'in_stock' in data:
        product.in_stock = str(data['in_stock']).lower() == 'true'
    if 'features' in data:
        try:
            raw = data['features']
            product.features = json.loads(raw) if isinstance(raw, str) and raw.startswith('[') else [f.strip() for f in raw.split(',') if f.strip()]
        except Exception:
            pass
    if 'image' in request.FILES:
        product.image = request.FILES['image']

    product.save()
    return Response({'message': 'Product updated'})


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return Response({'message': 'Product deleted'})


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_get_orders(request):
    orders = Order.objects.select_related('user').all().order_by('-created_at')
    data = [{
        'id': o.id,
        'user': o.user.username,
        'email': o.user.email,
        'total': float(o.total),
        'payment_method': o.payment_method,
        'status': o.status,
        'paid': o.paid,
        'created_at': o.created_at.isoformat(),
        'address': o.address,
        'hawk_code': o.hawk_code,
        'phone': o.phone,
    } for o in orders]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def confirm_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = 'Confirmed'
    order.paid = True
    order.save()

    # Send thank-you email to customer
    try:
        send_mail(
            subject='🦅 Your Hawk Life Solutions Order is Confirmed!',
            message=f"""Dear {order.user.username},

Thank you for shopping with Hawk Life Solutions! 🦅

Your order #{order.id} (Code: {order.hawk_code}) has been confirmed and is being processed.

Order Total: KES {order.total}
Delivery Address: {order.address}

We will contact you shortly to arrange delivery.

Warm regards,
Hawk Life Solutions Team
📞 +254-745-792-950
📧 info@hawklifesolutions.com
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=True,
        )
    except Exception as e:
        print("Email error:", e)

    return Response({'message': 'Order confirmed and customer notified'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart(request):
    cart_items = CartItem.objects.filter(user=request.user)
    data = [{
        'id': item.id,
        'product': item.product.name,
        'image': str(item.product.image),
        'description': item.product.description,
        'quantity': item.quantity,
        'price': float(item.product.price),
        'discounted': float(item.discounted_price()),
        'total': float(item.total_price()),
    } for item in cart_items]
    return Response(data)


@csrf_exempt
@login_required
def add_to_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        item, created = CartItem.objects.get_or_create(user=request.user, product_id=product_id)
        if not created:
            item.quantity += quantity
        item.save()
        return JsonResponse({'message': 'Item added to cart'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def place_order(request):
    data = request.data
    address = data.get('address', '')
    payment_method = data.get('payment_method', 'mpesa_paybill')
    phone = data.get('phone', '')
    items = data.get('items', [])
    total = data.get('total', 0)

    if not items:
        return Response({'error': 'Cart is empty'}, status=400)

    hawk_code = generate_hawk_code()

    order = Order.objects.create(
        user=request.user,
        total=total,
        address=address,
        payment_method=payment_method,
        paid=False,
        status='Pending',
        hawk_code=hawk_code,
        phone=phone,
    )

    # Notify admins
    admin_emails = ['admin1@induction.com', 'admin2@induction.com']
    try:
        send_mail(
            subject=f'🦅 New Order #{order.id} — Code {hawk_code}',
            message=f"""New order received on Hawk Life Solutions.

Customer: {request.user.username} ({request.user.email})
Phone: {phone}
Hawk Code: {hawk_code}
Total: KES {total}
Address: {address}
Payment: {payment_method}

Please log in to the admin dashboard to confirm this order.
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=True,
        )
    except Exception as e:
        print("Admin email error:", e)

    return Response({'message': 'Order placed', 'order_id': order.id, 'hawk_code': hawk_code}, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_purchase_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    data = [{
        'id': o.id,
        'total': float(o.total),
        'status': o.status,
        'paid': o.paid,
        'payment_method': o.payment_method,
        'address': o.address,
        'hawk_code': o.hawk_code,
        'created_at': o.created_at.isoformat(),
    } for o in orders]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def persist_user_cart(request):
    cart_data = request.data
    if not isinstance(cart_data, list):
        return Response({'detail': 'Cart payload must be a list'}, status=400)
    if len(cart_data) > 50:
        return Response({'detail': 'Cart too large'}, status=400)

    valid_items = []
    for item in cart_data:
        if not isinstance(item, dict):
            continue
        if all(f in item for f in ['id', 'quantity']):
            valid_items.append({
                'id': item['id'],
                'product': item.get('product', item.get('name', '')),
                'image': item.get('image', ''),
                'description': item.get('description', ''),
                'quantity': item['quantity'],
                'price': float(item.get('price', 0)),
                'discounted': float(item.get('discounted', item.get('price', 0))),
            })

    profile, _ = Profile.objects.get_or_create(user=request.user)
    profile.cart_data = valid_items
    profile.save()
    return Response({'message': 'Cart saved successfully'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_cart(request):
    try:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        saved_cart = profile.cart_data if isinstance(profile.cart_data, list) else []
        normalized = [{
            'id': item.get('id'),
            'product': item.get('product', 'Unnamed'),
            'image': item.get('image', ''),
            'description': item.get('description', ''),
            'quantity': item.get('quantity', 1),
            'price': float(item.get('price', 0)),
            'discounted': float(item.get('discounted', item.get('price', 0))),
        } for item in saved_cart]
        return Response({'items': normalized})
    except Exception:
        return Response({'detail': 'Corrupt cart data'}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wishlist(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    wishlist = profile.wishlist if isinstance(profile.wishlist, list) else []
    return Response({'items': wishlist})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_wishlist(request):
    item = request.data
    profile, _ = Profile.objects.get_or_create(user=request.user)
    wishlist = profile.wishlist if isinstance(profile.wishlist, list) else []
    if item.get('id') and not any(w.get('id') == item['id'] for w in wishlist):
        wishlist.append(item)
    profile.wishlist = wishlist
    profile.save()
    return Response({'message': 'Added to wishlist'})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_wishlist(request, item_id):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    wishlist = profile.wishlist if isinstance(profile.wishlist, list) else []
    profile.wishlist = [i for i in wishlist if i.get('id') != item_id]
    profile.save()
    return Response({'message': 'Removed from wishlist'})


@api_view(['GET'])
@permission_classes([AllowAny])
def get_reviews(request, product_id):
    reviews = Review.objects.filter(product_id=product_id).select_related('user').order_by('-created_at')
    data = [{
        'id': r.id,
        'user': r.user.username,
        'rating': r.rating,
        'comment': r.comment,
        'created_at': r.created_at.isoformat(),
    } for r in reviews]
    avg = sum(r.rating for r in reviews) / len(reviews) if reviews else 0
    return Response({'reviews': data, 'average': round(avg, 1), 'count': len(data)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    rating = int(request.data.get('rating', 5))
    comment = request.data.get('comment', '').strip()
    if not comment:
        return Response({'error': 'Comment is required'}, status=400)
    if not (1 <= rating <= 5):
        return Response({'error': 'Rating must be between 1 and 5'}, status=400)
    review, created = Review.objects.update_or_create(
        product=product, user=request.user,
        defaults={'rating': rating, 'comment': comment}
    )
    return Response({'message': 'Review saved', 'created': created}, status=201)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return Response({'message': 'Review deleted'})


# ── SLIDESHOW ──────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def get_slides(request):
    slides = SlideItem.objects.filter(active=True)
    return Response([{
        'id': s.id, 'title': s.title, 'subtitle': s.subtitle,
        'image': str(s.image), 'price': float(s.price) if s.price else None,
        'badge': s.badge, 'order': s.order,
    } for s in slides])


@api_view(['POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser])
def add_slide(request):
    image = request.FILES.get('image')
    if not image:
        return Response({'error': 'Image required'}, status=400)
    s = SlideItem.objects.create(
        title=request.data.get('title', ''),
        subtitle=request.data.get('subtitle', ''),
        image=image,
        price=request.data.get('price') or None,
        badge=request.data.get('badge', ''),
        order=request.data.get('order', 0),
    )
    return Response({'id': s.id, 'message': 'Slide added'}, status=201)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_slide(request, slide_id):
    get_object_or_404(SlideItem, id=slide_id).delete()
    return Response({'message': 'Slide deleted'})


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def toggle_slide(request, slide_id):
    s = get_object_or_404(SlideItem, id=slide_id)
    s.active = not s.active
    s.save()
    return Response({'active': s.active})


# ── OFFERS ─────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([AllowAny])
def get_offers(request):
    offers = Offer.objects.filter(active=True)
    return Response([{
        'id': o.id, 'title': o.title, 'description': o.description,
        'image': str(o.image),
        'original_price': float(o.original_price) if o.original_price else None,
        'offer_price': float(o.offer_price) if o.offer_price else None,
        'badge': o.badge,
    } for o in offers])


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_get_offers(request):
    offers = Offer.objects.all()
    return Response([{
        'id': o.id, 'title': o.title, 'description': o.description,
        'image': str(o.image),
        'original_price': float(o.original_price) if o.original_price else None,
        'offer_price': float(o.offer_price) if o.offer_price else None,
        'badge': o.badge, 'active': o.active,
    } for o in offers])


@api_view(['POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser])
def add_offer(request):
    image = request.FILES.get('image')
    if not image:
        return Response({'error': 'Image required'}, status=400)
    o = Offer.objects.create(
        title=request.data.get('title', ''),
        description=request.data.get('description', ''),
        image=image,
        original_price=request.data.get('original_price') or None,
        offer_price=request.data.get('offer_price') or None,
        badge=request.data.get('badge', 'OFFER'),
    )
    return Response({'id': o.id, 'message': 'Offer added'}, status=201)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_offer(request, offer_id):
    get_object_or_404(Offer, id=offer_id).delete()
    return Response({'message': 'Offer deleted'})


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def toggle_offer(request, offer_id):
    o = get_object_or_404(Offer, id=offer_id)
    o.active = not o.active
    o.save()
    return Response({'active': o.active})


# ── ORDER CANCEL ───────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAdminUser])
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = 'Cancelled'
    order.save()
    return Response({'message': 'Order cancelled'})
