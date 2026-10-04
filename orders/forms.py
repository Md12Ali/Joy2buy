"""Checkout and order management forms."""
import re

from django import forms

from joy2buy.forms import BootstrapFormMixin, tidy_text

from .models import Order

PHONE_PATTERN = re.compile(r"^\+?[0-9][0-9 ()-]{6,18}$")
POSTCODE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 -]{1,10}$")


def validate_phone(value):
    """Shared phone number rule: digits, spaces, brackets, optional +."""
    value = tidy_text(value)
    if not PHONE_PATTERN.match(value):
        raise forms.ValidationError(
            "Enter a valid phone number, for example 07700 900123."
        )
    return value


def validate_postcode(value):
    """Shared postcode rule: letters, digits, spaces and hyphens."""
    value = tidy_text(value).upper()
    if not POSTCODE_PATTERN.match(value):
        raise forms.ValidationError(
            "Enter a valid postcode, for example SW1A 1AA."
        )
    return value


class CheckoutForm(BootstrapFormMixin, forms.ModelForm):
    """Delivery details collected at checkout."""

    save_details = forms.BooleanField(
        required=False,
        initial=True,
        label="Save these delivery details to my account",
    )

    class Meta:
        model = Order
        fields = [
            "full_name",
            "email",
            "phone",
            "address_line1",
            "address_line2",
            "city",
            "postcode",
            "country",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
            "phone": forms.TextInput(
                attrs={"autocomplete": "tel", "inputmode": "tel"}
            ),
            "address_line1": forms.TextInput(
                attrs={"autocomplete": "address-line1"}
            ),
            "address_line2": forms.TextInput(
                attrs={"autocomplete": "address-line2"}
            ),
            "city": forms.TextInput(
                attrs={"autocomplete": "address-level2"}
            ),
            "postcode": forms.TextInput(
                attrs={"autocomplete": "postal-code"}
            ),
            "country": forms.TextInput(
                attrs={"autocomplete": "country-name"}
            ),
        }

    def clean_full_name(self):
        name = tidy_text(self.cleaned_data.get("full_name"))
        if len(name) < 2:
            raise forms.ValidationError("Please enter your full name.")
        return name

    def clean_phone(self):
        return validate_phone(self.cleaned_data.get("phone"))

    def clean_postcode(self):
        return validate_postcode(self.cleaned_data.get("postcode"))

    def clean_address_line1(self):
        address = tidy_text(self.cleaned_data.get("address_line1"))
        if len(address) < 4:
            raise forms.ValidationError(
                "Please enter the first line of your address."
            )
        return address


class OrderStatusForm(BootstrapFormMixin, forms.ModelForm):
    """Staff form for moving an order through its life cycle."""

    class Meta:
        model = Order
        fields = ["status"]
