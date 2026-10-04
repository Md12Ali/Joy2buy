"""Make the cart available to every template (for the navbar badge)."""
from django.conf import settings

from .cart import Cart


def cart(request):
    basket = Cart(request)
    return {
        "cart": basket,
        "cart_count": len(basket),
        "free_delivery_threshold": settings.FREE_DELIVERY_THRESHOLD,
    }
