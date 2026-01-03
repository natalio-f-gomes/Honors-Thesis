import json
import boto3
from datetime import datetime

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
ssm_client = boto3.client('ssm', region_name='us-east-1')
table = dynamodb.Table('resume-analyzer-users-resume')

BUCKET_NAME = 'resume-analyzer-user-data'

def get_claude_api_key():
    """Get Claude API key from Parameter Store"""
    try:
        response = ssm_client.get_parameter(
            Name='/atp-project/django/CLAUDE_AI_API_KEY',
            WithDecryption=True
        )
        return response['Parameter']['Value']
    except Exception as e:
        print(f"Error getting API key: {e}")
        return None


def create_recommendation_prompt(resume_data, jobs_data):
    """Create prompt for Claude to analyze skills gap"""
    
    jobs_summary = []
    for job in jobs_data.get('jobs', [])[:10]:  # Analyze top 10 jobs
        jobs_summary.append({
            'title': job.get('job_title', 'N/A'),
            'company': job.get('employer_name', 'N/A'),
            'highlights': job.get('job_highlights', {})
        })
    
    prompt = f"""Analyze this resume against these job postings and provide skill gap recommendations.

RESUME DATA:
Name: {resume_data.get('name', 'N/A')}
Skills: {', '.join(resume_data.get('skills', []))}
Education: {json.dumps(resume_data.get('education', []), indent=2)}
Experience: {json.dumps(resume_data.get('experience', []), indent=2)}

JOB POSTINGS ANALYZED:
{json.dumps(jobs_summary, indent=2)}

Provide a comprehensive skills gap analysis as JSON:

{{
  "missing_technical_skills": ["skill1", "skill2"],
  "missing_soft_skills": ["soft skill1", "soft skill2"],
  "missing_education": ["degree or course"],
  "missing_certifications": ["cert1", "cert2"],
  "missing_experience": ["experience type"],
  "recommended_actions": [
    "Specific action 1",
    "Specific action 2"
  ],
  "priority_skills": ["top priority skill1", "top priority skill2"],
  "learning_resources": [
    {{"skill": "skill name", "resource": "recommended platform or course"}}
  ]
}}

Focus on:
1. Most frequently mentioned skills in job postings that are missing from resume
2. Certifications commonly required
3. Education gaps if any
4. Practical, actionable recommendations
5. Prioritize skills by market demand

Return only valid JSON."""

    return prompt


def analyze_with_claude(resume_data, jobs_data):
    """Call Claude AI for skills gap analysis"""
    try:
        from anthropic import Anthropic
    except ImportError:
        return {"error": "Anthropic SDK not available. Check the lambda layer"}
    
    api_key = get_claude_api_key()
    if not api_key:
        return {"error": "Claude API key not found"}
    
    print("Analyzing skills gap with Claude AI...")
    
    try:
        client = Anthropic(api_key=api_key)
        prompt = create_recommendation_prompt(resume_data, jobs_data)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = ""
        for block in message.content:
            if hasattr(block, 'text'):
                response_text += block.text
        
        # Parse JSON response
        try:
            # Remove markdown code blocks if present
            if response_text.strip().startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            recommendations = json.loads(response_text.strip())
            
            # Add metadata
            recommendations['analysis_metadata'] = {
                'timestamp': datetime.utcnow().isoformat(),
                'jobs_analyzed': len(jobs_data.get('jobs', [])),
                'method': 'claude_ai_analysis'
            }
            
            print(f" Analysis complete - {len(recommendations.get('missing_technical_skills', []))} technical skills identified")
            return recommendations
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse Claude response: {e}")
            return {"error": "Failed to parse AI response", "raw": response_text[:500]}
    
    except Exception as e:
        print(f"Error calling Claude: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Claude API error: {str(e)}"}


def lambda_handler(event, context):
    """
    Recommendation handler - retrieves existing or generates new recommendations
    """
    print("=" * 80)
    print("RECOMMENDATION HANDLER - Starting")
    print("=" * 80)
    
    if event.get('httpMethod') == 'OPTIONS':
        return cors_response(200, {'message': 'OK'})
    
    try:
        user_id = event['requestContext']['authorizer']['claims']['sub']
        resume_id = event['queryStringParameters'].get('resumeId')
        
        if not resume_id:
            return cors_response(400, {'error': 'Missing resumeId'})
        
        print(f"Fetching recommendations for resume {resume_id}")
        
        # Get resume metadata from DynamoDB
        response = table.get_item(Key={'user_id': user_id, 'resume_id': resume_id})
        
        if 'Item' not in response:
            return cors_response(404, {'error': 'Resume not found'})
        
        item = response['Item']
        
        # Check if recomendations already exist in S3
        if 'recommendations_s3_path' in item and item['recommendations_s3_path']:
            print(f" Found existing recommendations, retrieving from S3...")
            
            # Parse S3 path and fetch
            rec_s3_path = item['recommendations_s3_path'].replace('s3://', '')
            rec_bucket, rec_key = rec_s3_path.split('/', 1)
            
            rec_obj = s3_client.get_object(Bucket=rec_bucket, Key=rec_key)
            recommendations = json.loads(rec_obj['Body'].read().decode('utf-8'))
            
            print(f" Retrieved existing recommendations from S3")
            
            return cors_response(200, {
                'success': True,
                'message': 'Recommendations retrieved successfully',
                'recommendations': recommendations,
                'cached': True
            })
        
        # If no recommendations exist, generate them
        print(f"No existing recommendations found, generating new ones...")
        
        resume_number = item.get('resume_number', 1)
        
        # Check if jobs exist
        if 'jobs_s3_path' not in item or not item['jobs_s3_path']:
            return cors_response(404, {'error': 'No jobs found. Please run job search first.'})
        
        # Get resume JSON from S3
        if 'json_s3_path' not in item or not item['json_s3_path']:
            return cors_response(404, {'error': 'Resume not parsed yet'})
        
        print("Fetching resume and jobs data from S3...")
        
        # Parse S3 paths
        resume_s3_path = item['json_s3_path'].replace('s3://', '')
        resume_bucket, resume_key = resume_s3_path.split('/', 1)
        
        jobs_s3_path = item['jobs_s3_path'].replace('s3://', '')
        jobs_bucket, jobs_key = jobs_s3_path.split('/', 1)
        
        # Get resume data
        resume_obj = s3_client.get_object(Bucket=resume_bucket, Key=resume_key)
        resume_data = json.loads(resume_obj['Body'].read().decode('utf-8'))
        
        # Get jobs data
        jobs_obj = s3_client.get_object(Bucket=jobs_bucket, Key=jobs_key)
        jobs_data = json.loads(jobs_obj['Body'].read().decode('utf-8'))
        
        print(f" Loaded resume with {len(resume_data.get('skills', []))} skills")
        print(f" Loaded {len(jobs_data.get('jobs', []))} jobs")
        
        # Analyze with Claude
        recommendations = analyze_with_claude(resume_data, jobs_data)
        
        if 'error' in recommendations:
            print(f" Analysis failed: {recommendations['error']}")
            return cors_response(500, recommendations)
        
        # Save recommendations to S3
        recommendations_key = f"recommendations/{user_id}/resume-{resume_number}/recommendations.json"
        
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=recommendations_key,
            Body=json.dumps(recommendations, indent=2),
            ContentType='application/json'
        )
        
        print(f" Saved recommendations to S3: {recommendations_key}")
        
        # Update DynamoDB with recommendations path
        table.update_item(
            Key={
                'user_id': user_id,
                'resume_id': resume_id
            },
            UpdateExpression='SET recommendations_s3_path = :path, recommendations_generated_at = :time',
            ExpressionAttributeValues={
                ':path': f's3://{BUCKET_NAME}/{recommendations_key}',
                ':time': datetime.utcnow().isoformat()
            }
        )
        
        print(f" Updated DynamoDB with recommendations path")
        
        print("=" * 80)
        print("RECOMMENDATION HANDLER - Complete")
        print("=" * 80)
        
        return cors_response(200, {
            'success': True,
            'message': 'Recommendations generated successfully',
            'recommendations': recommendations,
            'cached': False
        })
        
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