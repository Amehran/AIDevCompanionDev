# AWS Setup for GitHub Actions OIDC Deployment

## IAM Role Trust Policy (GitHub Actions Deploy Role)

Create (or update) the IAM role used by GitHub Actions with this *narrow* trust policy. It restricts assumptions to the `stage` branch only, enforcing branch-based deployment control:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_AWS_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:Amehran/AIDevCompanionDev:ref:refs/heads/stage"
        }
      }
    }
  ]
}
```

**Replace `YOUR_AWS_ACCOUNT_ID`** with your actual AWS account ID.

## IAM Role Permissions Policy (Least Privilege)

Attach this inline policy to the GitHub Actions deploy role. It grants only what the workflow requires (update code/config + read back). Remove broader managed policies like `AWSLambda_FullAccess` if previously attached:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:GetFunction",
  "lambda:GetFunctionConfiguration"
      ],
      "Resource": "arn:aws:lambda:YOUR_REGION:YOUR_AWS_ACCOUNT_ID:function/YOUR_LAMBDA_FUNCTION_NAME"
    }
  ]
}
```

**Replace placeholders:**
- `YOUR_REGION` → e.g. `us-east-1`
- `YOUR_AWS_ACCOUNT_ID` → your 12-digit account ID
- `YOUR_LAMBDA_FUNCTION_NAME` → e.g. `ai-dev-companion-stage`

### Optional: Add Read-Only Log Access (Not usually needed in deploy role)
If your workflow ever needs to inspect recent logs (rare), you can extend with:
```jsonc
// Additional statement (optional)
{
  "Effect": "Allow",
  "Action": [
    "logs:GetLogEvents",
    "logs:DescribeLogStreams"
  ],
  "Resource": "arn:aws:logs:YOUR_REGION:YOUR_AWS_ACCOUNT_ID:log-group:/aws/lambda/YOUR_LAMBDA_FUNCTION_NAME:*"
}
```

Keep this out unless required, to avoid unnecessary expansion of the role's surface area.

## Lambda Execution Role (Runtime) vs Deploy Role

You now have two distinct roles:
- **Execution Role** (e.g. `service-role/ai-dev-companion-stage-role-ui8vqf0e`): assumed by Lambda service when your function runs. Must include managed policy `AWSLambdaBasicExecutionRole` for CloudWatch logging.
- **Deploy Role** (e.g. `GitHubActionsLambdaDeploy`): assumed by GitHub Actions via OIDC. Only needs the limited Lambda update/read permissions above.

Never reuse the execution role as the deploy role—separating them reduces blast radius.

## OIDC Provider Setup (One-time)

If you haven't already set up the GitHub OIDC provider in AWS:

1. Go to **IAM → Identity providers → Add provider**
2. Choose **OpenID Connect**
3. Provider URL: `https://token.actions.githubusercontent.com`
4. Audience: `sts.amazonaws.com`
5. Click **Add provider**

## GitHub Secrets Configuration (Deployment Inputs)

Add these secrets in your GitHub repository settings (**Settings → Secrets and variables → Actions → New repository secret**):

| Secret Name | Value | Example |
|-------------|-------|---------|
| `AWS_ROLE_ARN` | ARN of the IAM role created above | `arn:aws:iam::123456789012:role/GitHubActionsLambdaDeploy` |
| `AWS_REGION` | AWS region where Lambda is deployed (can default to `us-east-1` in workflow) | `us-east-1` |
| `LAMBDA_FUNCTION_NAME` | Name of your Lambda function | `ai-dev-companion-stage` |
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-...` |
| `MODEL` | (Optional) LLM model name | `gpt-4o-mini` |
| `RATE_LIMIT_PER_MINUTE` | (Optional) Rate limit | `10` |
| `MAX_CONCURRENT_JOBS` | (Optional) Max concurrent jobs | `100` |

## Lambda Function Setup

### Option 1: Create via AWS Console

1. Go to **Lambda → Create function**
2. Choose **Author from scratch**
3. Function name: `ai-dev-companion-stage`
4. Runtime: **Python 3.11**
5. Architecture: **x86_64**
6. Click **Create function**
7. Under **Configuration → General configuration**:
   - Memory: 512 MB (adjust based on needs)
   - Timeout: 30 seconds (or higher for long-running tasks)
8. Under **Configuration → Function URL** (or set up API Gateway):
   - Click **Create function URL**
   - Auth type: **NONE** (or **AWS_IAM** if you want authentication)
   - Click **Save**

### Option 2: Create via AWS CLI

```bash
aws lambda create-function \
  --function-name ai-dev-companion-stage \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_handler.handler \
  --timeout 30 \
  --memory-size 512 \
  --region us-east-1
```

**Note:** You'll need a separate execution role for Lambda itself (different from the GitHub Actions deployment role).

## API Gateway HTTP API (Alternative to Function URL)

If you prefer API Gateway over Function URL:

```bash
# Create HTTP API
aws apigatewayv2 create-api \
  --name ai-dev-companion-stage \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:YOUR_AWS_ACCOUNT_ID:function/ai-dev-companion-stage

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
  --function-name ai-dev-companion-stage \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com
```

## Testing the Deployment

After the workflow runs:

1. Check **GitHub Actions** tab for deployment status
2. Get your Lambda Function URL or API Gateway endpoint
3. Test with:

```bash
curl -X POST https://YOUR_FUNCTION_URL/chat?fast=true \
  -H "Content-Type: application/json" \
  -d '{"source_code": "test", "code_snippet": "test"}'
```

Expected response:
```json
{
  "summary": "OK (stub)",
  "issues": []
}
```

## Cost Estimate (Recap)

- **Lambda**: Free tier covers first 1M requests/month + 400,000 GB-seconds compute
- **API Gateway HTTP API**: Free tier covers first 1M calls/month
- **CloudWatch Logs**: Free tier covers first 5GB/month
- **GitHub Actions**: 2,000 minutes/month free for public repos, 500 for private

**Total estimated cost for low-traffic demo: $0 - $5/month**

## Troubleshooting & Hardening

### Workflow fails with "AssumeRoleWithWebIdentity failed"
- Verify OIDC provider is set up correctly
- Check trust policy `sub` condition matches your repo and branch exactly
- Ensure `AWS_ROLE_ARN` secret is correct

### Deployment succeeds but Lambda returns errors
- Check CloudWatch Logs for the function
- Verify environment variables are set correctly
- Test locally with: `python -c "from lambda_handler import handler; print(handler)"`

### Import errors in Lambda
- Ensure `requirements-aws.txt` includes all runtime dependencies
- Check that `scripts/package_lambda.sh` ran successfully
- Verify zip includes both code and dependencies

## Next Steps & Hardening Checklist

1. ✅ Create IAM role with trust policy above
2. ✅ Set up OIDC provider (if not already done)
3. ✅ Create Lambda function
4. ✅ Add GitHub secrets
5. ✅ Push to `stage` branch to trigger first deployment
6. ✅ Test the deployed endpoint
7. Narrow trust policy to only required branches (already set to `stage`)
8. Confirm deploy role policy is least-privilege (remove legacy broad policies)
9. Add CloudWatch alarms (e.g., Errors > 0, Duration p95) for production readiness
10. (Optional) Enable concurrency controls or reserved concurrency on Lambda
11. (Optional) Use Parameter Store or Secrets Manager for sensitive config instead of plain env vars

---
### Example Final Deploy Role Policies (Complete Bundle)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:GetFunction",
        "lambda:GetFunctionConfiguration"
      ],
      "Resource": "arn:aws:lambda:us-east-1:YOUR_AWS_ACCOUNT_ID:function:ai-dev-companion-stage"
    }
  ]
}
```

### Example Final Trust Policy (Stage Branch Only)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_AWS_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:Amehran/AIDevCompanionDev:ref:refs/heads/stage"
        }
      }
    }
  ]
}
```

---
**Security Recap:**
- Separate execution vs deployment roles ✔️
- Narrow OIDC trust to one branch ✔️
- Least privilege Lambda actions ✔️
- Logging via `AWSLambdaBasicExecutionRole` ✔️
- Pending (optional): alarms, secret rotation, stricter branch protections.
