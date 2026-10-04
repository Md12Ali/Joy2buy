"""Customer profile: saved delivery details and a product wishlist."""
from django.conf import settings
from django.db import models

from products.models import Product


class UserProfile(models.Model):
    """Extra information attached one-to-one to a Django user account."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField(
        "address line 1", max_length=120, blank=True
    )
    address_line2 = models.CharField(
        "address line 2", max_length=120, blank=True
    )
    city = models.CharField("town or city", max_length=60, blank=True)
    postcode = models.CharField(max_length=12, blank=True)
    country = models.CharField(
        max_length=60, blank=True, default="United Kingdom"
    )
    wishlist = models.ManyToManyField(
        Product,
        blank=True,
        related_name="wishlisted_by",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return f"Profile of {self.user.get_username()}"

    @property
    def has_delivery_details(self):
        """True when enough is saved to pre-fill the checkout form."""
        return bool(self.address_line1 and self.city and self.postcode)

    @property
    def default_address(self):
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.postcode,
            self.country,
        ]
        return ", ".join(part for part in parts if part)

    def update_from_order(self, order):
        """Copy the delivery details used on an order into the profile."""
        self.phone = order.phone
        self.address_line1 = order.address_line1
        self.address_line2 = order.address_line2
        self.city = order.city
        self.postcode = order.postcode
        self.country = order.country
        self.save()


def get_profile(user):
    """Return the user's profile, creating it if it is somehow missing."""
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile
