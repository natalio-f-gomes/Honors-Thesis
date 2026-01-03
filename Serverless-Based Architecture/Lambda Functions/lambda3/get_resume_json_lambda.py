import json
import boto3

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('resume-analyzer-users-resume')
BUCKET_NAME = 'resume-analyzer-user-data'

def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response(200, {'message': 'OK'})
    
    try:
        user_id = event['requestContext']['authorizer']['claims']['sub']
        resume_id = event.get('queryStringParameters', {}).get('resumeId')
        
        if not resume_id:
            return cors_response(400, {'error': 'Missing resumeId'})
        
        print(f"Getting resume JSON: user_id={user_id}, resume_id={resume_id}")
        
        # Get metadata from DynamoDB to get S3 path
        response = table.get_item(
            Key={
                'user_id': user_id,
                'resume_id': resume_id
            }
        )
        
        item = response.get('Item')
        if not item:
            return cors_response(404, {'error': 'Resume not found'})
        
        json_s3_path = item.get('json_s3_path', '')
        if not json_s3_path:
            return cors_response(400, {'error': 'No JSON path found'})
        
        # Extract S3 key from path (remove s3://bucket/ prefix)
        s3_key = json_s3_path.replace(f's3://{BUCKET_NAME}/', '')
        print(f"Fetching from S3: {s3_key}")
        
        # Get JSON from S3
        s3_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        json_content = s3_response['Body'].read().decode('utf-8')
        
        return cors_response(200, json.loads(json_content))
        
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