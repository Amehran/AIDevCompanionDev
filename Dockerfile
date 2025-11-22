FROM public.ecr.aws/lambda/python:3.11-arm64
# --- ADD THE FIX HERE ---
RUN yum update -y && \
    yum groupinstall -y "Development Tools" && \
    yum clean all -y
# --- END OF FIX ---
WORKDIR /var/task
COPY requirements-aws.txt .
RUN pip install --no-cache-dir -r requirements-aws.txt
COPY . .
CMD [ "main.handler" ]