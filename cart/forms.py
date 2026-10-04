"""Validation for cart quantity input."""
from django import forms
from django.conf import settings


class CartQuantityForm(forms.Form):
    """Checks that a requested quantity is a sensible whole number."""

    quantity = forms.IntegerField(
        min_value=1,
        max_value=settings.MAX_QUANTITY_PER_LINE,
        error_messages={
            "required": "Please enter a quantity.",
            "invalid": "The quantity must be a whole number.",
            "min_value": "The quantity must be at least 1.",
            "max_value": (
                f"You can buy up to {settings.MAX_QUANTITY_PER_LINE} of "
                "one item per order."
            ),
        },
    )
