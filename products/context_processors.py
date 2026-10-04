"""Template context shared by every page."""
from .models import Category


def categories(request):
    """Expose the category list for the navigation bar and footer."""
    return {"nav_categories": Category.objects.all()}
