from mangum import Mangum

# Import the FastAPI app instance
from main import app

# AWS Lambda entrypoint
handler = Mangum(app)
