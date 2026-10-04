from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit_price", "quantity")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_id", "user", "status", "total", "created",
    )
    list_filter = ("status", "created")
    search_fields = ("transaction_id", "user__username", "email", "postcode")
    readonly_fields = (
        "transaction_id", "subtotal", "delivery_cost", "total", "created",
        "updated",
    )
    inlines = [OrderItemInline]
