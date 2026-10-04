from django.urls import path

from . import views

app_name = "products"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path(
        "search/suggestions/",
        views.search_suggestions,
        name="search_suggestions",
    ),
    path("manage/", views.product_manage, name="product_manage"),
    path(
        "manage/products/add/", views.product_create, name="product_create"
    ),
    path(
        "manage/products/<slug:slug>/edit/",
        views.product_update,
        name="product_update",
    ),
    path(
        "manage/products/<slug:slug>/delete/",
        views.product_delete,
        name="product_delete",
    ),
    path(
        "manage/categories/add/",
        views.category_create,
        name="category_create",
    ),
    path(
        "manage/categories/<slug:slug>/edit/",
        views.category_update,
        name="category_update",
    ),
    path(
        "manage/categories/<slug:slug>/delete/",
        views.category_delete,
        name="category_delete",
    ),
    path(
        "reviews/<int:pk>/delete/", views.review_delete, name="review_delete"
    ),
    path(
        "products/<slug:slug>/", views.product_detail, name="product_detail"
    ),
    path(
        "products/<slug:slug>/review/", views.review_save, name="review_save"
    ),
]
