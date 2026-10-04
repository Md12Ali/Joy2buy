"""
Session-based shopping cart.

The cart is stored in the visitor's session as ``{"<product id>": quantity}``
so that guests can shop before creating an account. Prices are never stored
in the session: they are always read fresh from the database, which means a
shopper cannot tamper with them and always sees the current price.
"""
from decimal import Decimal

from django.conf import settings

from products.models import Product


class Cart:
    """Wrapper around the cart dictionary kept in ``request.session``."""

    def __init__(self, request):
        self.session = request.session
        stored = self.session.get(settings.CART_SESSION_KEY)
        # Nothing is written here, so simply browsing never creates a
        # session row; the session is only saved once the cart changes.
        self.data = dict(stored) if isinstance(stored, dict) else {}
        self._lines = None

    # -- internal helpers --------------------------------------------------
    def _save(self):
        self.session[settings.CART_SESSION_KEY] = self.data
        self.session.modified = True
        self._lines = None

    @staticmethod
    def limit_for(product):
        """Largest quantity of ``product`` one cart line may hold."""
        return min(product.stock, settings.MAX_QUANTITY_PER_LINE)

    # -- changing the cart -------------------------------------------------
    def add(self, product, quantity=1, replace=False):
        """
        Add ``quantity`` of ``product``, or set it exactly when ``replace``.

        The quantity is capped at the available stock. Returns a tuple of
        (quantity now in the cart, True if the request had to be reduced).
        """
        key = str(product.pk)
        current = 0 if replace else int(self.data.get(key, 0))
        wanted = current + int(quantity)
        allowed = max(0, min(wanted, self.limit_for(product)))
        if allowed <= 0:
            self.data.pop(key, None)
        else:
            self.data[key] = allowed
        self._save()
        return allowed, allowed < wanted

    def remove(self, product_id):
        """Remove a line. Returns True if something was removed."""
        removed = self.data.pop(str(product_id), None) is not None
        if removed:
            self._save()
        return removed

    def clear(self):
        self.data = {}
        self._save()

    # -- reading the cart --------------------------------------------------
    def lines(self):
        """
        Return the cart lines as dictionaries, dropping anything that can
        no longer be bought and trimming quantities to the current stock.
        """
        if self._lines is not None:
            return self._lines

        ids = [int(key) for key in self.data if str(key).isdigit()]
        products = {
            product.pk: product
            for product in Product.objects.active()
            .filter(pk__in=ids)
            .select_related("category")
        }
        lines = []
        cleaned = {}
        for key, quantity in self.data.items():
            product = products.get(int(key)) if str(key).isdigit() else None
            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                continue
            if product is None or not product.in_stock or quantity < 1:
                continue
            quantity = min(quantity, self.limit_for(product))
            cleaned[str(product.pk)] = quantity
            lines.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "max_quantity": self.limit_for(product),
                    "line_total": product.price * quantity,
                }
            )
        if cleaned != self.data:
            self.data = cleaned
            self.session[settings.CART_SESSION_KEY] = cleaned
            self.session.modified = True
        self._lines = lines
        return lines

    def __iter__(self):
        return iter(self.lines())

    def __len__(self):
        """Total number of items (sum of all quantities)."""
        return sum(line["quantity"] for line in self.lines())

    def quantity_of(self, product):
        return int(self.data.get(str(product.pk), 0))

    @property
    def is_empty(self):
        return len(self) == 0

    @property
    def subtotal(self):
        return sum(
            (line["line_total"] for line in self.lines()), Decimal("0.00")
        )

    @property
    def delivery(self):
        """Delivery is free once the subtotal reaches the threshold."""
        subtotal = self.subtotal
        if subtotal == 0 or subtotal >= settings.FREE_DELIVERY_THRESHOLD:
            return Decimal("0.00")
        return settings.STANDARD_DELIVERY_COST

    @property
    def total(self):
        return self.subtotal + self.delivery

    @property
    def free_delivery_gap(self):
        """How much more to spend to qualify for free delivery."""
        gap = settings.FREE_DELIVERY_THRESHOLD - self.subtotal
        return max(gap, Decimal("0.00"))

    def summary(self):
        """Totals as plain strings, ready to send back as JSON."""
        symbol = settings.CURRENCY_SYMBOL
        return {
            "cart_count": len(self),
            "subtotal": f"{symbol}{self.subtotal:,.2f}",
            "delivery": (
                "Free" if self.delivery == 0
                else f"{symbol}{self.delivery:,.2f}"
            ),
            "total": f"{symbol}{self.total:,.2f}",
            "free_delivery_gap": f"{symbol}{self.free_delivery_gap:,.2f}",
            "qualifies_for_free_delivery": self.free_delivery_gap == 0,
        }
