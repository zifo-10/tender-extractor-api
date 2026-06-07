from django.urls import path

from .views import DocumentedTokenObtainPairView, DocumentedTokenRefreshView

urlpatterns = [
    path("token/", DocumentedTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", DocumentedTokenRefreshView.as_view(), name="token_refresh"),
]
