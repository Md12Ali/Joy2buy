import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("products", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone", models.CharField(blank=True, max_length=20)),
                ("address_line1", models.CharField(blank=True, max_length=120, verbose_name="address line 1")),
                ("address_line2", models.CharField(blank=True, max_length=120, verbose_name="address line 2")),
                ("city", models.CharField(blank=True, max_length=60, verbose_name="town or city")),
                ("postcode", models.CharField(blank=True, max_length=12)),
                ("country", models.CharField(blank=True, default="United Kingdom", max_length=60)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
                ("wishlist", models.ManyToManyField(blank=True, related_name="wishlisted_by", to="products.product")),
            ],
            options={
                "ordering": ["user__username"],
            },
        ),
    ]
