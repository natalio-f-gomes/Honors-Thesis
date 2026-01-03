# Resume Analyzer - Complete Deployment Guide - Part 2

###Partially edited by copilot

This guide documents the complete setup of Lambda functions, API Gateway, and backend services for the Resume Analyzer application. This is Part 2 of the deployment process, building upon the infrastructure established in Part 1.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Lambda Layer Setup](#lambda-layer-setup)
4. [IAM Roles and Permissions](#iam-roles-and-permissions)
5. [Parameter Store Configuration](#parameter-store-configuration)
6. [Lambda Functions](#lambda-functions)
7. [API Gateway Setup](#api-gateway-setup)
8. [Testing and Verification](#testing-and-verification)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Completed from Part 1
-  S3 bucket for static website (`resume-analyzer.net`)
-  S3 bucket for user data (`resume-analyzer-user-data`)
-  CloudFront distribution
-  Cognito User Pool configured
-  DynamoDB table (`resume-analyzer-users-resume`)

### Required Tools
- AWS CLI configured with credentials
- Docker Desktop (for building Lambda layers)
- PowerShell (Windows) or Bash (Linux/Mac)
- Python 3.11

### Account Information
- AWS Account ID: `992382508440` (replace with yours)
- AWS Region: `us-east-1`
- API Gateway ID: `q03yktvl4a` (will be created)

---

## Architecture Overview

### Backend Components
```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (REST API)                    │
│              q03yktvl4a.execute-api.us-east-1               │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
  /upload      /get-resume   /get-jobs
     │              │            │
     │              │            │
     ▼              ▼            ▼
┌─────────┐   ┌─────────┐   ┌─────────┐
│Lambda 1 │   │Lambda 2 │   │Lambda 4 │
│ Upload  │   │Get Data │   │Get Jobs │
└────┬────┘   └────┬────┘   └────┬────┘
     │             │              │
     ├─────────────┼──────────────┤
     ▼             ▼              ▼
┌──────────────────────────────────────┐
│           DynamoDB Table             │
│  resume-analyzer-users-resume        │
└──────────────────────────────────────┘
     │             │              │
     ▼             ▼              ▼
┌──────────────────────────────────────┐
│      S3: resume-analyzer-user-data   │
│  ├── USER_ID/resume-N/resume.pdf     │
│  ├── USER_ID/resume-N/resume.json    │
│  └── jobs/USER_ID/resume-N/jobs.json │
└──────────────────────────────────────┘
```

### Lambda Functions Overview
| Function | Purpose | Trigger | Runtime |
|----------|---------|---------|---------|
| `upload-handler` | Process PDF uploads, extract text, parse with Claude AI | API Gateway POST /upload | Python 3.11 |
| `get-user-resumes` | Retrieve all resumes or single resume metadata | API Gateway GET /get-user-resumes, /get-resume | Python 3.11 |
| `get-resume-json` | Fetch parsed resume JSON from S3 | API Gateway GET /get-resume-json | Python 3.11 |
| `get-jobs` | Fetch jobs from RapidAPI, store in S3 | API Gateway POST /get-jobs | Python 3.11 |
| `get-jobs-data` | Retrieve stored jobs from S3 | API Gateway GET /get-jobs-data | Python 3.11 |
| `recommendations-handler` | Generate AI-powered skill gap analysis | API Gateway GET /get-recommendations | Python 3.11 |

---

## Lambda Layer Setup

Lambda layers allow you to package dependencies separately from your function code, making deployments faster and more efficient.

### Step 1: Create Dependencies File

Create `requirements.txt`:
```txt
boto3
PyPDF2
anthropic
requests
```

### Step 2: Create Dockerfile for Layer Building

Create `Dockerfile`:
```dockerfile
FROM public.ecr.aws/lambda/python:3.11

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt -t /python

# Create layer structure
RUN mkdir -p /layer/python
RUN cp -r /python/* /layer/python/

CMD ["echo", "Layer built successfully"]
```

### Step 3: Create Build Script

Create `build-layer.ps1` (PowerShell):
```powershell
# Build Lambda Layer with Docker

Write-Host "Building Lambda Layer..." -ForegroundColor Green

# Build Docker image
docker build -t lambda-layer-builder .

# Create container and copy layer
docker create --name temp-layer lambda-layer-builder
docker cp temp-layer:/layer ./layer
docker rm temp-layer

# Create ZIP
Write-Host "Creating layer ZIP..." -ForegroundColor Green
Compress-Archive -Path ./layer/python -DestinationPath lambda-layer.zip -Force

# Cleanup
Remove-Item -Recurse -Force ./layer

Write-Host "Layer built: lambda-layer.zip" -ForegroundColor Green
```

### Step 4: Build and Upload Layer

```powershell
# Run build script
.\build-layer.ps1
```

```bash
# Upload to AWS (first version)
aws lambda publish-layer-version \
  --layer-name resume-analyzer-dependencies \
  --zip-file fileb://lambda-layer.zip \
  --compatible-runtimes python3.11
```

**Save the LayerVersionArn from output:**
```
arn:aws:lambda:us-east-1:992382508440:layer:resume-analyzer-dependencies:1
```

### Step 5: Update Layer (When Adding New Dependencies)

When you add `requests` later:

```powershell
# Rebuild layer
.\build-layer.ps1

# Upload new version
aws lambda publish-layer-version \
  --layer-name resume-analyzer-dependencies \
  --zip-file fileb://lambda-layer.zip \
  --compatible-runtimes python3.11
```

**New LayerVersionArn (version 2):**
```
arn:aws:lambda:us-east-1:992382508440:layer:resume-analyzer-dependencies:2
```

---

## IAM Roles and Permissions

### Step 1: Create Trust Policy

Create `trust-policy.json`:
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

### Step 2: Create IAM Role

```bash
aws iam create-role \
  --role-name lambda-resume-analyzer-role \
  --assume-role-policy-document file://trust-policy.json
```

### Step 3: Create Permissions Policy

Create `lambda-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::resume-analyzer-user-data/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/resume-analyzer-users-resume"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter"
      ],
      "Resource": "arn:aws:ssm:*:*:parameter/atp-project/django/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "*"
    }
  ]
}
```

### Step 4: Attach Policy to Role

```bash
aws iam put-role-policy \
  --role-name lambda-resume-analyzer-role \
  --policy-name lambda-resume-analyzer-policy \
  --policy-document file://lambda-policy.json
```

---

## Parameter Store Configuration

Store sensitive API keys securely in AWS Systems Manager Parameter Store.

### Claude AI API Key

```bash
aws ssm put-parameter \
  --name "/atp-project/django/CLAUDE_AI_API_KEY" \
  --value "sk-ant-api03-YOUR-KEY-HERE" \
  --type SecureString \
  --description "Claude AI API key for resume parsing"
```

### RapidAPI Key (for Job Search)

```bash
aws ssm put-parameter \
  --name "/atp-project/django/X_RAPID_API_KEY" \
  --value "YOUR_RAPIDAPI_KEY_HERE" \
  --type SecureString \
  --description "RapidAPI key for JSearch job listings"
```

### Verify Parameters

```bash
# List parameters
aws ssm get-parameters-by-path \
  --path "/atp-project/django" \
  --with-decryption

# Test retrieval (without showing value)
aws ssm get-parameter \
  --name "/atp-project/django/CLAUDE_AI_API_KEY" \
  --query "Parameter.Name"
```

---

## Lambda Functions

### Lambda 1: Upload Handler

**Purpose:** Processes resume uploads, extracts text from PDF, parses with Claude AI, stores in S3 and DynamoDB.

#### Code: `lambda1_upload_handler.py`

Key features:
- Validates file size and type
- Extracts text from PDF using PyPDF2
- Sends to Claude AI for structured parsing
- Stores PDF and JSON in S3
- Updates DynamoDB with metadata

#### Create Function

```powershell
# Zip the code
Compress-Archive -Path lambda1_upload_handler.py -DestinationPath lambda1-function.zip -Force
```

```bash
# Create Lambda function
aws lambda create-function \
  --function-name upload-handler \
  --runtime python3.11 \
  --role arn:aws:iam::992382508440:role/lambda-resume-analyzer-role \
  --handler lambda1_upload_handler.lambda_handler \
  --zip-file fileb://lambda1-function.zip \
  --timeout 60 \
  --memory-size 512 \
  --layers arn:aws:lambda:us-east-1:992382508440:layer:resume-analyzer-dependencies:1
```

#### Update Function (After Code Changes)

```powershell
Compress-Archive -Path lambda1_upload_handler.py -DestinationPath lambda1-function.zip -Force
```

```bash
aws lambda update-function-code \
  --function-name upload-handler \
  --zip-file fileb://lambda1-function.zip
```

#### Important: Fix Claude Model ID

If you encounter model not found error, update the model ID in the code:
```python
model="claude-sonnet-4-20250514"  # Correct model ID
```

### Lambda 2: Get User Resumes / Get Resume

**Purpose:** Retrieves all resumes for a user OR single resume metadata from DynamoDB.

#### Code: `get_user_resumes_lambda.py`

Key features:
- Single Lambda handles both endpoints
- Query parameter `resumeId` determines single vs. all resumes
- Converts DynamoDB Decimal types to JSON-compatible types
- Returns metadata only (no S3 JSON content)

#### Create Function

```powershell
Compress-Archive -Path get_user_resumes_lambda.py -DestinationPath get-user-resumes-function.zip -Force
```

```bash
aws lambda create-function \
  --function-name get-user-resumes \
  --runtime python3.11 \
  --role arn:aws:iam::992382508440:role/lambda-resume-analyzer-role \
  --handler get_user_resumes_lambda.lambda_handler \
  --zip-file fileb://get-user-resumes-function.zip \
  --timeout 30 \
  --memory-size 256 \
  --layers arn:aws:lambda:us-east-1:992382508440:layer:resume-analyzer-dependencies:1
```

### Lambda 3: Get Resume JSON

**Purpose:** Fetches parsed resume JSON content from S3.

#### Code: `get_resume_json_lambda.py`

Key features:
- Gets S3 path from DynamoDB metadata
- Retrieves full JSON from S3
- Returns complete resume structure

#### Create Function

```powershell
Compress-Archive -Path get_resume_json_lambda.py -DestinationPath get-resume-json-function.zip -Force
```

```bash
aws lambda create-function \
  --function-name get-resume-json \
  --runtime python3.11 \
  --role arn:aws:iam::992382508440:role/lambda-resume-analyzer-role \
  --handler get_resume_json_lambda.lambda_handler \
  --zip-file fileb://get-resume-json-function.zip \
  --timeout 30 \
  --memory-size 256 \
  --layers arn:aws:lambda:us-east-1:992382508440:layer:resume-analyzer-dependencies:1
```

### Lambda 4: Get Jobs

**Purpose:** Fetches job listings from RapidAPI JSearch, stores in S3 and updates DynamoDB.

#### Code: `get_jobs_lambda.py`

Key features:
- Calls RapidAPI JSearch endpoint
- Searches based on career field, experience level, location
- Stores jobs JSON in S3
- Updates DynamoDB with jobs path and count

#### Create Function

**Note:** Requires layer version 2 (with `requests` package)

```powershell
Compress-Archive -Path get_jobs_lambda.py -DestinationPath get-jobs-function.zip -Force
```

```bash
aws lambda create-function \
  --function-name get-jobs \
  --runtime python3.11 \
  --role arn:aws:iam::992382508440:role/lambda-resume-analyzer-role \
  --handler get_jobs_lambda.lambda_handler \
  --zip-file fileb://get-jobs-function.zip \
  --timeout 30 \
  --memory-size 256 \
  --layers arn:aws:lambda:us-east-1:992382508440:layer:resume-analyzer-dependencies:2
```

### Lambda 5: Get Jobs Data

**Purpose:** Retrieves stored job listings from S3.

#### Code: `get-jobs-data-lambda.py`

Key features:
- Gets jobs S3 path from DynamoDB
- Fetches jobs JSON from S3
- Optionally triggers recommendations Lambda asynchronously

#### Create Function

```powershell
Compress-Archive -Path get-jobs-data-lambda.py -DestinationPath get-jobs-data-function.zip -Force
```

```bash
aws lambda create-function \
  --function-name get-jobs-data \
  --runtime python3.11 \
  --role arn:aws:iam::992382508440:role/lambda-resume-analyzer-role \
  --handler get-jobs-data-lambda.lambda_handler \
  --zip-file fileb://get-jobs-data-function.zip \
  --timeout 30 \
  --memory-size 256 \
  --layers arn:aws:lambda:us-east-1:992382508440:layer:resume-analyzer-dependencies:2
```

### Lambda 6: Recommendations Handler

**Purpose:** Generates AI-powered skills gap analysis using Claude AI.

#### Code: `recommendation_lambda.py`

Key features:
- Analyzes resume against job postings
- Identifies missing skills, certifications, experience
- Generates actionable recommendations
- Stores recommendations in S3
- Returns cached recommendations if already generated

#### Create Function

```powershell
Compress-Archive -Path recommendation_lambda.py -DestinationPath recommendations-function.zip -Force
```

```bash
aws lambda create-function \
  --function-name recommendations-handler \
  --runtime python3.11 \
  --role arn:aws:iam::992382508440:role/lambda-resume-analyzer-role \
  --handler recommendation_lambda.lambda_handler \
  --zip-file fileb://recommendations-function.zip \
  --timeout 60 \
  --memory-size 512 \
  --layers arn:aws:lambda:us-east-1:992382508440:layer:resume-analyzer-dependencies:2
```

---

## API Gateway Setup

### Step 1: Create REST API

```bash
aws apigateway create-rest-api \
  --name resume-analyzer-api \
  --description "Resume Analyzer API" \
  --endpoint-configuration types=REGIONAL
```

**Save the API ID:** `q03yktvl4a`

### Step 2: Get Root Resource ID

```bash
aws apigateway get-resources \
  --rest-api-id q03yktvl4a \
  --query "items[0].id" \
  --output text
```

**Save Root Resource ID:** `c08maqbkki`

### Step 3: Create Cognito Authorizer

```bash
aws apigateway create-authorizer \
  --rest-api-id q03yktvl4a \
  --name cognito-authorizer \
  --type COGNITO_USER_POOLS \
  --provider-arns arn:aws:cognito-idp:us-east-1:992382508440:userpool/us-east-1_05vm9ewwO \
  --identity-source method.request.header.Authorization
```

**Save Authorizer ID:** `g80e7j`

### Step 4: Create CORS Config Files

Create `mock-integration.json`:
```json
{
  "application/json": "{\"statusCode\": 200}"
}
```

Create `cors-response.json` (adjust methods as needed):
```json
{
  "method.response.header.Access-Control-Allow-Headers": "'Content-Type,Authorization'",
  "method.response.header.Access-Control-Allow-Methods": "'GET,POST,OPTIONS'",
  "method.response.header.Access-Control-Allow-Origin": "'*'"
}
```

### Step 5: Create API Resources and Methods

For each Lambda function, follow this pattern:

#### Pattern for POST Endpoints (e.g., /upload)

**1. Create Resource:**
```bash
aws apigateway create-resource \
  --rest-api-id q03yktvl4a \
  --parent-id c08maqbkki \
  --path-part upload
```
Save resource ID: `tova6o`

**2. Create POST Method:**
```bash
aws apigateway put-method \
  --rest-api-id q03yktvl4a \
  --resource-id tova6o \
  --http-method POST \
  --authorization-type COGNITO_USER_POOLS \
  --authorizer-id g80e7j
```

**3. Integrate with Lambda:**
```bash
aws apigateway put-integration \
  --rest-api-id q03yktvl4a \
  --resource-id tova6o \
  --http-method POST \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:992382508440:function:upload-handler/invocations
```

**4. Grant Permission:**
```bash
aws lambda add-permission \
  --function-name upload-handler \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn arn:aws:execute-api:us-east-1:992382508440:q03yktvl4a/*/*
```

**5. Setup OPTIONS (CORS):**
```bash
aws apigateway put-method \
  --rest-api-id q03yktvl4a \
  --resource-id tova6o \
  --http-method OPTIONS \
  --authorization-type NONE

aws apigateway put-integration \
  --rest-api-id q03yktvl4a \
  --resource-id tova6o \
  --http-method OPTIONS \
  --type MOCK \
  --request-templates file://mock-integration.json

aws apigateway put-method-response \
  --rest-api-id q03yktvl4a \
  --resource-id tova6o \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters "method.response.header.Access-Control-Allow-Headers=false,method.response.header.Access-Control-Allow-Methods=false,method.response.header.Access-Control-Allow-Origin=false"

# Update cors-response.json to: "'POST,OPTIONS'"
aws apigateway put-integration-response \
  --rest-api-id q03yktvl4a \
  --resource-id tova6o \
  --http-method OPTIONS \
  --status-code 200 \
  --response-parameters file://cors-response.json
```

#### Pattern for GET Endpoints (e.g., /get-user-resumes)

Same as POST but change:
- `--http-method GET` instead of POST
- Update cors-response.json to: `"'GET,OPTIONS'"`

### Step 6: Complete API Endpoints

Create all endpoints following the pattern above:

| Endpoint | Method | Lambda Function | Resource ID |
|----------|--------|----------------|-------------|
| `/upload` | POST | upload-handler | tova6o |
| `/get-user-resumes` | GET | get-user-resumes | b0fwoy |
| `/get-resume` | GET | get-user-resumes | 9bt3em |
| `/get-resume-json` | GET | get-resume-json | aqxlf1 |
| `/get-jobs` | POST | get-jobs | no8ik0 |
| `/get-jobs-data` | GET | get-jobs-data | x9zmvn |
| `/get-recommendations` | GET | recommendations-handler | [created] |

### Step 7: Deploy API

```bash
aws apigateway create-deployment \
  --rest-api-id q03yktvl4a \
  --stage-name prod \
  --description "Initial deployment with all endpoints"
```

**Your API Base URL:**
```
https://q03yktvl4a.execute-api.us-east-1.amazonaws.com/prod
```

### Step 8: Update Frontend Configuration

Update all JavaScript files with the correct API endpoint:

**Files to update:**
- `js/upload.js`
- `js/account.js`
- `js/parsed-resume.js`
- `js/jobs.js`
- `js/recommendations.js`

Replace old API ID with: `q03yktvl4a`

Example:
```javascript
const API_ENDPOINT = 'https://q03yktvl4a.execute-api.us-east-1.amazonaws.com/prod/upload';
```

### Step 9: Deploy Frontend Changes

```powershell
# Sync to S3
aws s3 sync . s3://resume-analyzer.net/ --exclude ".git/*" --exclude "*.json" --exclude "*.ps1"

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id ABCDEFG12345 \
  --paths "/*"
```

---

## Testing and Verification

### Test Each Lambda Function

#### 1. Test Upload Handler

```bash
# Watch logs
aws logs tail /aws/lambda/upload-handler --follow
```

Upload a PDF through the website and monitor logs for:
-  "Processing upload for user"
-  "Extracting text from PDF"
-  "Parsing resume with Claude AI"
-  "Resume stored successfully"

#### 2. Test Get User Resumes

```bash
aws logs tail /aws/lambda/get-user-resumes --follow
```

Visit account page and check for:
-  "Fetching resumes for user"
-  "Found X resumes"

#### 3. Test Get Resume JSON

```bash
aws logs tail /aws/lambda/get-resume-json --follow
```

Click on a resume to view details:
-  "Getting resume JSON"
-  "Fetching from S3"

#### 4. Test Get Jobs

```bash
aws logs tail /aws/lambda/get-jobs --follow
```

Click "Find Jobs" button:
-  "Finding jobs for: [field] - [level] - [location]"
-  "Saved X jobs to S3"
-  "Updated DynamoDB with jobs path"

#### 5. Test Get Jobs Data

```bash
aws logs tail /aws/lambda/get-jobs-data --follow
```

#### 6. Test Recommendations

```bash
aws logs tail /aws/lambda/recommendations-handler --follow
```

Click "View Recommendations":
-  "Analyzing skills gap with Claude AI"
-  "Analysis complete"
-  "Saved recommendations to S3"

### Verify S3 Storage

```bash
# Check user data bucket structure
aws s3 ls s3://resume-analyzer-user-data/ --recursive

# Expected structure:
# USER_ID/resume-1/resume.pdf
# USER_ID/resume-1/resume.json
# jobs/USER_ID/resume-1/jobs.json
# recommendations/USER_ID/resume-1/recommendations.json
```

### Verify DynamoDB Entries

```bash
# Scan table
aws dynamodb scan --table-name resume-analyzer-users-resume

# Check specific user
aws dynamodb query \
  --table-name resume-analyzer-users-resume \
  --key-condition-expression "user_id = :uid" \
  --expression-attribute-values '{":uid":{"S":"YOUR_USER_ID"}}'
```

### Test API Gateway Endpoints Directly

```bash
# Get ID token from browser localStorage
# Then test endpoints:

curl -H "Authorization: Bearer YOUR_ID_TOKEN" \
  https://q03yktvl4a.execute-api.us-east-1.amazonaws.com/prod/get-user-resumes
```

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: CORS Errors

**Symptoms:**
```
Cross-Origin Request Blocked: The Same Origin Policy disallows...
Status code: 403
```

**Solutions:**

1. Check if OPTIONS method exists:
```bash
aws apigateway get-method \
  --rest-api-id q03yktvl4a \
  --resource-id RESOURCE_ID \
  --http-method OPTIONS
```

2. Verify CORS headers in integration response:
```bash
aws apigateway get-integration-response \
  --rest-api-id q03yktvl4a \
  --resource-id RESOURCE_ID \
  --http-method OPTIONS \
  --status-code 200
```

3. Ensure correct methods in cors-response.json
4. Redeploy API after CORS changes

#### Issue: Lambda 502 Errors

**Symptoms:**
```
Status 502 - Internal Server Error
```

**Solutions:**

1. Check Lambda logs:
```bash
aws logs tail /aws/lambda/FUNCTION_NAME --follow
```

2. Common causes:
   - Syntax errors in code
   - Missing dependencies in layer
   - Timeout (increase to 60s+)
   - Memory issues (increase to 512MB+)
   - Wrong handler name

3. Test Lambda directly:
```bash
aws lambda invoke \
  --function-name FUNCTION_NAME \
  --payload '{"test": true}' \
  response.json
```

#### Issue: Authentication Failed

**Symptoms:**
```
401 Unauthorized or 403 Forbidden
```

**Solutions:**

1. Verify Cognito authorizer is attached:
```bash
aws apigateway get-method \
  --rest-api-id q03yktvl4a \
  --resource-id RESOURCE_ID \
  --http-method GET
```

2. Check ID token is being sent:
   - Open browser DevTools > Network
   - Check Authorization header

3. Verify authorizer configuration:
```bash
aws apigateway get-authorizer \
  --rest-api-id q03yktvl4a \
  --authorizer-id g80e7j
```

#### Issue: Model Not Found (Claude AI)

**Symptoms:**
```
Error code: 404 - 'model: claude-3-5-sonnet-20241022'
```

**Solution:**

Update model ID in Lambda code:
```python
model="claude-sonnet-4-20250514"
```

Then redeploy Lambda.

#### Issue: DynamoDB Decimal Errors

**Symptoms:**
```
Object of type Decimal is not JSON serializable
```

**Solution:**

Add decimal conversion function:
```python
def decimal_to_int(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj
```

#### Issue: S3 Access Denied

**Symptoms:**
```
Access Denied when trying to read/write S3
```

**Solutions:**

1. Verify IAM role has S3 permissions
2. Check bucket policy
3. Verify S3 path format (no leading slash)

#### Issue: Parameter Store Access Denied

**Symptoms:**
```
Error getting API key: AccessDeniedException
```

**Solution:**

Ensure IAM role has SSM permission:
```json
{
  "Effect": "Allow",
  "Action": ["ssm:GetParameter"],
  "Resource": "arn:aws:ssm:*:*:parameter/atp-project/django/*"
}
```

### Viewing Logs

#### CloudWatch Logs

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/FUNCTION_NAME --follow

# Get recent logs
aws logs tail /aws/lambda/FUNCTION_NAME --since 1h

# Filter logs
aws logs tail /aws/lambda/FUNCTION_NAME --filter-pattern "ERROR"
```

#### API Gateway Logs

Enable CloudWatch logging:
```bash
aws apigateway update-stage \
  --rest-api-id q03yktvl4a \
  --stage-name prod \
  --patch-operations \
    op=replace,path=/~1*~1*/logging/loglevel,value=INFO \
    op=replace,path=/~1*~1*/logging/dataTrace,value=true
```

### Debugging Tips

1. **Enable detailed logging** in Lambda code:
```python
print(f"Event: {json.dumps(event)}")
print(f"Context: {vars(context)}")
```

2. **Test with minimal payload** first
3. **Check IAM permissions** - most common issue
4. **Verify environment variables** and Parameter Store
5. **Use AWS X-Ray** for distributed tracing

---

## Performance Optimization

### Lambda Optimizations

1. **Increase memory for faster processing:**
```bash
aws lambda update-function-configuration \
  --function-name upload-handler \
  --memory-size 1024
```

2. **Adjust timeout for long operations:**
```bash
aws lambda update-function-configuration \
  --function-name recommendations-handler \
  --timeout 120
```

3. **Use provisioned concurrency for frequently used functions:**
```bash
aws lambda put-provisioned-concurrency-config \
  --function-name upload-handler \
  --provisioned-concurrent-executions 2 \
  --qualifier $LATEST
```

### API Gateway Optimizations

1. **Enable caching:**
```bash
aws apigateway update-stage \
  --rest-api-id q03yktvl4a \
  --stage-name prod \
  --patch-operations \
    op=replace,path=/cacheClusterEnabled,value=true \
    op=replace,path=/cacheClusterSize,value=0.5
```

2. **Set up API throttling:**
```bash
aws apigateway update-stage \
  --rest-api-id q03yktvl4a \
  --stage-name prod \
  --patch-operations \
    op=replace,path=/throttle/rateLimit,value=100 \
    op=replace,path=/throttle/burstLimit,value=200
```

---

## Cost Optimization

### Estimated Monthly Costs

Based on moderate usage (100 users, 500 requests/day):

| Service | Usage | Cost |
|---------|-------|------|
| Lambda (6 functions) | 15,000 requests, 200ms avg | $0.30 |
| API Gateway | 15,000 requests | $0.05 |
| S3 Storage | 10 GB storage, 1 GB transfer | $0.30 |
| DynamoDB | On-demand, 15K reads/writes | $1.50 |
| CloudWatch Logs | 5 GB logs | $2.50 |
| Parameter Store | 2 parameters | $0.00 |
| **Total** | | **~$5/month** |

### Cost Reduction Tips

1. **Delete old Lambda versions:**
```bash
aws lambda list-versions-by-function \
  --function-name upload-handler \
  --query 'Versions[?Version!=`$LATEST`].Version' \
  | jq -r '.[]' \
  | xargs -I {} aws lambda delete-function --function-name upload-handler:{}
```

2. **Set CloudWatch log retention:**
```bash
aws logs put-retention-policy \
  --log-group-name /aws/lambda/upload-handler \
  --retention-in-days 7
```

3. **Use S3 Lifecycle policies:**
```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket resume-analyzer-user-data \
  --lifecycle-configuration file://lifecycle.json
```

lifecycle.json:
```json
{
  "Rules": [
    {
      "Id": "DeleteOldVersions",
      "Status": "Enabled",
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 30
      }
    }
  ]
}
```

---

## Security Best Practices

###  Current Security Measures

1. **API Authentication:** Cognito User Pools with JWT tokens
2. **Encryption at rest:** S3 and DynamoDB default encryption
3. **Encryption in transit:** HTTPS only via API Gateway
4. **Secrets management:** Parameter Store with encryption
5. **Least privilege IAM:** Lambda role has minimal permissions
6. **Private S3 buckets:** No public access

### Additional Security Recommendations

1. **Enable API Gateway WAF:**
```bash
# Create Web ACL with rate limiting
aws wafv2 create-web-acl \
  --name resume-analyzer-waf \
  --scope REGIONAL \
  --default-action Allow={} \
  --region us-east-1
```

2. **Enable S3 versioning:**
```bash
aws s3api put-bucket-versioning \
  --bucket resume-analyzer-user-data \
  --versioning-configuration Status=Enabled
```

3. **Add CloudTrail logging:**
```bash
aws cloudtrail create-trail \
  --name resume-analyzer-trail \
  --s3-bucket-name my-cloudtrail-bucket
```

4. **Set up CloudWatch Alarms:**
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name lambda-errors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold
```

---

## Monitoring and Alerts

### CloudWatch Dashboard

Create dashboard for monitoring:

```bash
aws cloudwatch put-dashboard \
  --dashboard-name resume-analyzer \
  --dashboard-body file://dashboard.json
```

### Useful CloudWatch Metrics

- `AWS/Lambda` - Invocations, Duration, Errors, Throttles
- `AWS/ApiGateway` - Count, Latency, 4XXError, 5XXError
- `AWS/DynamoDB` - ConsumedReadCapacity, ConsumedWriteCapacity

### Set Up SNS Alerts

```bash
# Create SNS topic
aws sns create-topic --name resume-analyzer-alerts

# Subscribe email
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:992382508440:resume-analyzer-alerts \
  --protocol email \
  --notification-endpoint your-email@example.com
```

---

## Disaster Recovery

### Backup Strategy

1. **DynamoDB Point-in-Time Recovery:**
```bash
aws dynamodb update-continuous-backups \
  --table-name resume-analyzer-users-resume \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true
```

2. **S3 Versioning (already covered)**

3. **Lambda Code Backup:**
   - All code in Git repository
   - Version controlled Lambda layers

### Recovery Procedures

#### Restore DynamoDB Table

```bash
# Restore to point in time
aws dynamodb restore-table-to-point-in-time \
  --source-table-name resume-analyzer-users-resume \
  --target-table-name resume-analyzer-users-resume-restored \
  --restore-date-time 2025-11-01T00:00:00Z
```

#### Restore Lambda Function

```bash
# Redeploy from code
aws lambda update-function-code \
  --function-name upload-handler \
  --zip-file fileb://lambda1-function.zip
```

---

## Next Steps

After completing Part 2, you should have:
-  6 Lambda functions deployed
-  API Gateway with 7 endpoints
-  Full backend processing pipeline
-  AI-powered resume parsing
-  Job search integration
-  Skills gap analysis

### Future Enhancements

1. **Add more Lambda functions:**
   - Email notifications
   - Resume comparison
   - Interview preparation tips

2. **Improve AI analysis:**
   - Fine-tune prompts
   - Add more job sources
   - Industry-specific recommendations

3. **Add analytics:**
   - User behavior tracking
   - Popular career fields
   - Success metrics

4. **Implement CI/CD:**
   - GitHub Actions for auto-deployment
   - Automated testing
   - Blue-green deployments

---

## Summary Commands Reference

### Quick Deploy Lambda

```powershell
# Zip and deploy
Compress-Archive -Path lambda_file.py -DestinationPath function.zip -Force
aws lambda update-function-code --function-name FUNCTION_NAME --zip-file fileb://function.zip
```

### Quick API Deployment

```bash
# Deploy API changes
aws apigateway create-deployment --rest-api-id q03yktvl4a --stage-name prod
```

### Quick Frontend Deploy

```powershell
# Sync and invalidate
aws s3 sync . s3://resume-analyzer.net/ --exclude ".git/*"
aws cloudfront create-invalidation --distribution-id ABCDEFG12345 --paths "/*"
```

### View All Logs

```bash
# Tail all Lambda logs
aws logs tail /aws/lambda/upload-handler --follow &
aws logs tail /aws/lambda/get-user-resumes --follow &
aws logs tail /aws/lambda/get-jobs --follow &
```

---

## Support Resources

- **AWS Documentation:** https://docs.aws.amazon.com/
- **Claude API Docs:** https://docs.anthropic.com/
- **RapidAPI JSearch:** https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
- **Lambda Best Practices:** https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html
- **API Gateway Guide:** https://docs.aws.amazon.com/apigateway/latest/developerguide/

---

**Document Version:** 2.0.0  
**Last Updated:** November 3, 2025  
**Maintained By:** Resume Analyzer Development Team