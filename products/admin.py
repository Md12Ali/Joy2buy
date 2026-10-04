from django.contrib import admin

from .models import Category, Product, ProductReview


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock", "rating", "status")
    list_filter = ("status", "category")
    list_editable = ("price", "stock", "status")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("rating", "created", "updated")


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "created")
    list_filter = ("rating",)
    search_fields = ("product__name", "user__username", "text")
    readonly_fields = ("created", "updated")
