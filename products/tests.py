"""Tests for the catalogue: models, storefront views, reviews, staff CRUD."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from .forms import ProductForm, ReviewForm
from .models import Category, Product, ProductReview

User = get_user_model()


class StoreTestCase(TestCase):
    """Shared fixtures: one category, three products, three users."""

    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(
            name="Audio", description="Headphones and speakers."
        )
        cls.product = Product.objects.create(
            category=cls.category,
            name="Aria Wireless Headphones",
            description="Closed-back wireless headphones with a long "
                        "battery life.",
            specifications="Battery life: 30 hours\nWeight: 255 g",
            price=Decimal("79.99"),
            stock=10,
        )
        cls.sold_out = Product.objects.create(
            category=cls.category,
            name="Tempo Speaker",
            description="A compact speaker with deep bass for outdoors.",
            price=Decimal("49.50"),
            stock=0,
        )
        cls.draft = Product.objects.create(
            category=cls.category,
            name="Unreleased Earbuds",
            description="Earbuds that are not on sale to the public yet.",
            price=Decimal("39.99"),
            stock=5,
            status=Product.Status.DRAFT,
        )
        cls.customer = User.objects.create_user(
            username="sam", email="sam@example.com", password="Str0ng-pass!"
        )
        cls.other_customer = User.objects.create_user(
            username="alex", email="alex@example.com", password="Str0ng-pass!"
        )
        cls.staff = User.objects.create_user(
            username="manager",
            email="manager@example.com",
            password="Str0ng-pass!",
            is_staff=True,
        )

    def product_payload(self, **overrides):
        data = {
            "category": self.category.pk,
            "name": "Pulse Wireless Earbuds",
            "description": "Lightweight earbuds with a pocket-sized "
                           "charging case.",
            "specifications": "Battery life: 7 hours",
            "price": "39.99",
            "stock": "25",
            "status": Product.Status.ACTIVE,
        }
        data.update(overrides)
        return data


class ModelTests(StoreTestCase):
    def test_slugs_are_generated_and_unique(self):
        self.assertEqual(self.category.slug, "audio")
        self.assertEqual(self.product.slug, "aria-wireless-headphones")
        twin = Product.objects.create(
            category=self.category,
            name="Aria Wireless Headphones",
            description="A second product that shares the same name.",
            price=Decimal("10.00"),
        )
        self.assertEqual(twin.slug, "aria-wireless-headphones-2")

    def test_string_representations(self):
        self.assertEqual(str(self.category), "Audio")
        self.assertEqual(str(self.product), "Aria Wireless Headphones")
        review = ProductReview.objects.create(
            product=self.product, user=self.customer, rating=4,
            text="Comfortable and clear sound.",
        )
        self.assertIn("4/5", str(review))

    def test_category_product_relationship(self):
        self.assertEqual(self.product.category, self.category)
        self.assertEqual(self.category.products.count(), 3)

    def test_category_with_products_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.category.delete()

    def test_stock_helpers(self):
        self.assertTrue(self.product.in_stock)
        self.assertTrue(self.product.is_purchasable)
        self.assertFalse(self.sold_out.in_stock)
        self.assertFalse(self.sold_out.is_purchasable)
        self.assertFalse(self.draft.is_purchasable)
        self.product.stock = 3
        self.assertTrue(self.product.low_stock)

    def test_spec_list_parses_lines(self):
        self.assertEqual(
            self.product.spec_list(),
            [("Battery life", "30 hours"), ("Weight", "255 g")],
        )

    def test_price_must_be_positive(self):
        self.product.price = Decimal("0.00")
        with self.assertRaises(ValidationError):
            self.product.full_clean()

    def test_active_queryset_hides_drafts(self):
        active = Product.objects.active()
        self.assertIn(self.product, active)
        self.assertNotIn(self.draft, active)

    def test_rating_follows_reviews(self):
        ProductReview.objects.create(
            product=self.product, user=self.customer, rating=5,
            text="Excellent headphones.",
        )
        review = ProductReview.objects.create(
            product=self.product, user=self.other_customer, rating=2,
            text="Too tight for my head.",
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.rating, Decimal("3.50"))

        review.delete()
        self.product.refresh_from_db()
        self.assertEqual(self.product.rating, Decimal("5.00"))

    def test_one_review_per_user_per_product(self):
        ProductReview.objects.create(
            product=self.product, user=self.customer, rating=5,
            text="Excellent headphones.",
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            ProductReview.objects.create(
                product=self.product, user=self.customer, rating=1,
                text="A second review is not allowed.",
            )

    def test_review_rating_range_is_validated(self):
        review = ProductReview(
            product=self.product, user=self.customer, rating=6,
            text="Six stars is not possible.",
        )
        with self.assertRaises(ValidationError):
            review.full_clean()


class FormTests(StoreTestCase):
    def test_product_form_accepts_valid_data(self):
        form = ProductForm(data=self.product_payload())
        self.assertTrue(form.is_valid(), form.errors)

    def test_product_form_rejects_bad_price_and_short_text(self):
        form = ProductForm(
            data=self.product_payload(price="-5", description="Too short")
        )
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)
        self.assertIn("description", form.errors)

    def test_review_form_requires_rating_and_real_text(self):
        form = ReviewForm(data={"rating": "", "text": "ok"})
        self.assertFalse(form.is_valid())
        self.assertIn("rating", form.errors)
        self.assertIn("text", form.errors)

    def test_review_form_rejects_out_of_range_rating(self):
        form = ReviewForm(data={"rating": "9", "text": "Long enough text."})
        self.assertFalse(form.is_valid())
        self.assertIn("rating", form.errors)


class StorefrontViewTests(StoreTestCase):
    def test_product_list_shows_active_products_only(self):
        response = self.client.get(reverse("products:product_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "products/product_list.html")
        self.assertContains(response, "Aria Wireless Headphones")
        self.assertNotContains(response, "Unreleased Earbuds")

    def test_search_filters_results(self):
        response = self.client.get(
            reverse("products:product_list"), {"q": "speaker"}
        )
        self.assertContains(response, "Tempo Speaker")
        self.assertNotContains(response, "Aria Wireless Headphones")

    def test_search_with_no_match_shows_empty_state(self):
        response = self.client.get(
            reverse("products:product_list"), {"q": "zzzz"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No products match your search")

    def test_category_filter(self):
        other = Category.objects.create(name="Travel")
        Product.objects.create(
            category=other,
            name="Commuter Backpack",
            description="A water-resistant backpack for a 16 inch laptop.",
            price=Decimal("54.99"),
            stock=4,
        )
        response = self.client.get(
            reverse("products:product_list"), {"category": other.slug}
        )
        self.assertContains(response, "Commuter Backpack")
        self.assertNotContains(response, "Tempo Speaker")

    def test_unknown_category_redirects_to_full_list(self):
        response = self.client.get(
            reverse("products:product_list"), {"category": "nope"}
        )
        self.assertRedirects(response, reverse("products:product_list"))

    def test_in_stock_filter_and_invalid_sort_and_page(self):
        response = self.client.get(
            reverse("products:product_list"),
            {"available": "1", "sort": "bogus", "page": "999"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Tempo Speaker")
        self.assertEqual(response.context["sort"], "newest")

    def test_search_suggestions_return_json(self):
        response = self.client.get(
            reverse("products:search_suggestions"), {"q": "aria"}
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Aria Wireless Headphones")
        self.assertEqual(results[0]["price"], "£79.99")

    def test_search_suggestions_ignore_one_letter(self):
        response = self.client.get(
            reverse("products:search_suggestions"), {"q": "a"}
        )
        self.assertEqual(response.json()["results"], [])

    def test_product_detail_page(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "£79.99")
        self.assertContains(response, "Battery life")
        self.assertContains(response, "Sign in to review")

    def test_draft_product_is_hidden_from_shoppers(self):
        response = self.client.get(self.draft.get_absolute_url())
        self.assertEqual(response.status_code, 404)

    def test_draft_product_is_visible_to_staff(self):
        self.client.force_login(self.staff)
        response = self.client.get(self.draft.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_unknown_page_uses_custom_404_template(self):
        response = self.client.get("/this-page-does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "404.html")


class ReviewViewTests(StoreTestCase):
    def setUp(self):
        self.url = reverse("products:review_save", args=[self.product.slug])
        self.valid = {"rating": "5", "text": "Brilliant sound and comfort."}

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.post(self.url, self.valid)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertEqual(ProductReview.objects.count(), 0)

    def test_get_is_not_allowed(self):
        self.client.force_login(self.customer)
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_create_review(self):
        self.client.force_login(self.customer)
        response = self.client.post(self.url, self.valid)
        self.assertEqual(response.status_code, 302)
        review = ProductReview.objects.get()
        self.assertEqual(review.user, self.customer)
        self.assertEqual(review.product, self.product)
        self.assertEqual(review.rating, 5)
        stored = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertIn("Thank you - your review is live.", stored)

    def test_second_submission_updates_the_existing_review(self):
        self.client.force_login(self.customer)
        self.client.post(self.url, self.valid)
        self.client.post(
            self.url, {"rating": "3", "text": "Changed my mind after a week."}
        )
        self.assertEqual(ProductReview.objects.count(), 1)
        self.assertEqual(ProductReview.objects.get().rating, 3)
        self.product.refresh_from_db()
        self.assertEqual(self.product.rating, Decimal("3.00"))

    def test_invalid_review_is_rejected_with_feedback(self):
        self.client.force_login(self.customer)
        response = self.client.post(self.url, {"rating": "", "text": "bad"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ProductReview.objects.count(), 0)
        self.assertContains(response, "Please choose a star rating.")

    def test_author_can_delete_own_review(self):
        review = ProductReview.objects.create(
            product=self.product, user=self.customer, rating=4,
            text="Good value for money.",
        )
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("products:review_delete", args=[review.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(ProductReview.objects.filter(pk=review.pk).exists())

    def test_other_customer_cannot_delete_review(self):
        review = ProductReview.objects.create(
            product=self.product, user=self.customer, rating=4,
            text="Good value for money.",
        )
        self.client.force_login(self.other_customer)
        response = self.client.post(
            reverse("products:review_delete", args=[review.pk])
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(ProductReview.objects.filter(pk=review.pk).exists())

    def test_staff_can_delete_any_review(self):
        review = ProductReview.objects.create(
            product=self.product, user=self.customer, rating=1,
            text="Inappropriate content here.",
        )
        self.client.force_login(self.staff)
        self.client.post(reverse("products:review_delete", args=[review.pk]))
        self.assertFalse(ProductReview.objects.filter(pk=review.pk).exists())


class StaffProductViewTests(StoreTestCase):
    def test_staff_pages_redirect_anonymous_users_to_login(self):
        urls = [
            reverse("products:product_manage"),
            reverse("products:product_create"),
            reverse("products:product_update", args=[self.product.slug]),
            reverse("products:product_delete", args=[self.product.slug]),
            reverse("products:category_create"),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)

    def test_staff_pages_forbid_ordinary_customers(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("products:product_manage"))
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "403.html")

        response = self.client.post(
            reverse("products:product_create"), self.product_payload()
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Product.objects.filter(name="Pulse Wireless Earbuds").exists()
        )

    def test_staff_can_open_management_pages(self):
        self.client.force_login(self.staff)
        for name in ("product_manage", "product_create", "category_create"):
            with self.subTest(page=name):
                response = self.client.get(reverse(f"products:{name}"))
                self.assertEqual(response.status_code, 200)

    def test_staff_can_create_product(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("products:product_create"), self.product_payload()
        )
        product = Product.objects.get(name="Pulse Wireless Earbuds")
        self.assertRedirects(response, product.get_absolute_url())
        self.assertEqual(product.price, Decimal("39.99"))
        self.assertEqual(product.stock, 25)

    def test_invalid_product_is_not_created(self):
        self.client.force_login(self.staff)
        before = Product.objects.count()
        response = self.client.post(
            reverse("products:product_create"),
            self.product_payload(name="", price="0"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), before)

    def test_staff_can_update_product(self):
        self.client.force_login(self.staff)
        self.client.post(
            reverse("products:product_update", args=[self.product.slug]),
            self.product_payload(
                name="Aria Wireless Headphones", price="69.99", stock="3"
            ),
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, Decimal("69.99"))
        self.assertEqual(self.product.stock, 3)

    def test_delete_asks_for_confirmation_then_deletes(self):
        self.client.force_login(self.staff)
        url = reverse("products:product_delete", args=[self.product.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Product.objects.filter(pk=self.product.pk).exists())

        response = self.client.post(url)
        self.assertRedirects(response, reverse("products:product_manage"))
        self.assertFalse(Product.objects.filter(pk=self.product.pk).exists())

    def test_staff_can_create_and_update_category(self):
        self.client.force_login(self.staff)
        self.client.post(
            reverse("products:category_create"),
            {"name": "Fitness", "description": "Training equipment."},
        )
        category = Category.objects.get(name="Fitness")
        self.assertEqual(category.slug, "fitness")

        self.client.post(
            reverse("products:category_update", args=[category.slug]),
            {"name": "Fitness & Sport", "description": "Training gear."},
        )
        category.refresh_from_db()
        self.assertEqual(category.name, "Fitness & Sport")

    def test_duplicate_category_name_is_rejected(self):
        self.client.force_login(self.staff)
        response = self.client.post(
            reverse("products:category_create"), {"name": "audio"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Category.objects.count(), 1)

    def test_category_in_use_is_not_deleted(self):
        self.client.force_login(self.staff)
        self.client.post(
            reverse("products:category_delete", args=[self.category.slug])
        )
        self.assertTrue(Category.objects.filter(pk=self.category.pk).exists())
