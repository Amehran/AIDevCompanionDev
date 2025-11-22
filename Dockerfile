FROM public.ecr.aws/lambda/python:3.11-arm64

# Set working directory inside the container
WORKDIR /var/task

# Copy and install dependencies

# We are assuming 'requirements-aws.txt' (which includes mangum) contains all Python dependencies
COPY requirements-aws.txt .
# FIX: Removed --platform and --only-binary flags to prevent conflict with modern pip versions.
# Since we are already running on an ARM64 base image, pip will install the correct wheels.
RUN pip install --no-cache-dir -r requirements-aws.txt


# Copy your application code (main.py, src/, app/, etc.)
COPY . .

# CRITICAL FIX: Command to run the FastAPI app using the Mangum handler.
# This tells the Lambda runtime to use the 'mangum.handler' function, 
# which will then look for the 'app' object in the 'main' module (main.py).
# MANGUM_APPLICATION_PATH is the critical environment variable for Mangum.

CMD [ "main.handler" ]
