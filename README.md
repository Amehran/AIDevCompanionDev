# AI Dev Companion Backend

FastAPI + CrewAI backend.

## Environment variables

- Copy `.env.example` to `.env` and fill in your keys:

```
cp .env.example .env
```

Key vars:
- `LLM_MODEL` (default: `gpt-4o-mini`) – cheaper default model. You can also set `MODEL` or `MODEL_NAME`; the app will pick the first available.
- `OPENAI_API_KEY` (or other provider keys as needed)

For local dev, the app loads `.env` automatically via `python-dotenv`.

## Run locally

```bash
uvicorn main:app --reload
```

## Docker

Build:

```bash
docker build -t ai-dev-companion .
```

Run (pass env without baking secrets into image):

```bash
docker run -d --rm \
	--env-file .env \
	-p 8000:8000 \
	--name ai-dev-companion \
	ai-dev-companion
```

Visit http://localhost:8000

## Notes

- `.dockerignore` excludes `.env` and other local files to keep secrets out of images.
- Python version is constrained to `>=3.11,<3.14` for CrewAI compatibility.
