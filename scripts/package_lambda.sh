#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
BUILD_DIR="$ROOT_DIR/build/lambda"
ARTIFACT="$ROOT_DIR/lambda_bundle.zip"

echo "[package] Cleaning build directory..."
rm -rf "$BUILD_DIR" "$ARTIFACT"
mkdir -p "$BUILD_DIR"

echo "[package] Installing minimal runtime dependencies to build dir..."
# Prefer project venv python if available
if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
	PY="$ROOT_DIR/.venv/bin/python"
else
	PY="$(command -v python3 || command -v python)"
fi

# Ensure we have a Python with pip available
if ! "$PY" -m pip --version >/dev/null 2>&1; then
	ALT="$(command -v python3 || command -v python)"
	if "$ALT" -m pip --version >/dev/null 2>&1; then
		PY="$ALT"
	else
		echo "[package] Error: No Python with pip available." >&2
		exit 1
	fi
fi

"$PY" -m pip install -r "$ROOT_DIR/requirements-aws.txt" -t "$BUILD_DIR" >/dev/null

echo "[package] Copying application code..."
cp "$ROOT_DIR/main.py" "$BUILD_DIR/"
cp "$ROOT_DIR/lambda_handler.py" "$BUILD_DIR/"
cp -R "$ROOT_DIR/app" "$BUILD_DIR/app"
cp -R "$ROOT_DIR/src" "$BUILD_DIR/src"

echo "[package] Creating zip artifact..."
cd "$BUILD_DIR"
zip -q -r "$ARTIFACT" .
cd - >/dev/null

echo "[package] Artifact created at: $ARTIFACT"
du -h "$ARTIFACT" | awk '{print "[package] Artifact size:", $1}'

echo "[package] Done."
