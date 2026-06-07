"""
Authentication views — thin wrappers around SimpleJWT with drf-spectacular docs.
"""
from __future__ import annotations

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class DocumentedTokenObtainPairView(TokenObtainPairView):
    """JWT token obtain endpoint."""

    @extend_schema(
        tags=["Authentication"],
        summary="Obtain JWT access and refresh tokens",
        description=(
            "Provide valid Django user credentials to receive a JWT access token "
            "(short-lived) and a refresh token (longer-lived)."
        ),
        responses={
            200: OpenApiResponse(
                description="Tokens issued",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "access": "eyJhbGci...",
                            "refresh": "eyJhbGci...",
                        },
                    )
                ],
            ),
            401: OpenApiResponse(description="Invalid credentials"),
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class DocumentedTokenRefreshView(TokenRefreshView):
    """JWT token refresh endpoint."""

    @extend_schema(
        tags=["Authentication"],
        summary="Refresh JWT access token",
        description="Exchange a valid refresh token for a new access token.",
        responses={
            200: OpenApiResponse(
                description="New access token issued",
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"access": "eyJhbGci..."},
                    )
                ],
            ),
            401: OpenApiResponse(description="Refresh token invalid or expired"),
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
