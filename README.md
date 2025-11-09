# AI Dev Companion Backend

Production-ready FastAPI + CrewAI backend providing async code review with rate limiting, structured error handling, and clean architecture.

---

## Architecture Overview

This project follows **Clean/Layered Architecture** with clear separation of concerns:

- **Domain Layer** (`app/domain/`): Core business models (ChatRequest, ChatResponse, Issue, etc.) using Pydantic v2.
- **Service Layer** (`app/services/`): Business logic including `RateLimiter` (per-IP fixed window) and `JobManager` (async task orchestration).
- **API Layer** (`app/api/`): FastAPI routers for health, chat, and job endpoints.
- **Core** (`app/core/`): Configuration (Pydantic Settings), DI singletons, custom exceptions, and global error handlers.
- **CrewAI Integration** (`src/crew.py`): Multi-agent code review workflow with Android/Kotlin focus. Provides stub behavior when dependencies unavailable (test/dev).

**Dependency Injection**: Services instantiated as singletons in `app/core/di.py` and injected at startup (see `main.py`).

---

## Directory Structure

```
ai-dev-companion-backend/
├── main.py               # FastAPI app assembly, routers, error handlers
├── app/
│   ├── api/              # Endpoint routers (health, chat, jobs)
│   ├── core/             # Config (Settings), DI, exceptions, error handlers
│   ├── domain/           # Pydantic models (ChatRequest, ChatResponse, etc.)
│   └── services/         # RateLimiter, JobManager
├── src/
│   └── crew.py           # CrewAI agents and tasks (with fallback stubs)
├── tests/
│   ├── test_api.py       # API integration tests (17 scenarios)
│   └── test_services.py  # Service unit tests (RateLimiter, JobManager)
├── pyproject.toml        # Dependencies + dev tools
├── Dockerfile            # Production container config
└── .env                  # Environment variables (not in repo)
```

---

## Environment Setup

### Prerequisites
- Python 3.11+ (< 3.14)
- pip or uv package manager

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd ai-dev-companion-backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   pip install -e ".[dev]"   # for tests
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and set OPENAI_API_KEY, optionally other keys
   ```

### Required Environment Variables
- `OPENAI_API_KEY` (required): Your OpenAI API key. Use `"dummy"` or `"test"` to trigger stub responses for local testing.
- `MODEL` (optional, default: `gpt-4o-mini`): LLM model name.
- `RATE_LIMIT_PER_MINUTE` (optional, default: `10`): Max requests per IP per minute.
- `MAX_CONCURRENT_JOBS` (optional, default: `100`): Server concurrency guard.

---

## Running the Application

### Development Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Server
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker
```bash
docker build -t ai-dev-companion .
docker run -p 8000:8000 --env-file .env ai-dev-companion
```

---

## API Endpoints

### Health
- `GET /` – Welcome message
- `POST /test` – Connectivity check
- `POST /echo` – Echo payload for client debugging

### Chat (Synchronous)
- `POST /chat?fast=true` – Fast stub response (no LLM)
- `POST /chat` – Full code review (blocks until complete)
  - **Body:** `{"source_code": "...", "code_snippet": "..."}`
  - **Response:** `{"summary": "...", "issues": [...]}`

### Jobs (Asynchronous)
- `POST /chat/submit` – Submit async review job, returns `{"job_id": "uuid"}`
- `GET /chat/status/{job_id}` – Check job status (`queued`, `running`, `done`, `error`)
- `GET /chat/result/{job_id}` – Get result (200 if done, 202 if running, 404/500 on error)
- `DELETE /chat/jobs/cleanup?ttl=3600` – Remove stale jobs

---

## Testing Strategy

### Run Tests
```bash
pytest                      # All tests
pytest tests/test_api.py    # API integration tests
pytest tests/test_services.py  # Service unit tests
pytest -m "not slow"        # Skip long-running tests
```

### Test Coverage
- **API Integration** (`tests/test_api.py`, 17 tests):
  - Fast mode, async job lifecycle, rate limiting, structured errors, edge cases.
- **Service Unit Tests** (`tests/test_services.py`, 6 tests):
  - RateLimiter: window reset, limit enforcement, cleanup.
  - JobManager: lifecycle (queued → running → done/error), cleanup, async execution.

### Test Mode
When `OPENAI_API_KEY` is set to `"dummy"`, `"test"`, or `"placeholder"`, the backend returns deterministic stub responses without invoking external LLMs. This ensures fast, reliable CI/CD tests.

---

## AWS Lambda (Stage 1)

This repo is ready to run on AWS Lambda behind an HTTP API using Mangum.

- Lambda entrypoint: `lambda_handler.py` exposes `handler = Mangum(app)`.
- Minimal runtime deps: `requirements-aws.txt` includes only FastAPI + Mangum (transitives resolved automatically). Heavy, optional packages like CrewAI/ChromaDB are intentionally excluded; the app uses test-safe stubs when those imports are unavailable.
- Packaging script: `scripts/package_lambda.sh` builds a slim zip with site-packages + app code.

### Build the artifact locally
```bash
bash scripts/package_lambda.sh
# Output: lambda_bundle.zip (~5 MB)
```

## CI/CD with GitHub Actions (Stage 2)

Automated deployment pipeline for the `stage` branch using GitHub OIDC (no API keys stored in GitHub).

### Workflow Features
- ✅ Runs tests before deployment
- ✅ Builds Lambda zip package
- ✅ Deploys to AWS Lambda via OIDC
- ✅ Updates environment variables
- ✅ Validates deployment success

### Setup Instructions

**Complete AWS setup guide:** See [`docs/AWS_SETUP.md`](docs/AWS_SETUP.md) for:
- IAM role creation with OIDC trust policy
- Lambda function setup
- GitHub secrets configuration
- API Gateway/Function URL setup
- Troubleshooting guide

**Quick start:**
1. Create IAM role with GitHub OIDC trust policy
2. Create Lambda function (Python 3.11)
3. Add GitHub secrets: `AWS_ROLE_ARN`, `AWS_REGION`, `LAMBDA_FUNCTION_NAME`, `OPENAI_API_KEY`
4. Push to `stage` branch → deployment triggers automatically

**Workflow file:** `.github/workflows/deploy-stage.yml`

---

## Error Handling

All errors return structured JSON with backward-compatible `detail` field:

```json
{
  "error": {
    "type": "rate_limit_exceeded",
    "message": "Too many requests. Try again in 42 seconds.",
    "retry_after": 42
  },
  "detail": "Too many requests. Try again in 42 seconds."
}
```

### Custom Exception Classes
- `RateLimitExceeded` (429)
- `ServerBusy` (503)
- `InvalidInput` (422)
- `JobNotFound` (404)
- `CodeAnalysisError` (500)

Global handlers in `app/core/error_handlers.py` normalize all exceptions and validation errors.

---

## Services & Dependency Injection

### RateLimiter (`app/services/rate_limiter.py`)
- **Strategy**: Fixed window per-IP (60s).
- **API**: `check(ip) -> Optional[int]` returns retry_after or None.
- **Thread-safe**: Uses internal lock.

### JobManager (`app/services/job_manager.py`)
- **Lifecycle**: `create_job() → run_job(coro) → get(job_id) → cleanup(ttl)`.
- **Concurrency**: `active_count()` tracks queued/running jobs.
- **Error Capture**: Stores exception details in job record.

### DI Module (`app/core/di.py`)
Provides singleton instances:
- `rate_limiter = RateLimiter(settings.rate_limit_per_minute)`
- `job_manager = JobManager()`
- `settings = Settings()` (Pydantic Settings)

---

## CrewAI Integration

### Agents
1. **Code Reviewer Agent**: Senior Android analyst (Kotlin, Jetpack Compose, MVVM).
2. **JSON Formatter Agent**: Ensures strict JSON output.

### Tasks
1. **Code Review Task**: Analyze source → produce structured findings.
2. **JSON Formatter Task**: Validate/normalize JSON schema.

### Fallback Behavior
If `crewai` imports fail (e.g., test env without ChromaDB), `src/crew.py` provides stub classes with deterministic JSON responses (`{"summary": "OK (stub)", "issues": []}`).

---

## Future Improvements

1. **App Factory Pattern**: Encapsulate app creation for easier testing/mocking.
2. **Request ID Logging**: Add correlation IDs for distributed tracing.
3. **Persistent Job Store**: Replace in-memory dict with Redis/DB for multi-instance deployments.
4. **Advanced Telemetry**: Integrate OpenTelemetry for metrics/traces.
5. **Webhook Notifications**: Notify clients when async jobs complete.
6. **User Authentication**: Add JWT/OAuth for multi-tenant rate limiting.

---

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and run tests (`pytest`)
4. Commit (`git commit -m 'Add amazing feature'`)
5. Push (`git push origin feature/amazing-feature`)
6. Open a Pull Request

---

## License

[Your license here]

---

## Support

For issues or questions, open a GitHub issue or contact [your-email@example.com].

