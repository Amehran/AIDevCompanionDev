FROM public.ecr.aws/lambda/python:3.11

# Copy requirements and install dependencies
COPY requirements-aws.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements-aws.txt

# Copy application code
COPY . ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD [ "main.handler" ]
