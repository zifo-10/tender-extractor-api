"""Usage tracking models — hourly aggregated API usage per user."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class APIUsage(models.Model):
    """
    Hourly-aggregated usage record for a user/API combination.

    One row = one (user, api_name, hour_timestamp) bucket.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="api_usages",
        null=True,
        blank=True,
        help_text="Null for anonymous requests.",
    )
    api_name = models.CharField(max_length=200, db_index=True)
    hour_timestamp = models.DateTimeField(db_index=True, help_text="UTC hour bucket")

    # Hit counters
    total_hits = models.PositiveIntegerField(default=0)
    success_hits = models.PositiveIntegerField(default=0)
    bad_request_hits = models.PositiveIntegerField(default=0)

    # Token counters
    total_input_tokens = models.BigIntegerField(default=0)
    total_output_tokens = models.BigIntegerField(default=0)

    # Cost
    total_cost_usd = models.DecimalField(max_digits=12, decimal_places=6, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "api_name", "hour_timestamp")]
        verbose_name = "API Usage"
        verbose_name_plural = "API Usages"
        ordering = ["-hour_timestamp"]
        indexes = [
            models.Index(fields=["api_name", "hour_timestamp"]),
        ]

    def __str__(self) -> str:
        user_str = self.user.username if self.user else "anonymous"
        return f"{user_str} | {self.api_name} | {self.hour_timestamp}"


class LLMCallLog(models.Model):
    """Per-request LLM call log for detailed cost accounting."""

    PROVIDER_GROQ = "groq"
    PROVIDER_OPENAI = "openai"
    PROVIDER_CHOICES = [
        (PROVIDER_GROQ, "Groq"),
        (PROVIDER_OPENAI, "OpenAI"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="llm_call_logs",
    )
    request_id = models.CharField(max_length=255, db_index=True)
    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
    model_name = models.CharField(max_length=200)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=12, decimal_places=6, default=0)
    latency_ms = models.FloatField(default=0)
    success = models.BooleanField(default=True)
    fallback_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "LLM Call Log"
        verbose_name_plural = "LLM Call Logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["request_id"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.request_id} | {self.provider} | {self.model_name}"
