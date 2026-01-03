import json
import boto3
import requests
from datetime import datetime

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
ssm_client = boto3.client('ssm', region_name='us-east-1')
table = dynamodb.Table('resume-analyzer-users-resume')

BUCKET_NAME = 'resume-analyzer-user-data'

def get_rapid_api_key():
    """Get RapidAPI key from Parameter Store"""
    try:
        response = ssm_client.get_parameter(
            Name='/atp-project/django/X_RAPID_API_KEY',
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Error getting API key: {e}")
        return None

def lambda_handler(event, context):
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response(200, {'message': 'OK'})
    
    try:
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # Get parameters from request
        body = json.loads(event.get('body', '{}'))
        resume_id = body.get('resumeId')
        career_field = body.get('careerField')
        experience_level = body.get('experienceLevel')
        location = body.get('location', 'United States')
        resume_number = body.get('resumeNumber')
        
        if not all([resume_id, career_field, experience_level, resume_number]):
            return cors_response(400, {'error': 'Missing required parameters'})
        
        print(f"Finding jobs for: {career_field} - {experience_level} - {location}")
        
        # Get RapidAPI key
        api_key = get_rapid_api_key()
        if not api_key:
            return cors_response(500, {'error': 'API key not found'})
        
        # Call RapidAPI JSearch
        url = "https://jsearch.p.rapidapi.com/search"
        querystring = {
            "query": f"{experience_level} {career_field}",
            "page": "1",
            "num_pages": "1",
            "size": "10",
            "remote_jobs_only": "false",
            "location": location
        }
        
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "jsearch.p.rapidapi.com"
        }
        
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        jobs = data.get('data', [])
        
        if not jobs:
            return cors_response(200, {
                'success': True,
                'message': 'No jobs found',
                'jobs': []
            })
        
        # Save jobs to S3
        s3_key = f"jobs/{user_id}/resume-{resume_number}/jobs.json"
        jobs_data = {
            'jobs': jobs,
            'search_params': {
                'career_field': career_field,
                'experience_level': experience_level,
                'location': location
            },
            'fetched_at': datetime.utcnow().isoformat(),
            'count': len(jobs)
        }
        
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(jobs_data, indent=2),
            ContentType='application/json'
        )
        
        print(f"Saved {len(jobs)} jobs to S3: {s3_key}")
        
        # Update DynamoDB with jobs path
        table.update_item(
            Key={
                'user_id': user_id,
                'resume_id': resume_id
            },
            UpdateExpression='SET jobs_s3_path = :path, jobs_count = :count, jobs_fetched_at = :time',
            ExpressionAttributeValues={
                ':path': f's3://{BUCKET_NAME}/{s3_key}',
                ':count': len(jobs),
                ':time': datetime.utcnow().isoformat()
            }
        )
        
        print(f"Updated DynamoDB with jobs path")
        
        return cors_response(200, {
            'success': True,
            'message': f'Found {len(jobs)} jobs',
            'jobs_count': len(jobs),
            'jobs_s3_path': f's3://{BUCKET_NAME}/{s3_key}'
        })
        
    except requests.RequestException as e:
        print(f"RapidAPI error: {e}")
        return cors_response(500, {'error': f'Job search failed: {str(e)}'})
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
            'Access-Control-Allow-Methods': 'POST,OPTIONS',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }