"""Project-level error handlers that render the custom error templates."""
from django.http import HttpResponseServerError
from django.shortcuts import render
from django.template import loader


def permission_denied(request, exception=None):
    """403: the visitor is signed in but not allowed to do this."""
    return render(request, "403.html", status=403)


def page_not_found(request, exception=None):
    """404: the address does not match any page."""
    return render(request, "404.html", status=404)


def server_error(request):
    """
    500: something failed on our side.

    The template is rendered without context processors so that this page
    still works when the database or the session store is the thing failing.
    """
    return HttpResponseServerError(loader.render_to_string("500.html"))
