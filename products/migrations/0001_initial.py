import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models

import products.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=100, unique=True)),
                ("description", models.TextField(blank=True)),
                ("image", models.ImageField(blank=True, upload_to="categories/", validators=[products.validators.validate_image_size])),
            ],
            options={
                "verbose_name_plural": "categories",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(blank=True, max_length=140, unique=True)),
                ("description", models.TextField()),
                ("specifications", models.TextField(blank=True, help_text='One per line, written as "Label: value".')),
                ("price", models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))])),
                ("stock", models.PositiveIntegerField(default=0)),
                ("image", models.ImageField(blank=True, upload_to="products/", validators=[products.validators.validate_image_size])),
                ("rating", models.DecimalField(decimal_places=2, default=Decimal("0.00"), editable=False, help_text="Average of customer review scores (kept up to date automatically).", max_digits=3)),
                ("status", models.CharField(choices=[("active", "Active (visible in store)"), ("draft", "Draft (hidden)"), ("archived", "Archived (no longer sold)")], default="active", max_length=10)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="products", to="products.category")),
            ],
            options={
                "ordering": ["-created", "name"],
                "indexes": [models.Index(fields=["status", "-created"], name="product_status_created_idx")],
            },
        ),
        migrations.CreateModel(
            name="ProductReview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rating", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ("text", models.TextField(max_length=1000)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to="products.product")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reviews", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created"],
                "constraints": [models.UniqueConstraint(fields=("product", "user"), name="one_review_per_user_per_product")],
            },
        ),
    ]
