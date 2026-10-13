"""Checkout, order history and staff order management."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
    require_safe,
)

from cart.cart import Cart
from joy2buy.decorators import is_staff_member, staff_required
from products.models import Product
from profiles.models import get_profile

from .forms import CheckoutForm, OrderStatusForm
from .models import Order, OrderItem


class StockError(Exception):
    """Raised inside the checkout transaction when stock has run out."""


class StatusChangeError(Exception):
    """Raised when an order's current status does not allow a change."""

    def __init__(self, order, message):
        super().__init__(message)
        self.order = order


def _initial_delivery_details(user):
    """Pre-fill the checkout form from the customer's saved profile."""
    profile = get_profile(user)
    return {
        "full_name": user.get_full_name(),
        "email": user.email,
        "phone": profile.phone,
        "address_line1": profile.address_line1,
        "address_line2": profile.address_line2,
        "city": profile.city,
        "postcode": profile.postcode,
        "country": profile.country or "United Kingdom",
    }


def _place_order(user, cart, form):
    """
    Create the order, its lines and reduce stock - all or nothing.

    Product rows are locked for the length of the transaction so that two
    shoppers cannot both buy the last item in stock.
    """
    lines = cart.lines()
    with transaction.atomic():
        ids = [line["product"].pk for line in lines]
        locked = {
            product.pk: product
            for product in Product.objects.select_for_update().filter(
                pk__in=ids
            )
        }
        for line in lines:
            product = locked.get(line["product"].pk)
            if product is None or not product.is_purchasable:
                raise StockError(
                    f"{line['product'].name} is no longer available."
                )
            if product.stock < line["quantity"]:
                raise StockError(
                    f"Only {product.stock} of {product.name} left in "
                    "stock. Please update your cart."
                )

        order = form.save(commit=False)
        order.user = user
        order.save()
        for line in lines:
            product = locked[line["product"].pk]
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                unit_price=product.price,
                quantity=line["quantity"],
            )
            Product.objects.filter(pk=product.pk).update(
                stock=F("stock") - line["quantity"]
            )
        order.update_totals()
    return order


@login_required
@require_http_methods(["GET", "POST"])
def checkout(request):
    """Collect delivery details and turn the cart into an order."""
    cart = Cart(request)
    if cart.is_empty:
        messages.info(
            request, "Your cart is empty. Add something before checking out."
        )
        return redirect("products:product_list")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                order = _place_order(request.user, cart, form)
            except StockError as error:
                messages.error(request, str(error))
                return redirect("cart:cart_detail")

            if form.cleaned_data.get("save_details"):
                profile = get_profile(request.user)
                profile.update_from_order(order)
            cart.clear()
            messages.success(
                request,
                f"Order {order.transaction_id} placed. A summary is shown "
                "below.",
            )
            return redirect(order.get_absolute_url())
        messages.error(
            request,
            "Your order was not placed. Please fix the highlighted fields.",
        )
    else:
        form = CheckoutForm(initial=_initial_delivery_details(request.user))

    return render(request, "orders/checkout.html", {"form": form})


def _get_order_for(request, transaction_id):
    """Fetch an order, allowing only its owner or staff to see it."""
    order = get_object_or_404(
        Order.objects.prefetch_related("items__product"),
        transaction_id=transaction_id,
    )
    if order.user_id != request.user.pk and not is_staff_member(
        request.user
    ):
        raise PermissionDenied
    return order


@login_required
@require_safe
def order_detail(request, transaction_id):
    """Order confirmation and summary page."""
    order = _get_order_for(request, transaction_id)
    context = {"order": order}
    if is_staff_member(request.user):
        context["status_form"] = OrderStatusForm(instance=order)
    return render(request, "orders/order_detail.html", context)


def _change_status(order_pk, new_status, allowed_from=None):
    """
    Move an order to ``new_status``, returning stock if it is cancelled.

    The order row is locked with SELECT ... FOR UPDATE and its status is
    read again inside the transaction. Any other request for the same order
    waits here until this one commits, then sees the new status, so stock
    can never be returned twice and a cancelled order can never be reopened,
    however many requests arrive at once. ``allowed_from`` limits which
    statuses the change may start from.
    """
    cancelled = Order.Status.CANCELLED
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_pk)
        current = order.status
        if current == cancelled:
            raise StatusChangeError(
                order,
                f"Order {order.transaction_id} has already been cancelled "
                "and its items returned to stock, so it can no longer be "
                "changed.",
            )
        if allowed_from is not None and current not in allowed_from:
            raise StatusChangeError(
                order,
                "This order can no longer be cancelled because it is "
                f"{order.get_status_display().lower()}.",
            )
        if new_status == cancelled:
            order.restock()
        order.status = new_status
        order.save(update_fields=["status", "updated"])
    return order


@login_required
@require_POST
def order_cancel(request, transaction_id):
    """Let a customer cancel an order that has not been dispatched yet."""
    order = _get_order_for(request, transaction_id)
    try:
        order = _change_status(
            order.pk,
            Order.Status.CANCELLED,
            allowed_from={Order.Status.PENDING, Order.Status.PROCESSING},
        )
    except StatusChangeError as error:
        messages.error(request, str(error))
        return redirect(error.order.get_absolute_url())
    messages.success(
        request,
        f"Order {order.transaction_id} has been cancelled and the items "
        "returned to stock.",
    )
    return redirect(order.get_absolute_url())


@staff_required
@require_safe
def order_manage(request):
    """Staff list of every order, filterable by status."""
    orders = Order.objects.select_related("user").prefetch_related("items")
    status = request.GET.get("status", "")
    if status in Order.Status.values:
        orders = orders.filter(status=status)
    else:
        status = ""
    paginator = Paginator(orders, 20)
    context = {
        "page_obj": paginator.get_page(request.GET.get("page")),
        "status": status,
        "status_choices": Order.Status.choices,
    }
    return render(request, "orders/order_manage.html", context)


@staff_required
@require_POST
def order_status_update(request, transaction_id):
    """Staff action: move an order to a new status."""
    order = get_object_or_404(Order, transaction_id=transaction_id)
    form = OrderStatusForm(request.POST, instance=order)
    if not form.is_valid():
        messages.error(request, "Please choose a valid order status.")
        return redirect(order.get_absolute_url())

    try:
        order = _change_status(order.pk, form.cleaned_data["status"])
    except StatusChangeError as error:
        messages.error(request, str(error))
        return redirect(error.order.get_absolute_url())
    messages.success(
        request,
        f"Order {order.transaction_id} is now "
        f"{order.get_status_display().lower()}.",
    )
    return redirect(order.get_absolute_url())
