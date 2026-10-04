"""Tests for the session cart and its views."""
from decimal import Decimal

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from products.models import Category, Product


class CartTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        category = Category.objects.create(name="Fitness")
        cls.mat = Product.objects.create(
            category=category,
            name="FlexGrip Yoga Mat",
            description="A non-slip mat with cushioning for hard floors.",
            price=Decimal("24.99"),
            stock=5,
        )
        cls.bottle = Product.objects.create(
            category=category,
            name="Steel Water Bottle",
            description="Keeps drinks cold for a full day outdoors.",
            price=Decimal("18.50"),
            stock=50,
        )
        cls.sold_out = Product.objects.create(
            category=category,
            name="Adjustable Dumbbells",
            description="A pair of dumbbells that adjust from 2 to 10 kg.",
            price=Decimal("89.00"),
            stock=0,
        )

    def add(self, product, quantity=1, **extra):
        return self.client.post(
            reverse("cart:cart_add", args=[product.pk]),
            {"quantity": quantity},
            **extra,
        )

    def session_cart(self):
        return self.client.session.get(settings.CART_SESSION_KEY, {})


class CartViewTests(CartTestCase):
    def test_empty_cart_page(self):
        response = self.client.get(reverse("cart:cart_detail"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your cart is empty")

    def test_add_to_cart_stores_quantity_in_session(self):
        response = self.add(self.mat, 2)
        self.assertRedirects(response, reverse("cart:cart_detail"))
        self.assertEqual(self.session_cart(), {str(self.mat.pk): 2})

    def test_adding_twice_increases_quantity(self):
        self.add(self.mat, 1)
        self.add(self.mat, 2)
        self.assertEqual(self.session_cart()[str(self.mat.pk)], 3)

    def test_quantity_is_capped_at_stock(self):
        self.add(self.mat, 4)
        self.add(self.mat, 4)
        self.assertEqual(self.session_cart()[str(self.mat.pk)], 5)

    def test_cannot_add_out_of_stock_product(self):
        self.add(self.sold_out)
        self.assertEqual(self.session_cart(), {})

    def test_invalid_quantities_are_rejected(self):
        for bad in ("0", "-3", "abc", "", "9999"):
            with self.subTest(quantity=bad):
                self.add(self.mat, bad)
                self.assertEqual(self.session_cart(), {})

    def test_add_requires_post(self):
        response = self.client.get(
            reverse("cart:cart_add", args=[self.mat.pk])
        )
        self.assertEqual(response.status_code, 405)

    def test_unknown_product_returns_404(self):
        response = self.client.post(
            reverse("cart:cart_add", args=[99999]), {"quantity": 1}
        )
        self.assertEqual(response.status_code, 404)

    def test_cart_page_shows_totals_and_delivery_charge(self):
        self.add(self.mat, 1)
        response = self.client.get(reverse("cart:cart_detail"))
        cart = response.context["cart"]
        self.assertEqual(cart.subtotal, Decimal("24.99"))
        self.assertEqual(cart.delivery, settings.STANDARD_DELIVERY_COST)
        self.assertEqual(
            cart.total, Decimal("24.99") + settings.STANDARD_DELIVERY_COST
        )
        self.assertContains(response, "FlexGrip Yoga Mat")

    def test_delivery_is_free_over_threshold(self):
        self.add(self.bottle, 3)
        cart = self.client.get(reverse("cart:cart_detail")).context["cart"]
        self.assertEqual(cart.subtotal, Decimal("55.50"))
        self.assertEqual(cart.delivery, Decimal("0.00"))
        self.assertEqual(cart.total, Decimal("55.50"))

    def test_update_quantity(self):
        self.add(self.mat, 1)
        self.client.post(
            reverse("cart:cart_update", args=[self.mat.pk]), {"quantity": 4}
        )
        self.assertEqual(self.session_cart()[str(self.mat.pk)], 4)

    def test_update_rejects_item_not_in_cart(self):
        self.client.post(
            reverse("cart:cart_update", args=[self.mat.pk]), {"quantity": 2}
        )
        self.assertEqual(self.session_cart(), {})

    def test_remove_from_cart(self):
        self.add(self.mat, 1)
        self.add(self.bottle, 1)
        self.client.post(reverse("cart:cart_remove", args=[self.mat.pk]))
        self.assertEqual(self.session_cart(), {str(self.bottle.pk): 1})

    def test_cart_drops_products_that_become_unavailable(self):
        self.add(self.mat, 2)
        Product.objects.filter(pk=self.mat.pk).update(
            status=Product.Status.ARCHIVED
        )
        response = self.client.get(reverse("cart:cart_detail"))
        self.assertContains(response, "Your cart is empty")

    def test_cart_count_appears_in_navbar(self):
        self.add(self.mat, 2)
        self.add(self.bottle, 1)
        response = self.client.get(reverse("products:product_list"))
        self.assertEqual(response.context["cart_count"], 3)

    def test_external_next_address_is_ignored(self):
        response = self.client.post(
            reverse("cart:cart_add", args=[self.mat.pk]),
            {"quantity": 1, "next": "https://evil.example.com/"},
        )
        self.assertRedirects(response, reverse("cart:cart_detail"))


class CartJsonTests(CartTestCase):
    """The same views answer with JSON for JavaScript (fetch) requests."""

    ajax = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}

    def test_add_returns_summary(self):
        response = self.add(self.mat, 2, **self.ajax)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["cart_count"], 2)
        self.assertEqual(data["subtotal"], "£49.98")
        self.assertEqual(data["delivery"], "£4.99")
        self.assertEqual(data["total"], "£54.97")

    def test_invalid_quantity_returns_400_with_message(self):
        response = self.add(self.mat, "abc", **self.ajax)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["ok"])
        self.assertEqual(data["cart_count"], 0)
        self.assertTrue(data["message"])

    def test_update_returns_line_total(self):
        self.add(self.mat, 1)
        response = self.client.post(
            reverse("cart:cart_update", args=[self.mat.pk]),
            {"quantity": 3},
            **self.ajax,
        )
        data = response.json()
        self.assertEqual(data["quantity"], 3)
        self.assertEqual(data["line_total"], "£74.97")

    def test_remove_returns_empty_cart(self):
        self.add(self.mat, 1)
        response = self.client.post(
            reverse("cart:cart_remove", args=[self.mat.pk]), **self.ajax
        )
        self.assertEqual(response.json()["cart_count"], 0)
