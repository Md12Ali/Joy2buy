"""Order models: an order and the individual lines that make it up."""
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse

from products.models import Product


def generate_transaction_id():
    """Return a unique, hard-to-guess 16 character order reference."""
    return uuid.uuid4().hex[:16].upper()


class Order(models.Model):
    """A completed checkout belonging to one customer."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="orders",
    )
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.PENDING,
    )
    transaction_id = models.CharField(
        max_length=32,
        unique=True,
        editable=False,
        default=generate_transaction_id,
    )

    # Delivery details are copied onto the order so that later changes to
    # the customer's profile never rewrite where a past order was sent.
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address_line1 = models.CharField("address line 1", max_length=120)
    address_line2 = models.CharField(
        "address line 2", max_length=120, blank=True
    )
    city = models.CharField("town or city", max_length=60)
    postcode = models.CharField(max_length=12)
    country = models.CharField(max_length=60, default="United Kingdom")

    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    delivery_cost = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal("0.00")
    )
    total = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"Order {self.transaction_id}"

    def get_absolute_url(self):
        return reverse("orders:order_detail", args=[self.transaction_id])

    @property
    def shipping_address(self):
        """The delivery address as a single comma-separated line."""
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.postcode,
            self.country,
        ]
        return ", ".join(part for part in parts if part)

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def can_be_cancelled(self):
        """Customers may cancel until the order has been dispatched."""
        return self.status in {self.Status.PENDING, self.Status.PROCESSING}

    @property
    def status_colour(self):
        """Bootstrap colour name used for the status badge."""
        return {
            self.Status.PENDING: "warning",
            self.Status.PROCESSING: "info",
            self.Status.SHIPPED: "primary",
            self.Status.DELIVERED: "success",
            self.Status.CANCELLED: "secondary",
        }.get(self.status, "secondary")

    def update_totals(self, save=True):
        """Recalculate subtotal, delivery and total from the order lines."""
        subtotal = sum(
            (item.line_total for item in self.items.all()), Decimal("0.00")
        )
        if subtotal == 0 or subtotal >= settings.FREE_DELIVERY_THRESHOLD:
            delivery = Decimal("0.00")
        else:
            delivery = settings.STANDARD_DELIVERY_COST
        self.subtotal = subtotal
        self.delivery_cost = delivery
        self.total = subtotal + delivery
        if save:
            self.save(update_fields=[
                "subtotal", "delivery_cost", "total", "updated",
            ])
        return self.total

    def restock(self):
        """Return every line's quantity to stock (used on cancellation)."""
        for item in self.items.select_related("product"):
            if item.product_id:
                Product.objects.filter(pk=item.product_id).update(
                    stock=models.F("stock") + item.quantity
                )


class OrderItem(models.Model):
    """One product line within an order."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    # The product may later be deleted from the catalogue, so its name and
    # price at the time of purchase are stored on the line itself.
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
    )
    product_name = models.CharField(max_length=120)
    unit_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    quantity = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity
