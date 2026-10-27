from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit_price", "quantity")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        # Lines are created only at checkout, together with the stock change.
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Orders are read-only for status here. Changing the status in the admin
    would skip the locked, re-checked update in ``orders.views`` and so
    could cancel an order without returning its stock, or reopen a
    cancelled one. Staff change status on the Store management order page.
    """

    list_display = (
        "transaction_id", "user", "status", "total", "created",
    )
    list_filter = ("status", "created")
    search_fields = ("transaction_id", "user__username", "email", "postcode")
    readonly_fields = (
        "transaction_id", "status", "subtotal", "delivery_cost", "total",
        "created", "updated",
    )
    inlines = [OrderItemInline]

    def has_delete_permission(self, request, obj=None):
        # Deleting an order would not return its stock; cancel it instead.
        return False
