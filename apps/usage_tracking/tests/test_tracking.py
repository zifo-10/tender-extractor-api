"""Tests for usage tracking service and pricing."""
import pytest
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model

from apps.usage_tracking.services.pricing_service import PricingService

User = get_user_model()


class TestPricingService:
    def test_openai_cost_calculation(self):
        cost = PricingService.calculate_cost(
            provider="openai",
            input_tokens=1_000_000,
            output_tokens=1_000_000,
        )
        # 0.40 + 1.60 = 2.00
        assert abs(cost - 2.0) < 0.0001

    def test_groq_cost_calculation(self):
        cost = PricingService.calculate_cost(
            provider="groq",
            input_tokens=1_000_000,
            output_tokens=1_000_000,
        )
        # 0.05 + 0.10 = 0.15
        assert abs(cost - 0.15) < 0.0001

    def test_zero_tokens(self):
        cost = PricingService.calculate_cost(
            provider="openai",
            input_tokens=0,
            output_tokens=0,
        )
        assert cost == 0.0

    def test_unknown_provider_zero_cost(self):
        cost = PricingService.calculate_cost(
            provider="unknown_provider",
            input_tokens=100_000,
            output_tokens=50_000,
        )
        assert cost == 0.0

    def test_small_token_count(self):
        cost = PricingService.calculate_cost(
            provider="openai",
            input_tokens=1000,
            output_tokens=500,
        )
        # 1000/1M * 0.40 + 500/1M * 1.60
        expected = (1000 / 1_000_000 * 0.40) + (500 / 1_000_000 * 1.60)
        assert abs(cost - expected) < 1e-8


@pytest.mark.django_db
class TestUsageTrackingService:
    def test_record_api_hit_creates_bucket(self):
        from apps.usage_tracking.services.tracking_service import UsageTrackingService
        from apps.usage_tracking.models import APIUsage

        user = User.objects.create_user(username="tracker_user", password="pass")

        UsageTrackingService.record_api_hit(
            user=user,
            api_name="/api/v1/tender-extractor",
            success=True,
            bad_request=False,
            input_tokens=100,
            output_tokens=50,
            provider="groq",
            model_name="test-model",
            cost_usd=0.001,
            request_id="req-track-001",
            latency_ms=500.0,
        )

        assert APIUsage.objects.filter(api_name="/api/v1/tender-extractor").exists()
        usage = APIUsage.objects.get(api_name="/api/v1/tender-extractor")
        assert usage.total_hits == 1
        assert usage.success_hits == 1
        assert usage.bad_request_hits == 0
        assert usage.total_input_tokens == 100
        assert usage.total_output_tokens == 50

    def test_multiple_hits_aggregated(self):
        from apps.usage_tracking.services.tracking_service import UsageTrackingService
        from apps.usage_tracking.models import APIUsage

        user = User.objects.create_user(username="agg_user", password="pass")

        for _ in range(3):
            UsageTrackingService.record_api_hit(
                user=user,
                api_name="/api/v1/test-agg",
                success=True,
                bad_request=False,
            )

        usage = APIUsage.objects.get(api_name="/api/v1/test-agg")
        assert usage.total_hits == 3
        assert usage.success_hits == 3

    def test_bad_request_counted(self):
        from apps.usage_tracking.services.tracking_service import UsageTrackingService
        from apps.usage_tracking.models import APIUsage

        user = User.objects.create_user(username="bad_req_user", password="pass")

        UsageTrackingService.record_api_hit(
            user=user,
            api_name="/api/v1/bad-test",
            success=False,
            bad_request=True,
        )

        usage = APIUsage.objects.get(api_name="/api/v1/bad-test")
        assert usage.bad_request_hits == 1
        assert usage.success_hits == 0
