
# LLM-Powered Tender Extractor API

A production-grade Django REST Framework API that extracts structured data from tender, RFP, and RFQ documents using Large Language Models (Groq primary, OpenAI fallback).

---

## Features

- **JWT-protected API** — Obtain tokens via `/api/token/`
- **LLM extraction** — Groq (primary) → OpenAI (fallback) with automatic failover
- **Structured outputs** — Pydantic v2 schema validation on all LLM responses
- **Graceful degradation** — Returns a valid empty response if all providers fail (HTTP 200)
- **Usage tracking** — Per-user, per-hour aggregated hit/token/cost tracking in PostgreSQL
- **Cost accounting** — Configurable per-million-token pricing per provider
- **Structured JSON logging** — Every request, LLM call, and fallback event is logged
- **Slack alerting** — Notifies on total provider failure or unexpected errors
- **OpenAPI/Swagger UI** — Full interactive documentation at `/api/docs/`
- **Docker Compose** — Single-command startup: `docker compose up --build`

---

## Quick Start

### 1. Clone and configure

```bash
cp .env.example .env
# Edit .env with your GROQ_API_KEY and OPENAI_API_KEY
```

### 2. Start with Docker Compose

```bash
docker compose up --build
```

This starts:
- PostgreSQL 16 (with health check)
- Django API on http://localhost:8000

Migrations are applied automatically on startup.

### 3. Create a superuser

```bash
docker compose exec api python scripts/create_superuser.py
# Default: admin / admin123 (override via env vars)
```

### 4. Access Swagger UI

Open http://localhost:8000/api/docs/

---

## API Reference

### Authentication

**Obtain tokens**
```http
POST /api/token/
Content-Type: application/json

{"username": "admin", "password": "admin123"}
```

Response:
```json
{"access": "eyJ...", "refresh": "eyJ..."}
```

**Refresh token**
```http
POST /api/token/refresh/
Content-Type: application/json

{"refresh": "eyJ..."}
```

---

### Tender Extraction

```http
POST /api/v1/tender-extractor/
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request body:**
```json
{
  "request_id": "req-001",
  "text": "Full tender document text...",
  "output_language": "Arabic"
}
```

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `request_id` | string | Yes | — | Unique request identifier |
| `text` | string | Yes | — | Tender document plain text (≥20 chars) |
| `output_language` | string | No | `Arabic` | `Arabic` or `English` |

**Success response (200):**
```json
{
  "request_id": "req-001",
  "tender": {
    "title": "Supply of IT Equipment",
    "issuer": "Ministry of Finance",
    "reference_number": "MOF-2024-001",
    "publication_date": "2024-01-15",
    "submission_deadline": "2024-02-15",
    "budget": {"amount": 500000.0, "currency": "SAR"},
    "scope_of_work": "Supply and installation of servers",
    "key_requirements": ["ISO 9001 certified"],
    "eligibility_criteria": ["Registered in KSA"],
    "evaluation_criteria": ["Technical 60%", "Financial 40%"],
    "deliverables": ["Equipment", "Installation", "Training"],
    "contact": {"name": "Ahmed", "email": "a@mof.sa", "phone": "+966"}
  },
  "llm_general_fields": {
    "api_time": 1.23,
    "input_tokens": 1500,
    "output_tokens": 400,
    "model_name": "openai/gpt-oss-120b"
  }
}
```

**Validation error (400):**
```json
{"response_code": 1002, "message": "text field is required"}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 1001 | `request_id` field is required |
| 1002 | `text` field is required |
| 1003 | Invalid `output_language` value |
| 1004 | `text` too short (< 20 characters) |
| 2001 | Authentication failed |
| 2002 | Permission denied |
| 2003 | Token expired |

---

## Project Structure

```
tender-extractor-api/
├── config/
│   ├── settings/
│   │   └── base.py           # All settings (loaded from env)
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── authentication/       # JWT views + URL routing
│   ├── tender_extractor/
│   │   ├── api/              # DRF views, serializers, URLs
│   │   ├── llm/              # BaseLLMClient, GroqLLMClient, OpenAILLMClient, Orchestrator
│   │   ├── prompts/          # PromptBuilder
│   │   ├── schemas/          # Pydantic v2 schemas
│   │   ├── services/         # TenderExtractionService
│   │   ├── validators/       # LLMJSONValidator
│   │   └── tests/
│   └── usage_tracking/
│       ├── api/              # Admin read-only endpoints
│       ├── models.py         # APIUsage, LLMCallLog
│       ├── middleware.py     # Per-request tracking
│       ├── services/         # UsageTrackingService, PricingService
│       └── tests/
│
├── shared/
│   ├── exceptions/           # Custom exception classes + DRF handler
│   ├── integrations/         # SlackWebhookClient
│   ├── logging/              # JSONFormatter, request_logger
│   └── utils/
│
├── scripts/
│   └── create_superuser.py
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## LLM Architecture

```
Request
  │
  ▼
PromptBuilder.build()          # Provider-independent prompt
  │
  ▼
LLMOrchestrator.extract()
  ├─► GroqLLMClient             # Primary: Groq openai/gpt-oss-120b
  │     └─► JSON mode + Pydantic validation
  │
  └─► OpenAILLMClient (fallback) # Fallback: OpenAI gpt-4.1-mini
        └─► Structured Outputs (beta.parse) + Pydantic validation
              │
              ▼
        LLMJSONValidator         # Schema validation, date normalisation,
                                 # array defaults, unknown field removal
              │
              ▼
        TenderSchema             # Fully typed Pydantic model
```

---

## Running Tests

```bash
# Local (requires PostgreSQL or uses in-memory SQLite via conftest.py)
pip install -r requirements.txt
pytest

# With coverage report
pytest --cov=apps --cov=shared --cov-report=term-missing

# Inside Docker
docker compose exec api pytest
```

---

## Environment Variables

See `.env.example` for the complete list. Key variables:

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` / `False` |
| `POSTGRES_*` | Database connection |
| `GROQ_API_KEY` | Groq API key |
| `GROQ_MODEL` | Groq model ID (default: `openai/gpt-oss-120b`) |
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENAI_MODEL` | OpenAI model ID (default: `gpt-4.1-mini`) |
| `OPENAI_INPUT_COST_PER_MILLION` | USD per million input tokens |
| `OPENAI_OUTPUT_COST_PER_MILLION` | USD per million output tokens |
| `GROQ_INPUT_COST_PER_MILLION` | USD per million input tokens |
| `GROQ_OUTPUT_COST_PER_MILLION` | USD per million output tokens |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL (optional) |
| `LOG_LEVEL` | Logging level (default: `INFO`) |

---

## Usage Tracking (Admin)

Admin endpoints (superuser only):

```http
GET /api/v1/usage/              # Hourly aggregated usage
GET /api/v1/usage/llm-calls/    # Per-request LLM call logs
```

---

## License

MIT
