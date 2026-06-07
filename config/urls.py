"""Main URL configuration."""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # OpenAPI schema + UIs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),

    # JWT auth
    path("api/", include("apps.authentication.urls")),

    # Tender extractor
    path("api/v1/", include("apps.tender_extractor.api.urls")),

    # Usage tracking
    path("api/v1/", include("apps.usage_tracking.api.urls")),
]
