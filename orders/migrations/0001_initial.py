import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models

import orders.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("products", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("shipped", "Shipped"), ("delivered", "Delivered"), ("cancelled", "Cancelled")], default="pending", max_length=12)),
                ("transaction_id", models.CharField(default=orders.models.generate_transaction_id, editable=False, max_length=32, unique=True)),
                ("full_name", models.CharField(max_length=100)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(max_length=20)),
                ("address_line1", models.CharField(max_length=120, verbose_name="address line 1")),
                ("address_line2", models.CharField(blank=True, max_length=120, verbose_name="address line 2")),
                ("city", models.CharField(max_length=60, verbose_name="town or city")),
                ("postcode", models.CharField(max_length=12)),
                ("country", models.CharField(default="United Kingdom", max_length=60)),
                ("subtotal", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("delivery_cost", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=6)),
                ("total", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="orders", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created"],
            },
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("product_name", models.CharField(max_length=120)),
                ("unit_price", models.DecimalField(decimal_places=2, max_digits=8, validators=[django.core.validators.MinValueValidator(Decimal("0.00"))])),
                ("quantity", models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="orders.order")),
                ("product", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="order_items", to="products.product")),
            ],
            options={
                "ordering": ["pk"],
            },
        ),
    ]
