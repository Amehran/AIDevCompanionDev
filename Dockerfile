FROM public.ecr.aws/lambda/python:3.11

# Install build dependencies
RUN yum groupinstall -y "Development Tools" && \
    yum install -y gcc-c++

# Copy requirements first for better caching
COPY requirements-aws.txt ${LAMBDA_TASK_ROOT}

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements-aws.txt

# Copy application code
COPY . ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "main.handler" ]
