import json
import boto3

lambda_client = boto3.client('lambda', region_name='us-east-1')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('resume-analyzer-users-resume')

def trigger_recommendations_async(user_id, resume_id):
    """Asynchronusly trigger recommendations generation"""
    try:
        print(f" Triggering async recommendations for resume {resume_id}")
        
        payload = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'resumeId': resume_id
            },
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': user_id
                    }
                }
            }
        }
        
        # Async invocation
        lambda_client.invoke(
            FunctionName='recommendations-handler',
            InvocationType='Event',
            Payload=json.dumps(payload)
        )
        
        print(f" Async recommendations triggered sucessfully")
        
    except Exception as e:
        print(f" Failed to trigger async recommendations (non-critical): {e}")



def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response(200, {'message': 'OK'})
    
    try:
        user_id = event['requestContext']['authorizer']['claims']['sub']
        resume_id = event['queryStringParameters'].get('resumeId')
        
        if not resume_id:
            return cors_response(400, {'error': 'Missing resumeId'})
        
        # Get metadata from DynamoDB
        response = table.get_item(Key={'user_id': user_id, 'resume_id': resume_id})
        
        if 'Item' not in response:
            return cors_response(404, {'error': 'Resume not found'})
        
        item = response['Item']
        
        # Check if jobs exist
        if 'jobs_s3_path' not in item or not item['jobs_s3_path']:
            return cors_response(404, {
                'error': 'No jobs found', 
                'message': 'Please click "Find Jobs" on the resume page first'
            })
        
        # Parse S3 path
        s3_path = item['jobs_s3_path'].replace('s3://', '')
        bucket, key = s3_path.split('/', 1)
        
        # Get jobs from S3
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        jobs_data = json.loads(obj['Body'].read().decode('utf-8'))
        # Trigger async recommendations generation
        if 'recommendations_s3_path' not in item or not item.get('recommendations_s3_path'):
            # Only trigger if recommendations don't exist yet
            trigger_recommendations_async(user_id, resume_id)
        else:
            print(f"ℹ Recommendations already exist, skipping generation")

        return cors_response(200, jobs_data)
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return cors_response(500, {'error': str(e)})

def cors_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,OPTIONS',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }