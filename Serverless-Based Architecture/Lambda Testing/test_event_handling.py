import unittest
import json


class TestOptionsRequestHandling(unittest.TestCase):
    """Test CORS preflight (OPTIONS) handling"""
    
    def test_options_response(self):
        """Test OPTIONS request returns correct headers"""
        def handle_options():
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps({'message': 'OK'})
            }
        
        response = handle_options()
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Access-Control-Allow-Origin', response['headers'])


class TestEventDataExtraction(unittest.TestCase):
    """Test extracting data from Lambda events"""
    
    def test_extract_user_from_event(self):
        """Test extracting user info from event"""
        event = {
            'requestContext': {
                'authorizer': {
                    'claims': {
                        'sub': 'user-123',
                        'email': 'test@example.com'
                    }
                }
            }
        }
        
        user_id = event['requestContext']['authorizer']['claims']['sub']
        user_email = event['requestContext']['authorizer']['claims']['email']
        
        self.assertEqual(user_id, 'user-123')
        self.assertEqual(user_email, 'test@example.com')
    
    def test_extract_query_parameters(self):
        """Test extracting query parameters"""
        event = {
            'queryStringParameters': {
                'resumeId': 'resume-123',
                'format': 'json'
            }
        }
        
        params = event.get('queryStringParameters', {})
        resume_id = params.get('resumeId')
        
        self.assertEqual(resume_id, 'resume-123')
        self.assertIsNone(params.get('nonexistent'))
    
    def test_extract_query_parameters_none(self):
        """Test extracting query parameters when none exist"""
        event = {}
        
        params = event.get('queryStringParameters', {})
        
        self.assertEqual(params, {})
        self.assertIsNone(params.get('anyKey'))


if __name__ == '__main__':
    unittest.main()
