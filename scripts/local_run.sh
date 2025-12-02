#!/bin/bash
# Run the FastAPI app locally for testing

# Change to the project root directory (one level up from this script)
cd "$(dirname "$0")/.." || exit

# Ensure venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements-aws.txt
    .venv/bin/pip install uvicorn
fi

# Activate venv
source .venv/bin/activate

# Run app
echo "Starting local server at http://localhost:8000"
echo "Test with: curl -X POST http://localhost:8000/chat -H 'Content-Type: application/json' -d '{\"source_code\": \"fun main() {}\"}'"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
