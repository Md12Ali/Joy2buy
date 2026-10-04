"""Tests for accounts: sign up, login, dashboard, profile and wishlist."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from products.models import Category, Product

from .forms import SignUpForm, UserProfileForm
from .models import UserProfile, get_profile

User = get_user_model()

SIGNUP = {
    "username": "jordan",
    "first_name": "Jordan",
    "last_name": "Lee",
    "email": "Jordan@Example.com",
    "password1": "Tr1cky-Passphrase",
    "password2": "Tr1cky-Passphrase",
}


class ProfileModelTests(TestCase):
    def test_profile_is_created_with_user(self):
        user = User.objects.create_user("sam", password="Str0ng-pass!")
        self.assertIsInstance(user.profile, UserProfile)
        self.assertEqual(str(user.profile), "Profile of sam")
        self.assertFalse(user.profile.has_delivery_details)

    def test_get_profile_recreates_a_missing_profile(self):
        user = User.objects.create_user("sam", password="Str0ng-pass!")
        UserProfile.objects.filter(user=user).delete()
        profile = get_profile(User.objects.get(pk=user.pk))
        self.assertEqual(profile.user, user)

    def test_default_address(self):
        user = User.objects.create_user("sam", password="Str0ng-pass!")
        profile = user.profile
        profile.address_line1 = "12 Market Street"
        profile.city = "Leeds"
        profile.postcode = "LS1 4AP"
        profile.save()
        self.assertTrue(profile.has_delivery_details)
        self.assertEqual(
            profile.default_address,
            "12 Market Street, Leeds, LS1 4AP, United Kingdom",
        )

    def test_password_is_stored_hashed(self):
        user = User.objects.create_user("sam", password="Str0ng-pass!")
        self.assertNotEqual(user.password, "Str0ng-pass!")
        self.assertTrue(user.check_password("Str0ng-pass!"))


class SignUpTests(TestCase):
    def test_signup_page_loads(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)

    def test_signup_creates_user_profile_and_logs_in(self):
        response = self.client.post(reverse("signup"), SIGNUP)
        self.assertRedirects(response, reverse("profiles:dashboard"))
        user = User.objects.get(username="jordan")
        self.assertEqual(user.email, "jordan@example.com")
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_mismatched_passwords_are_rejected(self):
        form = SignUpForm(data=dict(SIGNUP, password2="Different-pass1"))
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_weak_password_is_rejected(self):
        form = SignUpForm(
            data=dict(SIGNUP, password1="12345678", password2="12345678")
        )
        self.assertFalse(form.is_valid())

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            "first", email="jordan@example.com", password="Str0ng-pass!"
        )
        form = SignUpForm(data=SIGNUP)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class AccountViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="sam",
            email="sam@example.com",
            password="Str0ng-pass!",
            first_name="Sam",
        )
        category = Category.objects.create(name="Stationery")
        cls.product = Product.objects.create(
            category=category,
            name="A5 Dotted Notebook",
            description="192 numbered pages of bleed-resistant paper.",
            price=Decimal("12.50"),
            stock=20,
        )

    def test_login_page_loads(self):
        self.assertEqual(self.client.get(reverse("login")).status_code, 200)

    def test_login_with_correct_and_incorrect_password(self):
        response = self.client.post(
            reverse("login"), {"username": "sam", "password": "wrong"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

        response = self.client.post(
            reverse("login"), {"username": "sam", "password": "Str0ng-pass!"}
        )
        self.assertRedirects(response, reverse("profiles:dashboard"))

    def test_logout_requires_post_and_signs_out(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("products:product_list"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_private_pages_redirect_anonymous_users(self):
        for name in ("dashboard", "profile_edit", "password_change"):
            with self.subTest(page=name):
                url = reverse(f"profiles:{name}")
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)

    def test_dashboard_shows_account_sections(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("profiles:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Order history")
        self.assertContains(response, "Your reviews")
        self.assertContains(response, "Your wishlist")

    def test_update_profile(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("profiles:profile_edit"),
            {
                "user-first_name": "Samuel",
                "user-last_name": "Taylor",
                "user-email": "samuel@example.com",
                "profile-phone": "07700 900123",
                "profile-address_line1": "12 Market Street",
                "profile-address_line2": "",
                "profile-city": "Leeds",
                "profile-postcode": "ls1 4ap",
                "profile-country": "United Kingdom",
            },
        )
        self.assertRedirects(response, reverse("profiles:dashboard"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Samuel")
        self.assertEqual(self.user.email, "samuel@example.com")
        self.assertEqual(self.user.profile.postcode, "LS1 4AP")

    def test_invalid_profile_update_changes_nothing(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("profiles:profile_edit"),
            {
                "user-first_name": "Samuel",
                "user-last_name": "Taylor",
                "user-email": "not-an-email",
                "profile-phone": "abc",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Sam")

    def test_profile_form_allows_blank_optional_fields(self):
        form = UserProfileForm(data={"country": "United Kingdom"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_password_change(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("profiles:password_change"),
            {
                "old_password": "Str0ng-pass!",
                "new_password1": "An0ther-Passphrase",
                "new_password2": "An0ther-Passphrase",
            },
        )
        self.assertRedirects(response, reverse("profiles:dashboard"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("An0ther-Passphrase"))

    def test_wishlist_toggle_adds_then_removes(self):
        url = reverse("profiles:wishlist_toggle", args=[self.product.pk])
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertEqual(self.user.profile.wishlist.count(), 0)

        self.client.force_login(self.user)
        self.client.post(url)
        self.assertIn(self.product, self.user.profile.wishlist.all())

        response = self.client.post(
            url, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertFalse(response.json()["saved"])
        self.assertEqual(self.user.profile.wishlist.count(), 0)
