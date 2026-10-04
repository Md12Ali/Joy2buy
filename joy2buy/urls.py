"""Root URL configuration for JOY2BUY."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from profiles.urls import auth_patterns, profile_patterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
    path("account/", include(auth_patterns)),
    path(
        "account/",
        include((profile_patterns, "profiles"), namespace="profiles"),
    ),
    path("", include("products.urls")),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )

handler403 = "joy2buy.views.permission_denied"
handler404 = "joy2buy.views.page_not_found"
handler500 = "joy2buy.views.server_error"

admin.site.site_header = "JOY2BUY administration"
admin.site.site_title = "JOY2BUY admin"
admin.site.index_title = "Store management"
