import json
import boto3
import PyPDF2
import io
import base64
from datetime import datetime
from anthropic import Anthropic
import re
from typing import Tuple, Dict, Any

# AWS Clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
eventbridge = boto3.client('events') 
ssm_client = boto3.client('ssm')

# Configuration
TABLE_NAME = 'resume-analyzer-users-resume'
BUCKET_NAME = 'resume-analyzer-user-data'
EVENT_BUS_NAME = 'default'
table = dynamodb.Table(TABLE_NAME)

def get_claude_api_key():
    """Get Claude API key from Parameter Store"""
    response = ssm_client.get_parameter(
        Name='/atp-project/django/CLAUDE_AI_API_KEY',
        WithDecryption=True
    )
    return response['Parameter']['Value']

def extract_text_from_pdf(pdf_bytes):
    """Extract text from PDF bytes for validatio only"""
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"[WARNING] PDF extraction error: {e}")
        return ""

def validate_resume_with_claude(resume_text):
    """ONLY validate if this is a valid resume - don't parse it"""
    api_key = get_claude_api_key()
    client = Anthropic(api_key=api_key)

    prompt = f"""Is this a valid resume? Answer with ONLY 'YES' or 'NO'.

A valid resume should contain:
- Contact information (name, email, or phone)
- Work experience OR education OR skills

Resume text:
\"\"\"{resume_text[:3000]}\"\"\"

Answer (YES or NO):"""

    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=10,
        temperature=0,
        messages=[{"role": "user", "content": prompt}]
    )

    response = getattr(msg.content[0], "text", "").strip().upper()
    return response == "YES"

def get_next_resume_number(user_id):
    """Get the next resume number for user"""
    response = table.query(
        KeyConditionExpression='user_id = :uid',
        ExpressionAttributeValues={':uid': user_id}
    )
    
    items = response.get('Items', [])
    
    if len(items) >= 5:
        raise Exception("Resume limit reached (5/5)")
    
    if not items:
        return 1
    
    max_number = max([item.get('resume_number', 0) for item in items])
    return max_number + 1

def trigger_async_processing(resume_id, user_id, resume_number, career_field, experience_level, preferred_location):
    """Trigger Lambda3 (parse) and Lambda3b (fetch jobs) via EventBridge"""
    
    # Event 1: Trigger resume parsing
    eventbridge.put_events(
        Entries=[
            {
                'Source': 'resume-analyzer.upload',
                'DetailType': 'ResumeUploaded',
                'Detail': json.dumps({
                    'resume_id': resume_id,
                    'user_id': user_id,
                    'resume_number': resume_number,
                    'trigger': 'parse_resume'
                }),
                'EventBusName': EVENT_BUS_NAME
            }
        ]
    )
    
    # Event 2: Trigger job fetching
    eventbridge.put_events(
        Entries=[
            {
                'Source': 'resume-analyzer.upload',
                'DetailType': 'ResumeUploaded',
                'Detail': json.dumps({
                    'resume_id': resume_id,
                    'user_id': user_id,
                    'career_field': career_field,
                    'experience_level': experience_level,
                    'preferred_location': preferred_location,
                    'trigger': 'fetch_jobs'
                }),
                'EventBusName': EVENT_BUS_NAME
            }
        ]
    )
    
    print(f" Triggered async processing for resume {resume_id}")

def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response(200, {'message': 'OK'})

    try:
        # Get user info
        claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_id = claims.get('sub')
        user_email = claims.get('email')
        
        if not user_id or not user_email:
            return cors_response(401, {'error': 'Unauthorized'})

        print(f"Processing upload for user: {user_id}")

        # Parse request body
        body = json.loads(event.get('body', '{}'))
        file_data_b64 = body.get('file_data')
        
        if not file_data_b64:
            return cors_response(400, {'error': 'Missing file_data'})
        
        # Decode file
        file_bytes = base64.b64decode(file_data_b64)
        filename = body.get('file_name', 'resume.pdf')
        career_field = body.get('career_field', '')
        experience_level = body.get('experience_level', '')
        preferred_location = body.get('preferred_location', '')
        
        # Check resume limit
        resume_number = get_next_resume_number(user_id)
        print(f"Assigning resume number: {resume_number}")

        # Generate resume_id
        ts = int(datetime.utcnow().timestamp())
        resume_id = f"{user_id}-{resume_number}-{ts}"

        # VALIDATION ONLY - Extract text
        print("Extracting text for validation...")
        resume_text = extract_text_from_pdf(file_bytes)
        
        if not resume_text:
            return cors_response(400, {
                'error': 'Could not extract text from PDF. Please ensure your resume is readable.'
            })

        # VALIDATION ONLY - Check if valid resume
        print("Validating resume with Claude AI...")
        is_valid = validate_resume_with_claude(resume_text)
        
        if not is_valid:
            return cors_response(400, {
                'error': 'This does not appear to be a valid resume. Please upload a document with your work experience, education, or skills.'
            })

        # Save PDF to S3
        pdf_key = f"{user_id}/resume-{resume_number}/{filename}"
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=pdf_key,
            Body=file_bytes,
            ContentType='application/pdf'
        )
        print(f"Saved PDF: {pdf_key}")

        # Save metadata to DynamoDB with status="uploaded"
        item = {
            'user_id': user_id,
            'resume_id': resume_id,
            'resume_number': int(resume_number),
            'user_email': user_email,
            'file_name': filename,
            'upload_date': datetime.utcnow().isoformat(),
            'status': 'uploaded', 
            'progress': 5, 
            'pdf_s3_path': f's3://{BUCKET_NAME}/{pdf_key}',
            'career_field': career_field,
            'experience_level': experience_level,
            'preferred_location': preferred_location,
        }
        table.put_item(Item=item)
        print(f" Saved to DynamoDB: {resume_id}")

        # Trigger async processing (Lambda3 + Lambda3b)
        trigger_async_processing(
            resume_id, user_id, resume_number, 
            career_field, experience_level, preferred_location
        )

        return cors_response(200, {
            'success': True,
            'message': 'Resume uploaded successfully. Processing in background.',
            'data': {
                'resume_id': resume_id,
                'resume_number': resume_number,
                'status': 'processing'
            }
        })

    except Exception as e:
        import traceback
        print(f"ERROR: {str(e)}")
        traceback.print_exc()
        return cors_response(500, {'error': str(e)})

def cors_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        },
        'body': json.dumps(body)
    }