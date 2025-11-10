from mangum import Mangum

# Import the FastAPI app instance
from main import app

# Create the underlying Mangum ASGI adapter once.
_asgi_handler = Mangum(app)

def handler(event, context):  # pragma: no cover - AWS entrypoint
	"""AWS Lambda handler.

	Some ad-hoc test events (or older console templates) omit
	requestContext.http.sourceIp for HTTP API (v2) events, which Mangum
	currently expects. We defensively inject a placeholder to avoid
	KeyError and still allow the request to proceed for simple health
	checks or manual tests.
	"""
	try:
		rc = event.get("requestContext") or {}
		http_ctx = rc.get("http") or {}
		if "sourceIp" not in http_ctx:
			# Minimal placeholder; real API Gateway invocations populate this.
			http_ctx["sourceIp"] = "0.0.0.0"
			rc["http"] = http_ctx
			event["requestContext"] = rc
	except Exception:
		# Never fail solely on the defensive patch logic.
		pass
	return _asgi_handler(event, context)
