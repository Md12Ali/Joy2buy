"""Account views: sign up, dashboard, profile editing and wishlist."""
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
    require_safe,
)

from products.models import Product

from .forms import (
    LoginForm,
    SignUpForm,
    StyledPasswordChangeForm,
    UserDetailsForm,
    UserProfileForm,
)
from .models import get_profile


class StoreLoginView(SuccessMessageMixin, LoginView):
    """Sign in. Already signed-in users are sent to their dashboard."""

    authentication_form = LoginForm
    template_name = "registration/login.html"
    redirect_authenticated_user = True
    success_message = "Welcome back, %(username)s."


class StorePasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    """Change password (the user stays signed in afterwards)."""

    form_class = StyledPasswordChangeForm
    template_name = "registration/password_change_form.html"
    success_url = reverse_lazy("profiles:dashboard")
    success_message = "Your password has been changed."


@require_http_methods(["GET", "POST"])
def signup(request):
    """Register a new customer account and sign them in."""
    if request.user.is_authenticated:
        return redirect("profiles:dashboard")

    form = SignUpForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
            login(request, user)
            messages.success(
                request,
                f"Welcome to JOY2BUY, {user.first_name or user.username}. "
                "Your account is ready.",
            )
            return redirect("profiles:dashboard")
        messages.error(
            request,
            "Your account was not created. Please fix the highlighted "
            "fields.",
        )
    return render(request, "profiles/signup.html", {"form": form})


@login_required
@require_safe
def dashboard(request):
    """Customer dashboard: order history, review log and wishlist."""
    profile = get_profile(request.user)
    context = {
        "profile": profile,
        "orders": request.user.orders.prefetch_related("items"),
        "reviews": request.user.reviews.select_related("product"),
        "wishlist": profile.wishlist.select_related("category"),
    }
    return render(request, "profiles/dashboard.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def profile_edit(request):
    """Update account details and default delivery address together."""
    profile = get_profile(request.user)
    # Bind the form to a separate copy of the user so that rejected input
    # never leaks into "request.user" (and from there into the navbar).
    account = get_object_or_404(get_user_model(), pk=request.user.pk)
    user_form = UserDetailsForm(
        request.POST or None, instance=account, prefix="user"
    )
    profile_form = UserProfileForm(
        request.POST or None, instance=profile, prefix="profile"
    )
    if request.method == "POST":
        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user_form.save()
                profile_form.save()
            messages.success(request, "Your details have been updated.")
            return redirect("profiles:dashboard")
        messages.error(
            request,
            "Your details were not saved. Please fix the highlighted "
            "fields.",
        )
    context = {"user_form": user_form, "profile_form": profile_form}
    return render(request, "profiles/profile_form.html", context)


@login_required
@require_POST
def wishlist_toggle(request, product_id):
    """Add a product to the wishlist, or remove it if already saved."""
    product = get_object_or_404(Product.objects.active(), pk=product_id)
    profile = get_profile(request.user)
    if profile.wishlist.filter(pk=product.pk).exists():
        profile.wishlist.remove(product)
        saved = False
        text = f"{product.name} was removed from your wishlist."
    else:
        profile.wishlist.add(product)
        saved = True
        text = f"{product.name} was saved to your wishlist."

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {"ok": True, "saved": saved, "level": "success", "message": text}
        )
    messages.success(request, text)
    return redirect(product.get_absolute_url())
