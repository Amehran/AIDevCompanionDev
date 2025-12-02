# Testing Guide

## Setup

Install test dependencies:

```bash
poetry install --with dev
```

Or with pip:
```bash
pip install pytest pytest-asyncio httpx
```

## Running Tests

### Run all tests
```bash
poetry run pytest
```

### Run with coverage
```bash
poetry run pytest --cov=. --cov-report=html
```

### Run specific test file
```bash
poetry run pytest tests/test_api.py
```

### Run specific test
```bash
poetry run pytest tests/test_api.py::test_rate_limit_per_ip
```

### Skip slow tests
```bash
poetry run pytest -m "not slow"
```

### Run only slow tests
```bash
poetry run pytest -m slow
```

### Verbose output
```bash
poetry run pytest -v -s
```

## Test Categories

### Basic Endpoints (`test_root_endpoint`, `test_echo_endpoint`, etc.)
- Fast tests (<1s each)
- No external dependencies
- Test basic HTTP functionality

### Async Job Flow (`test_full_job_flow`, `test_job_status_not_found`)
- Moderate speed (5-30s per test)
- Requires AWS Bedrock API key in `.env`
- Tests real Bedrock LLM integration

### Rate Limiting (`test_rate_limit_per_ip`, `test_concurrent_jobs_limit`)
- Fast to moderate (1-5s)
- Tests per-IP and global concurrency guards
- Validates error response structure

### Structured Errors (`test_chat_structured_error_on_exception`)
- Fast (<1s)
- Validates JSON error payloads

## Environment Variables

Tests use the same `.env` file as the application:

```bash
BEDROCK_API_KEY=...
BEDROCK_REGION=us-east-1
MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
RATE_LIMIT_PER_MINUTE=5
MAX_CONCURRENT_JOBS=3
```

For tests, you may want lower rate limits to make tests run faster.

## Continuous Integration

Example GitHub Actions workflow:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install poetry
          poetry install --with dev
      - name: Run tests
        env:
          BEDROCK_API_KEY: ${{ secrets.BEDROCK_API_KEY }}
          BEDROCK_REGION: ${{ secrets.BEDROCK_REGION }}
          MODEL_ID: ${{ secrets.MODEL_ID }}
        run: poetry run pytest -m "not slow"
```

## Troubleshooting

### Import errors
Make sure you're in the project root and have installed dependencies:
```bash
poetry install --with dev
```

### Rate limit test failures
If `test_rate_limit_per_ip` fails, check that `RATE_LIMIT_PER_MINUTE` in your environment matches the test expectations (default 5).

### Slow test timeouts
Increase timeout in `test_full_job_flow`:
```python
max_wait = 60  # Increase this if LLM is slow
```

## Writing New Tests

Add tests to `tests/test_api.py` or create new test files following the `test_*.py` pattern.

Use the `client` fixture for making requests:
```python
def test_my_endpoint(client):
    response = client.get("/my-endpoint")
    assert response.status_code == 200
```

Mark slow tests:
```python
@pytest.mark.slow
def test_long_running_operation(client):
    # ...
```
