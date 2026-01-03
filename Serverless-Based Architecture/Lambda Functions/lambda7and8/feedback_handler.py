import json
import boto3
from datetime import datetime

sns_client = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

FEEDBACK_TOPIC_ARN = 'arn:aws:sns:us-east-1:01234567890:resume-analyzer-feedback-notifications'

def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response(200, {'message': 'OK'})
    
    try:
        # Get user info from Cognito
        user_id = event['requestContext']['authorizer']['claims']['sub']
        user_email = event['requestContext']['authorizer']['claims'].get('email', 'Unknown')
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        rating = body.get('rating', 0)
        category = body.get('category', '').strip()
        message = body.get('message', '').strip()
        
        # Validate
        if not all([rating, category, message]):
            return cors_response(400, {'error': 'Missing required fields'})
        
        if rating < 1 or rating > 5:
            return cors_response(400, {'error': 'Invalid rating'})
        
        if len(message) < 10 or len(message) > 1000:
            return cors_response(400, {'error': 'Message must be between 10 and 1000 characters'})
        
        # Create star rating display
        stars = '' * rating + '' * (5 - rating)
        
        # Create email notification
        email_subject = f"[Feedback] {rating} - {category}"
        email_body = f"""
New Feedback Submission

User: {user_email}
User ID: {user_id}
Rating: {stars} ({rating}/5)
Category: {category}

Feedback:
{message}

---
Submitted at: {datetime.utcnow().isoformat()}
        """
        
        # Send SNS notification
        sns_client.publish(
            TopicArn=FEEDBACK_TOPIC_ARN,
            Subject=email_subject,
            Message=email_body
        )
        
        print(f"Feedback submitted by {user_email} - Rating: {rating}")
        
        return cors_response(200, {
            'success': True,
            'message': 'Thank you for your feedback! We appreciate your input.'
        })
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return cors_response(500, {'error': 'Failed to submit feedback'})

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