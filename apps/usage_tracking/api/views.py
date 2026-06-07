"""Usage tracking read-only API endpoints (admin/superuser only)."""
from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.usage_tracking.models import APIUsage, LLMCallLog
from apps.usage_tracking.api.serializers import APIUsageSerializer, LLMCallLogSerializer


class APIUsageListView(APIView):
    """List aggregated API usage records (admin only)."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Usage Tracking"],
        summary="List hourly API usage aggregates",
        responses={200: APIUsageSerializer(many=True)},
    )
    def get(self, request) -> Response:
        queryset = (
            APIUsage.objects.select_related("user")
            .order_by("-hour_timestamp")[:200]
        )
        serializer = APIUsageSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LLMCallLogListView(APIView):
    """List LLM call logs (admin only)."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        tags=["Usage Tracking"],
        summary="List LLM call logs",
        responses={200: LLMCallLogSerializer(many=True)},
    )
    def get(self, request) -> Response:
        queryset = (
            LLMCallLog.objects.select_related("user")
            .order_by("-created_at")[:200]
        )
        serializer = LLMCallLogSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
