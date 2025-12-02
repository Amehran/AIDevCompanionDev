---
description: Setup AWS Resources for Docker-based Lambda
---

# Setup AWS Resources

Since you deleted everything, we need to recreate the ECR repository, the Lambda function, and the IAM role.

## Prerequisites
- AWS CLI installed and configured (`aws configure`)
- Docker installed and running

## 1. Create ECR Repository
This is where your Docker images will be stored.

```bash
# Replace 'ai-dev-companion' with your preferred name
aws ecr create-repository --repository-name ai-dev-companion --region us-east-1
```

## 2. Create IAM Role for Lambda
The Lambda needs permissions to run and log to CloudWatch.

1. Create a trust policy file `trust-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

2. Create the role:
```bash
aws iam create-role --role-name ai-dev-companion-role --assume-role-policy-document file://trust-policy.json
```

3. Attach basic execution policy:
```bash
aws iam attach-role-policy --role-name ai-dev-companion-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

4. (Optional) Attach Bedrock permissions if needed:
```bash
aws iam attach-role-policy --role-name ai-dev-companion-role --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
```

## 3. Create Lambda Function (Initial Placeholder)
You cannot create a Lambda from a container image until the image exists in ECR.

1. **Build and Push Initial Image**:
   (Run these commands in your project root)
   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

   # Build
   docker build -t ai-dev-companion .

   # Tag
   docker tag ai-dev-companion:latest <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/ai-dev-companion:latest

   # Push
   docker push <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/ai-dev-companion:latest
   ```

2. **Create Function**:
   ```bash
   aws lambda create-function \
     --function-name ai-dev-companion \
     --package-type Image \
     --code ImageUri=<YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/ai-dev-companion:latest \
     --role arn:aws:iam::<YOUR_ACCOUNT_ID>:role/ai-dev-companion-role \
     --region us-east-1
   ```

## 4. GitHub Secrets
Update your GitHub Repository Secrets with the new values:
- `AWS_ROLE_ARN`: The ARN of the role you created (or a separate OIDC role for GitHub Actions).
- `ECR_REPOSITORY`: `ai-dev-companion`
- `LAMBDA_FUNCTION_NAME`: `ai-dev-companion`
