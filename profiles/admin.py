from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "city", "postcode", "country")
    search_fields = ("user__username", "user__email", "postcode")
    filter_horizontal = ("wishlist",)
    readonly_fields = ("created", "updated")
