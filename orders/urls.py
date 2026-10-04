from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout, name="checkout"),
    path("manage/", views.order_manage, name="order_manage"),
    path("<str:transaction_id>/", views.order_detail, name="order_detail"),
    path(
        "<str:transaction_id>/cancel/",
        views.order_cancel,
        name="order_cancel",
    ),
    path(
        "<str:transaction_id>/status/",
        views.order_status_update,
        name="order_status_update",
    ),
]
