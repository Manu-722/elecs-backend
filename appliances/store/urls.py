from django.urls import path
from .views import (
    landing,
    get_shoes,
    get_cart,
    add_to_cart,
    place_order,
    get_user_cart,
    persist_user_cart,
    get_wishlist,
    add_to_wishlist,
    remove_from_wishlist,
)

urlpatterns = [
    path('', landing),
    path('shoes/', get_shoes),
    path('cart/', get_cart),
    path('cart/add/', add_to_cart),
    path('order/place/', place_order),

    # 🔐 Cart persistence
    path('user/cart/', get_user_cart, name='get_user_cart'),
    path('persist_cart/', persist_user_cart, name='persist_user_cart'),

    # 💖 Wishlist endpoints
    path('wishlist/', get_wishlist),
    path('wishlist/add/', add_to_wishlist),
    path('wishlist/remove/<int:item_id>/', remove_from_wishlist),
    path('user/wishlist/', get_wishlist, name='get_user_wishlist'), 
]