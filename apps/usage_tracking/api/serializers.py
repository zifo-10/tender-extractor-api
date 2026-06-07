from rest_framework import serializers

from apps.usage_tracking.models import APIUsage, LLMCallLog


class APIUsageSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = APIUsage
        fields = [
            "id",
            "user",
            "api_name",
            "hour_timestamp",
            "total_hits",
            "success_hits",
            "bad_request_hits",
            "total_input_tokens",
            "total_output_tokens",
            "total_cost_usd",
            "updated_at",
        ]


class LLMCallLogSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = LLMCallLog
        fields = [
            "id",
            "user",
            "request_id",
            "provider",
            "model_name",
            "input_tokens",
            "output_tokens",
            "cost_usd",
            "latency_ms",
            "success",
            "fallback_used",
            "created_at",
        ]
