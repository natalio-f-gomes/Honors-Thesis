import json
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

# AWS Clients only necessary ones
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('resume-analyzer-users-resume')


def decimal_to_int(obj):
    """Convert Decimal to int/float for JSON serialization"""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj


def convert_decimals(obj):
    """Recursively convert all Decimals"""
    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj


def lambda_handler(event, context):
    """Get all resumes OR single resume metadata for a user"""
    
    # Handle CORS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response(200, {'message': 'OK'})
    
    try:
        # Get user info from Cognito authorizer
        user_id = event['requestContext']['authorizer']['claims']['sub']
        
        # Check if specific resume requested
        query_params = event.get('queryStringParameters') or {}
        resume_id = query_params.get('resumeId')
        
        if resume_id:
            # Get single resume
            print(f"Getting resume: user_id={user_id}, resume_id={resume_id}")
            
            response = table.get_item(
                Key={
                    'user_id': user_id,
                    'resume_id': resume_id
                }
            )
            
            item = response.get('Item')
            
            if not item:
                return cors_response(404, {'error': 'Resume not found'})
            
            return cors_response(200, convert_decimals(item))
        
        else:
            # Get all resumes
            print(f"Fetching resumes for user: {user_id}")
            
            response = table.query(
                KeyConditionExpression=Key('user_id').eq(user_id)
            )
            
            items = response.get('Items', [])
            print(f"Found {len(items)} resumes")
            
            # Convert Decimals and format metadata
            resumes = []
            for item in items:
                resume_metadata = {
                    'resume_id': item.get('resume_id'),
                    'resume_number': decimal_to_int(item.get('resume_number', 0)),
                    'file_name': item.get('file_name'),
                    'file_size': decimal_to_int(item.get('file_size', 0)),
                    'career_field': item.get('career_field'),
                    'experience_level': item.get('experience_level'),
                    'preferred_location': item.get('preferred_location'),
                    'upload_date': item.get('upload_date'),
                    'status': item.get('status'),
                    'parsed_name': item.get('parsed_name', ''),
                    'skills_count': decimal_to_int(item.get('skills_count', 0)),
                    'experience_count': decimal_to_int(item.get('experience_count', 0))
                }
                resumes.append(resume_metadata)
            
            # Sort by resume_number
            resumes.sort(key=lambda x: x.get('resume_number', 0))
            
            return cors_response(200, {
                'success': True,
                'count': len(resumes),
                'max_count': 5,
                'resumes': resumes
            })
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return cors_response(500, {
            'success': False,
            'error': 'Failed to fetch resumes',
            'message': str(e)
        })


def cors_response(status_code, body):
    """Return response with CORS headers"""
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