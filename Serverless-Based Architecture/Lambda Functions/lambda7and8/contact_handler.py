import json
import boto3
from datetime import datetime

sns_client = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

CONTACT_TOPIC_ARN = 'arn:aws:sns:us-east-1:01234567890:resume-analyzer-contact-notifications'

def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response(200, {'message': 'OK'})
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        name = body.get('name', '').strip()
        email = body.get('email', '').strip()
        subject = body.get('subject', '').strip()
        category = body.get('category', 'general')
        message = body.get('message', '').strip()
        
        # Validate required fields
        if not all([name, email, subject, message]):
            return cors_response(400, {'error': 'Missing required fields'})
        
        # Validate email format
        if '@' not in email or '.' not in email:
            return cors_response(400, {'error': 'Invalid email format'})
        
        # Create email notification
        email_subject = f"[Contact Form] {subject}"
        email_body = f"""
New Contact Form Submission

From: {name}
Email: {email}
Category: {category}
Subject: {subject}

Message:
{message}

---
Submitted at: {datetime.utcnow().isoformat()}
        """
        
        # Send SNS notification
        sns_client.publish(
            TopicArn=CONTACT_TOPIC_ARN,
            Subject=email_subject,
            Message=email_body
        )
        
        print(f"Contact form submitted by {email}")
        
        return cors_response(200, {
            'success': True,
            'message': 'Your message has been sent successfully! We will get back to you soon.'
        })
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return cors_response(500, {'error': 'Failed to send message'})

def cors_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }