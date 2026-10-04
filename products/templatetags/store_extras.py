"""Small presentation helpers used by the store templates."""
from decimal import Decimal, InvalidOperation

from django import template
from django.conf import settings
from django.utils.html import format_html

register = template.Library()


@register.filter
def currency(value):
    """Format a number as pounds sterling, e.g. 1234.5 -> "£1,234.50"."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return ""
    return f"{settings.CURRENCY_SYMBOL}{amount:,.2f}"


@register.filter
def tone(value):
    """Map an id onto one of six placeholder colour themes (0-5)."""
    try:
        return int(value) % 6
    except (TypeError, ValueError):
        return 0


@register.simple_tag
def star_rating(value, count=None):
    """
    Render a five-star rating that is also readable by screen readers.

    The visual stars are hidden from assistive technology and replaced by a
    plain-language label such as "Rated 4.5 out of 5".
    """
    try:
        score = float(value or 0)
    except (TypeError, ValueError):
        score = 0.0
    score = max(0.0, min(5.0, score))
    percent = round(score / 5 * 100)
    try:
        total = int(count)
    except (TypeError, ValueError):
        total = None
    if total == 0:
        label = "No reviews yet"
    else:
        label = f"Rated {score:.1f} out of 5"
    return format_html(
        '<span class="stars" role="img" aria-label="{}">'
        '<span class="stars-base" aria-hidden="true">'
        "★★★★★"
        '<span class="stars-fill" style="width: {}%">'
        "★★★★★</span></span></span>",
        label,
        percent,
    )


@register.simple_tag(takes_context=True)
def query_string(context, **changes):
    """
    Rebuild the current query string with some parameters replaced.

    Used by pagination and filter links so that "page 2" keeps the search
    term and category the shopper already chose.
    """
    params = context["request"].GET.copy()
    for key, value in changes.items():
        if value in (None, ""):
            params.pop(key, None)
        else:
            params[key] = value
    encoded = params.urlencode()
    return f"?{encoded}" if encoded else "?"
