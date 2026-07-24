from django.urls import path
from .views import (
    landing, get_products, add_product, update_product, delete_product,
    admin_get_orders, confirm_order, cancel_order,
    get_cart, add_to_cart, place_order,
    get_user_cart, persist_user_cart,
    get_wishlist, add_to_wishlist, remove_from_wishlist,
    get_purchase_history,
    get_reviews, add_review, delete_review,
    get_slides, add_slide, delete_slide, toggle_slide,
    get_offers, admin_get_offers, add_offer, delete_offer, toggle_offer,
)

urlpatterns = [
    path('', landing),
    path('products/', get_products),

    # Admin — products
    path('admin/products/add/', add_product),
    path('admin/products/<int:product_id>/update/', update_product),
    path('admin/products/<int:product_id>/delete/', delete_product),

    # Admin — orders
    path('admin/orders/', admin_get_orders),
    path('admin/orders/<int:order_id>/confirm/', confirm_order),
    path('admin/orders/<int:order_id>/cancel/', cancel_order),

    # Admin — slides
    path('admin/slides/', add_slide),
    path('admin/slides/<int:slide_id>/delete/', delete_slide),
    path('admin/slides/<int:slide_id>/toggle/', toggle_slide),

    # Admin — offers
    path('admin/offers/', admin_get_offers),
    path('admin/offers/add/', add_offer),
    path('admin/offers/<int:offer_id>/delete/', delete_offer),
    path('admin/offers/<int:offer_id>/toggle/', toggle_offer),

    # Public
    path('slides/', get_slides),
    path('offers/', get_offers),

    # Orders
    path('orders/place/', place_order),
    path('orders/history/', get_purchase_history),

    # Cart
    path('cart/', get_cart),
    path('cart/add/', add_to_cart),
    path('user/cart/', get_user_cart),
    path('persist_cart/', persist_user_cart),

    # Wishlist
    path('wishlist/', get_wishlist),
    path('wishlist/add/', add_to_wishlist),
    path('wishlist/remove/<int:item_id>/', remove_from_wishlist),
    path('user/wishlist/', get_wishlist),

    # Reviews
    path('products/<int:product_id>/reviews/', get_reviews),
    path('products/<int:product_id>/reviews/add/', add_review),
    path('reviews/<int:review_id>/delete/', delete_review),
]
