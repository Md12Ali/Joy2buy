"""Shared access-control decorators."""
from functools import wraps

from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied


def is_staff_member(user):
    """Return True for active staff accounts (store administrators)."""
    return user.is_active and user.is_staff


def _staff_or_403(user):
    """Test used with ``user_passes_test``: non-staff users get a 403."""
    if is_staff_member(user):
        return True
    raise PermissionDenied


def staff_required(view_func):
    """
    Restrict a view to store staff.

    Anonymous visitors are redirected to the login page (302). Signed-in
    customers receive the custom 403 page instead of a confusing login loop.
    """
    protected = login_required(user_passes_test(_staff_or_403)(view_func))
    return wraps(view_func)(protected)
