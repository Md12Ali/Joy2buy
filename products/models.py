"""Catalogue models: categories, products and customer reviews."""
from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.urls import reverse
from django.utils.text import slugify

from .validators import validate_image_size


def unique_slug(instance, source, max_length=140):
    """
    Build a URL-safe slug for ``instance`` that is unique within its model.

    "Desk Lamp" becomes "desk-lamp"; a second one becomes "desk-lamp-2".
    """
    base = slugify(source)[: max_length - 6] or "item"
    slug = base
    model = instance.__class__
    counter = 2
    while model.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


class Category(models.Model):
    """A department of the store, e.g. "Audio" or "Home & Kitchen"."""

    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="categories/",
        blank=True,
        validators=[validate_image_size],
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, max_length=100)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"{reverse('products:product_list')}?category={self.slug}"


class ProductQuerySet(models.QuerySet):
    """Query helpers shared by views and the cart."""

    def active(self):
        """Products that shoppers are allowed to see."""
        return self.filter(status=Product.Status.ACTIVE)

    def search(self, term):
        """Case-insensitive match on name, description and category."""
        term = (term or "").strip()
        if not term:
            return self
        return self.filter(
            models.Q(name__icontains=term)
            | models.Q(description__icontains=term)
            | models.Q(category__name__icontains=term)
        )


class Product(models.Model):
    """An item for sale."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active (visible in store)"
        DRAFT = "draft", "Draft (hidden)"
        ARCHIVED = "archived", "Archived (no longer sold)"

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField()
    specifications = models.TextField(
        blank=True,
        help_text='One per line, written as "Label: value".',
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(
        upload_to="products/",
        blank=True,
        validators=[validate_image_size],
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.00"),
        editable=False,
        help_text="Average of customer review scores (kept up to date "
                  "automatically).",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["-created", "name"]
        indexes = [
            models.Index(
                fields=["status", "-created"],
                name="product_status_created_idx",
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("products:product_detail", args=[self.slug])

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def is_purchasable(self):
        """True when the product is visible and at least one is in stock."""
        return self.status == self.Status.ACTIVE and self.in_stock

    @property
    def low_stock(self):
        return 0 < self.stock <= 5

    @property
    def initials(self):
        """Up to two letters shown on the tile when there is no photo."""
        words = [word for word in self.name.split() if word[0].isalnum()]
        return "".join(word[0] for word in words[:2]).upper() or "J"

    def spec_list(self):
        """Return specifications as a list of (label, value) pairs."""
        pairs = []
        for line in self.specifications.splitlines():
            line = line.strip()
            if not line:
                continue
            label, separator, value = line.partition(":")
            if separator and value.strip():
                pairs.append((label.strip(), value.strip()))
            else:
                pairs.append(("Detail", line))
        return pairs

    def update_rating(self):
        """Recalculate and store the average review score."""
        average = self.reviews.aggregate(average=Avg("rating"))["average"]
        value = Decimal(str(average or 0)).quantize(Decimal("0.01"))
        Product.objects.filter(pk=self.pk).update(rating=value)
        self.rating = value
        return value


class ProductReview(models.Model):
    """A customer's star rating and written review of a product."""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    text = models.TextField(max_length=1000)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"],
                name="one_review_per_user_per_product",
            ),
        ]

    def __str__(self):
        return f"{self.rating}/5 for {self.product} by {self.user}"
