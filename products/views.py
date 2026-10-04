"""Catalogue views: browsing, searching, reviewing and staff management."""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, ProtectedError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import (
    require_http_methods,
    require_POST,
    require_safe,
)

from joy2buy.decorators import is_staff_member, staff_required
from profiles.models import get_profile

from .forms import CategoryForm, ProductForm, ReviewForm
from .models import Category, Product, ProductReview

SORT_OPTIONS = {
    "newest": ("Newest first", ["-created", "name"]),
    "price_low": ("Price: low to high", ["price", "name"]),
    "price_high": ("Price: high to low", ["-price", "name"]),
    "rating": ("Highest rated", ["-rating", "name"]),
    "name": ("Name: A to Z", ["name"]),
}
MAX_SEARCH_LENGTH = 100


# --------------------------------------------------------------------------
# Read: storefront
# --------------------------------------------------------------------------
@require_safe
def product_list(request):
    """Product grid with search, category filter, sorting and pagination."""
    products = (
        Product.objects.active()
        .select_related("category")
        .annotate(review_total=Count("reviews"))
    )

    query = request.GET.get("q", "").strip()[:MAX_SEARCH_LENGTH]
    category_slug = request.GET.get("category", "").strip()
    sort = request.GET.get("sort", "newest")
    in_stock_only = request.GET.get("available") == "1"

    current_category = None
    if category_slug:
        current_category = Category.objects.filter(slug=category_slug).first()
        if current_category is None:
            messages.info(
                request,
                "That category could not be found, so all products are "
                "shown instead.",
            )
            return redirect("products:product_list")
        products = products.filter(category=current_category)

    if query:
        products = products.search(query)
    if in_stock_only:
        products = products.filter(stock__gt=0)
    if sort not in SORT_OPTIONS:
        sort = "newest"
    products = products.order_by(*SORT_OPTIONS[sort][1])

    paginator = Paginator(products, settings.PRODUCTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    is_filtered = bool(query or current_category or in_stock_only)
    context = {
        "page_obj": page_obj,
        "query": query,
        "current_category": current_category,
        "sort": sort,
        "sort_options": [
            (key, label) for key, (label, _) in SORT_OPTIONS.items()
        ],
        "in_stock_only": in_stock_only,
        "is_filtered": is_filtered,
        "result_count": paginator.count,
    }
    return render(request, "products/product_list.html", context)


@require_safe
def search_suggestions(request):
    """Return up to six matching products as JSON for the live search box."""
    query = request.GET.get("q", "").strip()[:MAX_SEARCH_LENGTH]
    results = []
    if len(query) >= 2:
        matches = (
            Product.objects.active()
            .search(query)
            .select_related("category")
            .order_by("name")[:6]
        )
        results = [
            {
                "name": product.name,
                "category": product.category.name,
                "price": f"{settings.CURRENCY_SYMBOL}{product.price:,.2f}",
                "url": product.get_absolute_url(),
            }
            for product in matches
        ]
    return JsonResponse({"query": query, "results": results})


def _get_visible_product(request, slug):
    """Fetch a product, hiding drafts and archived items from shoppers."""
    product = get_object_or_404(
        Product.objects.select_related("category"), slug=slug
    )
    visible = product.status == Product.Status.ACTIVE
    if not visible and not is_staff_member(request.user):
        raise Http404("This product is not available.")
    return product


def _detail_context(request, product, review_form=None):
    """Build the template context for the product detail page."""
    reviews = product.reviews.select_related("user")
    user_review = None
    in_wishlist = False
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()
        in_wishlist = (
            get_profile(request.user).wishlist.filter(pk=product.pk).exists()
        )
        if review_form is None:
            review_form = ReviewForm(instance=user_review)

    max_quantity = min(product.stock, settings.MAX_QUANTITY_PER_LINE)
    related = (
        Product.objects.active()
        .filter(category=product.category)
        .exclude(pk=product.pk)
        .select_related("category")
        .annotate(review_total=Count("reviews"))
        .order_by("-rating", "name")[:4]
    )
    return {
        "product": product,
        "reviews": reviews,
        "review_count": reviews.count(),
        "user_review": user_review,
        "review_form": review_form,
        "in_wishlist": in_wishlist,
        "max_quantity": max_quantity,
        "related_products": related,
    }


@require_safe
def product_detail(request, slug):
    """Full product page: gallery, price, stock, specifications, reviews."""
    product = _get_visible_product(request, slug)
    context = _detail_context(request, product)
    return render(request, "products/product_detail.html", context)


# --------------------------------------------------------------------------
# Create / update / delete: customer reviews
# --------------------------------------------------------------------------
@login_required
@require_POST
def review_save(request, slug):
    """Create the signed-in user's review, or update it if one exists."""
    product = get_object_or_404(Product.objects.active(), slug=slug)
    existing = ProductReview.objects.filter(
        product=product, user=request.user
    ).first()
    form = ReviewForm(request.POST, instance=existing)

    if form.is_valid():
        review = form.save(commit=False)
        review.product = product
        review.user = request.user
        review.save()
        if existing:
            messages.success(request, "Your review has been updated.")
        else:
            messages.success(request, "Thank you - your review is live.")
        return redirect(f"{product.get_absolute_url()}#reviews")

    messages.error(
        request,
        "Your review was not saved. Please fix the highlighted fields.",
    )
    context = _detail_context(request, product, review_form=form)
    return render(request, "products/product_detail.html", context)


@login_required
@require_POST
def review_delete(request, pk):
    """Delete a review. Only its author or a staff member may do this."""
    review = get_object_or_404(
        ProductReview.objects.select_related("product"), pk=pk
    )
    if review.user_id != request.user.pk and not is_staff_member(
        request.user
    ):
        raise PermissionDenied
    product = review.product
    review.delete()
    messages.success(request, "The review has been deleted.")
    return redirect(f"{product.get_absolute_url()}#reviews")


# --------------------------------------------------------------------------
# Staff: product and category management
# --------------------------------------------------------------------------
@staff_required
@require_safe
def product_manage(request):
    """Staff table of every product, including drafts and archived items."""
    products = Product.objects.select_related("category").order_by("name")
    query = request.GET.get("q", "").strip()[:MAX_SEARCH_LENGTH]
    status = request.GET.get("status", "")
    if query:
        products = products.search(query)
    if status in Product.Status.values:
        products = products.filter(status=status)
    else:
        status = ""

    paginator = Paginator(products, 20)
    context = {
        "page_obj": paginator.get_page(request.GET.get("page")),
        "query": query,
        "status": status,
        "status_choices": Product.Status.choices,
        "categories": Category.objects.annotate(
            product_total=Count("products")
        ),
    }
    return render(request, "products/product_manage.html", context)


@staff_required
@require_http_methods(["GET", "POST"])
def product_create(request):
    """Add a new product to the catalogue."""
    if not Category.objects.exists():
        messages.warning(
            request, "Create a category first, then add products to it."
        )
        return redirect("products:category_create")

    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            product = form.save()
            messages.success(request, f'"{product.name}" has been added.')
            return redirect(product.get_absolute_url())
        messages.error(
            request,
            "The product was not saved. Please fix the highlighted fields.",
        )
    context = {"form": form, "heading": "Add a product", "product": None}
    return render(request, "products/product_form.html", context)


@staff_required
@require_http_methods(["GET", "POST"])
def product_update(request, slug):
    """Edit an existing product."""
    product = get_object_or_404(Product, slug=slug)
    form = ProductForm(
        request.POST or None, request.FILES or None, instance=product
    )
    if request.method == "POST":
        if form.is_valid():
            product = form.save()
            messages.success(request, f'"{product.name}" has been updated.')
            return redirect(product.get_absolute_url())
        messages.error(
            request,
            "Your changes were not saved. Please fix the highlighted "
            "fields.",
        )
    context = {
        "form": form,
        "heading": f"Edit {product.name}",
        "product": product,
    }
    return render(request, "products/product_form.html", context)


@staff_required
@require_http_methods(["GET", "POST"])
def product_delete(request, slug):
    """Confirm (GET) and then permanently delete (POST) a product."""
    product = get_object_or_404(Product, slug=slug)
    if request.method == "POST":
        name = product.name
        product.delete()
        messages.success(request, f'"{name}" has been deleted.')
        return redirect("products:product_manage")
    context = {
        "product": product,
        "cancel_url": product.get_absolute_url(),
    }
    return render(request, "products/product_confirm_delete.html", context)


@staff_required
@require_http_methods(["GET", "POST"])
def category_create(request):
    """Add a new category."""
    form = CategoryForm(request.POST or None, request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            category = form.save()
            messages.success(
                request, f'The "{category.name}" category has been added.'
            )
            return redirect("products:product_manage")
        messages.error(
            request,
            "The category was not saved. Please fix the highlighted "
            "fields.",
        )
    context = {"form": form, "heading": "Add a category", "category": None}
    return render(request, "products/category_form.html", context)


@staff_required
@require_http_methods(["GET", "POST"])
def category_update(request, slug):
    """Edit an existing category."""
    category = get_object_or_404(Category, slug=slug)
    form = CategoryForm(
        request.POST or None, request.FILES or None, instance=category
    )
    if request.method == "POST":
        if form.is_valid():
            category = form.save()
            messages.success(
                request, f'The "{category.name}" category has been updated.'
            )
            return redirect("products:product_manage")
        messages.error(
            request,
            "Your changes were not saved. Please fix the highlighted "
            "fields.",
        )
    context = {
        "form": form,
        "heading": f"Edit {category.name}",
        "category": category,
    }
    return render(request, "products/category_form.html", context)


@staff_required
@require_POST
def category_delete(request, slug):
    """Delete a category, but only when no products still belong to it."""
    category = get_object_or_404(Category, slug=slug)
    try:
        name = category.name
        category.delete()
    except ProtectedError:
        messages.error(
            request,
            f'"{category.name}" still contains products. Move or delete '
            "them first.",
        )
    else:
        messages.success(request, f'The "{name}" category was deleted.')
    return redirect("products:product_manage")
