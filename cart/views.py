"""
Shopping cart views.

Every view that changes the cart accepts POST only and answers in two ways:
a JSON payload for JavaScript (``fetch``) requests, so the page can update
without reloading, or a redirect with a Django message when JavaScript is
unavailable.
"""
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST, require_safe

from products.models import Product

from .cart import Cart
from .forms import CartQuantityForm

LEVELS = {
    "success": messages.SUCCESS,
    "warning": messages.WARNING,
    "danger": messages.ERROR,
    "info": messages.INFO,
}


def _wants_json(request):
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _safe_next(request, fallback="cart:cart_detail"):
    """Only redirect to a "next" address on this site (no open redirects)."""
    target = request.POST.get("next", "")
    if target and url_has_allowed_host_and_scheme(
        target,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return target
    return fallback


def _respond(request, cart, ok, level, text, status=200, extra=None):
    """Answer with JSON or with a message + redirect, as appropriate."""
    if _wants_json(request):
        payload = {"ok": ok, "level": level, "message": text}
        payload.update(cart.summary())
        payload.update(extra or {})
        return JsonResponse(payload, status=status)
    messages.add_message(request, LEVELS[level], text)
    return redirect(_safe_next(request))


@require_safe
def cart_detail(request):
    """Show the cart (supplied to the template by the context processor)."""
    return render(request, "cart/cart.html")


@require_POST
def cart_add(request, product_id):
    """Add a product to the cart (from a product card or detail page)."""
    cart = Cart(request)
    product = get_object_or_404(Product.objects.active(), pk=product_id)

    form = CartQuantityForm({"quantity": request.POST.get("quantity", "1")})
    if not form.is_valid():
        error = form.errors["quantity"][0]
        return _respond(request, cart, False, "danger", error, status=400)
    if not product.in_stock:
        return _respond(
            request,
            cart,
            False,
            "danger",
            f"Sorry, {product.name} is out of stock.",
            status=400,
        )

    quantity, reduced = cart.add(product, form.cleaned_data["quantity"])
    if reduced:
        level = "warning"
        text = (
            f"Only {quantity} of {product.name} can be added, so your cart "
            f"now holds {quantity}."
        )
    else:
        level = "success"
        text = f"{product.name} was added to your cart."
    return _respond(request, cart, True, level, text)


@require_POST
def cart_update(request, product_id):
    """Change the quantity of a line already in the cart."""
    cart = Cart(request)
    product = get_object_or_404(Product.objects.active(), pk=product_id)

    if cart.quantity_of(product) == 0:
        return _respond(
            request,
            cart,
            False,
            "danger",
            f"{product.name} is not in your cart.",
            status=400,
        )

    form = CartQuantityForm({"quantity": request.POST.get("quantity")})
    if not form.is_valid():
        error = form.errors["quantity"][0]
        return _respond(request, cart, False, "danger", error, status=400)

    quantity, reduced = cart.add(
        product, form.cleaned_data["quantity"], replace=True
    )
    if quantity == 0:
        level = "warning"
        text = f"{product.name} sold out and was removed from your cart."
    elif reduced:
        level = "warning"
        text = f"Only {quantity} of {product.name} are available."
    else:
        level = "success"
        text = f"{product.name} quantity updated to {quantity}."
    extra = {
        "quantity": quantity,
        "line_total": (
            f"{settings.CURRENCY_SYMBOL}{product.price * quantity:,.2f}"
        ),
    }
    return _respond(request, cart, True, level, text, extra=extra)


@require_POST
def cart_remove(request, product_id):
    """Remove a line from the cart."""
    cart = Cart(request)
    product = Product.objects.filter(pk=product_id).first()
    name = product.name if product else "The item"
    if cart.remove(product_id):
        return _respond(
            request, cart, True, "success",
            f"{name} was removed from your cart.",
        )
    return _respond(
        request, cart, False, "warning",
        f"{name} was not in your cart.", status=404,
    )
