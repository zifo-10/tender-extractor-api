"""Initial migration for usage_tracking app."""
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="APIUsage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("api_name", models.CharField(db_index=True, max_length=200)),
                ("hour_timestamp", models.DateTimeField(db_index=True, help_text="UTC hour bucket")),
                ("total_hits", models.PositiveIntegerField(default=0)),
                ("success_hits", models.PositiveIntegerField(default=0)),
                ("bad_request_hits", models.PositiveIntegerField(default=0)),
                ("total_input_tokens", models.BigIntegerField(default=0)),
                ("total_output_tokens", models.BigIntegerField(default=0)),
                ("total_cost_usd", models.DecimalField(decimal_places=6, default=0, max_digits=12)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        help_text="Null for anonymous requests.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="api_usages",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "API Usage",
                "verbose_name_plural": "API Usages",
                "ordering": ["-hour_timestamp"],
                "indexes": [models.Index(fields=["api_name", "hour_timestamp"], name="usage_track_api_nam_hour_ts_idx")],
                "unique_together": {("user", "api_name", "hour_timestamp")},
            },
        ),
        migrations.CreateModel(
            name="LLMCallLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("request_id", models.CharField(db_index=True, max_length=255)),
                ("provider", models.CharField(choices=[("groq", "Groq"), ("openai", "OpenAI")], max_length=50)),
                ("model_name", models.CharField(max_length=200)),
                ("input_tokens", models.PositiveIntegerField(default=0)),
                ("output_tokens", models.PositiveIntegerField(default=0)),
                ("cost_usd", models.DecimalField(decimal_places=6, default=0, max_digits=12)),
                ("latency_ms", models.FloatField(default=0)),
                ("success", models.BooleanField(default=True)),
                ("fallback_used", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="llm_call_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "LLM Call Log",
                "verbose_name_plural": "LLM Call Logs",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["request_id"], name="usage_track_request_id_idx"),
                    models.Index(fields=["user", "created_at"], name="usage_track_user_created_idx"),
                ],
            },
        ),
    ]
