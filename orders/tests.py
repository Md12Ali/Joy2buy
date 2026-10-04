"""Tests for checkout, order history and staff order management."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from products.models import Category, Product

from .forms import CheckoutForm
from .models import Order, OrderItem
from .views import StockError, _place_order

User = get_user_model()

DELIVERY = {
    "full_name": "Sam Taylor",
    "email": "sam@example.com",
    "phone": "07700 900123",
    "address_line1": "12 Market Street",
    "address_line2": "",
    "city": "Leeds",
    "postcode": "ls1 4ap",
    "country": "United Kingdom",
    "save_details": "on",
}


class OrderTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name="Travel")
        cls.backpack = Product.objects.create(
            category=cls.category,
            name="Commuter Backpack",
            description="A water-resistant backpack for a 16 inch laptop.",
            price=Decimal("54.99"),
            stock=3,
        )
        cls.adapter = Product.objects.create(
            category=cls.category,
            name="Travel Adapter",
            description="One adapter covering sockets in 150 countries.",
            price=Decimal("22.50"),
            stock=10,
        )
        cls.customer = User.objects.create_user(
            username="sam", email="sam@example.com", password="Str0ng-pass!"
        )
        cls.other_customer = User.objects.create_user(
            username="alex", email="alex@example.com", password="Str0ng-pass!"
        )
        cls.staff = User.objects.create_user(
            username="manager", password="Str0ng-pass!", is_staff=True
        )

    def fill_cart(self, product, quantity=1):
        self.client.post(
            reverse("cart:cart_add", args=[product.pk]),
            {"quantity": quantity},
        )

    def place_order(self, product=None, quantity=1):
        """Log in as the customer, buy something, return the order."""
        self.client.force_login(self.customer)
        self.fill_cart(product or self.adapter, quantity)
        self.client.post(reverse("orders:checkout"), DELIVERY)
        return Order.objects.latest("created")


class OrderModelTests(OrderTestCase):
    def make_order(self):
        order = Order.objects.create(
            user=self.customer,
            full_name="Sam Taylor",
            email="sam@example.com",
            phone="07700 900123",
            address_line1="12 Market Street",
            city="Leeds",
            postcode="LS1 4AP",
        )
        OrderItem.objects.create(
            order=order,
            product=self.adapter,
            product_name=self.adapter.name,
            unit_price=self.adapter.price,
            quantity=2,
        )
        return order

    def test_transaction_id_is_generated_and_unique(self):
        first = self.make_order()
        second = self.make_order()
        self.assertEqual(len(first.transaction_id), 16)
        self.assertNotEqual(first.transaction_id, second.transaction_id)
        self.assertEqual(str(first), f"Order {first.transaction_id}")

    def test_totals_add_delivery_below_threshold(self):
        order = self.make_order()
        order.update_totals()
        self.assertEqual(order.subtotal, Decimal("45.00"))
        self.assertEqual(order.delivery_cost, Decimal("4.99"))
        self.assertEqual(order.total, Decimal("49.99"))

    def test_relationships_and_helpers(self):
        order = self.make_order()
        item = order.items.get()
        self.assertEqual(item.line_total, Decimal("45.00"))
        self.assertEqual(str(item), "2 x Travel Adapter")
        self.assertEqual(order.item_count, 2)
        self.assertIn(order, self.customer.orders.all())
        self.assertEqual(
            order.shipping_address,
            "12 Market Street, Leeds, LS1 4AP, United Kingdom",
        )

    def test_order_line_survives_product_deletion(self):
        order = self.make_order()
        self.adapter.delete()
        item = order.items.get()
        self.assertIsNone(item.product)
        self.assertEqual(item.product_name, "Travel Adapter")
        self.assertEqual(item.unit_price, Decimal("22.50"))


class CheckoutFormTests(TestCase):
    def test_valid_details_are_normalised(self):
        form = CheckoutForm(data=DELIVERY)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["postcode"], "LS1 4AP")

    def test_bad_phone_postcode_and_email_are_rejected(self):
        data = dict(DELIVERY, phone="call me", postcode="!!", email="nope")
        form = CheckoutForm(data=data)
        self.assertFalse(form.is_valid())
        for field in ("phone", "postcode", "email"):
            self.assertIn(field, form.errors)

    def test_required_fields(self):
        form = CheckoutForm(data={})
        self.assertFalse(form.is_valid())
        for field in ("full_name", "email", "phone", "address_line1",
                      "city", "postcode"):
            self.assertIn(field, form.errors)


class CheckoutViewTests(OrderTestCase):
    def test_checkout_requires_login(self):
        response = self.client.get(reverse("orders:checkout"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_empty_cart_redirects_to_shop(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("orders:checkout"))
        self.assertRedirects(response, reverse("products:product_list"))

    def test_checkout_page_loads_with_items(self):
        self.client.force_login(self.customer)
        self.fill_cart(self.adapter)
        response = self.client.get(reverse("orders:checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Travel Adapter")

    def test_placing_an_order(self):
        self.client.force_login(self.customer)
        self.fill_cart(self.backpack, 2)
        self.fill_cart(self.adapter, 1)
        response = self.client.post(reverse("orders:checkout"), DELIVERY)

        order = Order.objects.get()
        self.assertRedirects(response, order.get_absolute_url())
        self.assertEqual(order.user, self.customer)
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.subtotal, Decimal("132.48"))
        self.assertEqual(order.delivery_cost, Decimal("0.00"))
        self.assertEqual(order.total, Decimal("132.48"))
        self.assertEqual(order.postcode, "LS1 4AP")

        # Stock is reduced and the cart is emptied.
        self.backpack.refresh_from_db()
        self.adapter.refresh_from_db()
        self.assertEqual(self.backpack.stock, 1)
        self.assertEqual(self.adapter.stock, 9)
        self.assertEqual(self.client.session.get("cart"), {})

        # Delivery details were saved to the profile.
        self.customer.profile.refresh_from_db()
        self.assertEqual(self.customer.profile.city, "Leeds")

    def test_invalid_details_do_not_create_an_order(self):
        self.client.force_login(self.customer)
        self.fill_cart(self.adapter)
        response = self.client.post(
            reverse("orders:checkout"), dict(DELIVERY, phone="", city="")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.adapter.refresh_from_db()
        self.assertEqual(self.adapter.stock, 10)

    def test_cart_is_trimmed_when_stock_drops_before_checkout(self):
        self.client.force_login(self.customer)
        self.fill_cart(self.backpack, 3)
        # Someone else buys two while this shopper is still browsing.
        Product.objects.filter(pk=self.backpack.pk).update(stock=1)

        self.client.post(reverse("orders:checkout"), DELIVERY)
        self.assertEqual(Order.objects.get().items.get().quantity, 1)
        self.backpack.refresh_from_db()
        self.assertEqual(self.backpack.stock, 0)

    def test_order_is_rolled_back_when_stock_runs_out_mid_checkout(self):
        """Simulate the race the row lock protects against."""

        class StaleCart:
            """A cart whose lines were read before the stock changed."""

            def __init__(self, product):
                self.product = product

            def lines(self):
                return [{"product": self.product, "quantity": 3}]

        stale = StaleCart(self.backpack)
        Product.objects.filter(pk=self.backpack.pk).update(stock=1)
        form = CheckoutForm(data=DELIVERY)
        self.assertTrue(form.is_valid(), form.errors)

        with self.assertRaises(StockError):
            _place_order(self.customer, stale, form)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderItem.objects.count(), 0)
        self.backpack.refresh_from_db()
        self.assertEqual(self.backpack.stock, 1)


class OrderAccessTests(OrderTestCase):
    def test_owner_can_view_order(self):
        order = self.place_order()
        response = self.client.get(order.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, order.transaction_id)

    def test_anonymous_user_is_redirected(self):
        order = self.place_order()
        self.client.logout()
        response = self.client.get(order.get_absolute_url())
        self.assertEqual(response.status_code, 302)

    def test_other_customer_gets_403(self):
        order = self.place_order()
        self.client.force_login(self.other_customer)
        response = self.client.get(order.get_absolute_url())
        self.assertEqual(response.status_code, 403)

    def test_staff_can_view_any_order(self):
        order = self.place_order()
        self.client.force_login(self.staff)
        response = self.client.get(order.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Staff: update status")

    def test_unknown_order_returns_404(self):
        self.client.force_login(self.customer)
        response = self.client.get(
            reverse("orders:order_detail", args=["DOESNOTEXIST"])
        )
        self.assertEqual(response.status_code, 404)

    def test_customer_can_cancel_and_stock_is_returned(self):
        order = self.place_order(self.adapter, 4)
        self.adapter.refresh_from_db()
        self.assertEqual(self.adapter.stock, 6)

        self.client.post(
            reverse("orders:order_cancel", args=[order.transaction_id])
        )
        order.refresh_from_db()
        self.adapter.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(self.adapter.stock, 10)

    def test_shipped_order_cannot_be_cancelled(self):
        order = self.place_order(self.adapter, 4)
        Order.objects.filter(pk=order.pk).update(status=Order.Status.SHIPPED)
        self.client.post(
            reverse("orders:order_cancel", args=[order.transaction_id])
        )
        order.refresh_from_db()
        self.adapter.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPED)
        self.assertEqual(self.adapter.stock, 6)

    def test_other_customer_cannot_cancel(self):
        order = self.place_order()
        self.client.force_login(self.other_customer)
        response = self.client.post(
            reverse("orders:order_cancel", args=[order.transaction_id])
        )
        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)


class StaffOrderTests(OrderTestCase):
    def test_order_list_is_staff_only(self):
        url = reverse("orders:order_manage")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_staff_can_update_status(self):
        order = self.place_order()
        self.client.force_login(self.staff)
        self.client.post(
            reverse(
                "orders:order_status_update", args=[order.transaction_id]
            ),
            {"status": Order.Status.SHIPPED},
        )
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPED)

    def test_customer_cannot_update_status(self):
        order = self.place_order()
        response = self.client.post(
            reverse(
                "orders:order_status_update", args=[order.transaction_id]
            ),
            {"status": Order.Status.DELIVERED},
        )
        self.assertEqual(response.status_code, 403)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)

    def test_invalid_status_is_rejected(self):
        order = self.place_order()
        self.client.force_login(self.staff)
        self.client.post(
            reverse(
                "orders:order_status_update", args=[order.transaction_id]
            ),
            {"status": "teleported"},
        )
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)

    def test_staff_cancellation_restocks_once_and_cannot_be_reopened(self):
        order = self.place_order(self.adapter, 2)
        url = reverse(
            "orders:order_status_update", args=[order.transaction_id]
        )
        self.client.force_login(self.staff)
        self.client.post(url, {"status": Order.Status.CANCELLED})
        self.client.post(url, {"status": Order.Status.PROCESSING})
        order.refresh_from_db()
        self.adapter.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(self.adapter.stock, 10)
