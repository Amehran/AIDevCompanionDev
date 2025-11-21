FROM public.ecr.aws/lambda/python:3.11-arm64

# Set working directory inside the container
WORKDIR /var/task

# Copy and install dependencies
# We are assuming 'requirements.txt' (which includes mangum) contains all Python dependencies
COPY requirements.txt .
# Install packages. Use --platform linux/arm64 to ensure any platform-specific wheels are fetched.
RUN pip install --no-cache-dir -r requirements.txt --platform linux/arm64 --only-binary :all:

# Copy your application code (main.py, src/, app/, etc.)
COPY . .

# CRITICAL FIX: Command to run the FastAPI app using the Mangum handler.
# This tells the Lambda runtime to use the 'mangum.handler' function, 
# which will then look for the 'app' object in the 'main' module (main.py).
# MANGUM_APPLICATION_PATH is the critical environment variable for Mangum.
ENV MANGUM_APPLICATION_PATH="main.app"
CMD [ "mangum.handler" ]