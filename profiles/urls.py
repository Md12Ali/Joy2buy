from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

# The three authentication routes are deliberately left outside the
# "profiles" namespace so that Django's own defaults (LOGIN_URL = "login")
# resolve without extra configuration.
auth_patterns = [
    path("login/", views.StoreLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("signup/", views.signup, name="signup"),
]

profile_patterns = [
    path("", views.dashboard, name="dashboard"),
    path("edit/", views.profile_edit, name="profile_edit"),
    path(
        "password/",
        views.StorePasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "wishlist/<int:product_id>/",
        views.wishlist_toggle,
        name="wishlist_toggle",
    ),
]
