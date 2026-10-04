"""Registration and account forms."""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    UserCreationForm,
)

from joy2buy.forms import BootstrapFormMixin, tidy_text
from orders.forms import validate_phone, validate_postcode

from .models import UserProfile

User = get_user_model()


class SignUpForm(BootstrapFormMixin, UserCreationForm):
    """Create an account. Passwords are hashed by Django, never stored."""

    email = forms.EmailField(
        help_text="Used for order confirmations only.",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    first_name = forms.CharField(max_length=60)
    last_name = forms.CharField(max_length=60)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "An account with this email address already exists."
            )
        return email

    def clean_first_name(self):
        return tidy_text(self.cleaned_data.get("first_name"))

    def clean_last_name(self):
        return tidy_text(self.cleaned_data.get("last_name"))


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    """The standard Django login form with Bootstrap styling."""


class StyledPasswordChangeForm(BootstrapFormMixin, PasswordChangeForm):
    """The standard Django password change form with Bootstrap styling."""


class UserDetailsForm(BootstrapFormMixin, forms.ModelForm):
    """Name and email address held on the user account."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        clash = User.objects.filter(email__iexact=email).exclude(
            pk=self.instance.pk
        )
        if clash.exists():
            raise forms.ValidationError(
                "Another account already uses this email address."
            )
        return email


class UserProfileForm(BootstrapFormMixin, forms.ModelForm):
    """Default delivery details used to pre-fill the checkout."""

    class Meta:
        model = UserProfile
        fields = [
            "phone",
            "address_line1",
            "address_line2",
            "city",
            "postcode",
            "country",
        ]

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        return validate_phone(phone) if phone else ""

    def clean_postcode(self):
        postcode = self.cleaned_data.get("postcode")
        return validate_postcode(postcode) if postcode else ""
