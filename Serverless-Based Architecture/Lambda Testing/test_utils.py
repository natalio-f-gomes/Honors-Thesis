import unittest
from decimal import Decimal
import json


class TestDecimalConversion(unittest.TestCase):
    """Test decimal to int/float conversion"""
    
    def test_decimal_to_int(self):
        """Test whole number decimal conversion"""
        def convert_decimals(obj):
            if isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: convert_decimals(value) for key, value in obj.items()}
            elif isinstance(obj, Decimal):
                return int(obj) if obj % 1 == 0 else float(obj)
            return obj
        
        result = convert_decimals(Decimal('10'))
        self.assertEqual(result, 10)
        self.assertIsInstance(result, int)
    
    def test_decimal_to_float(self):
        """Test decimal with fractional part conversion"""
        def convert_decimals(obj):
            if isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: convert_decimals(value) for key, value in obj.items()}
            elif isinstance(obj, Decimal):
                return int(obj) if obj % 1 == 0 else float(obj)
            return obj
        
        result = convert_decimals(Decimal('10.5'))
        self.assertEqual(result, 10.5)
        self.assertIsInstance(result, float)
    
    def test_nested_decimal_conversion(self):
        """Test conversion of decimals in nested structures"""
        def convert_decimals(obj):
            if isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: convert_decimals(value) for key, value in obj.items()}
            elif isinstance(obj, Decimal):
                return int(obj) if obj % 1 == 0 else float(obj)
            return obj
        
        test_data = {
            'count': Decimal('5'),
            'items': [Decimal('1'), Decimal('2.5')],
            'nested': {'value': Decimal('100')}
        }
        result = convert_decimals(test_data)
        self.assertEqual(result['count'], 5)
        self.assertEqual(result['items'], [1, 2.5])
        self.assertEqual(result['nested']['value'], 100)


class TestCORSResponse(unittest.TestCase):
    """Test CORS response generation"""
    
    def test_cors_response_structure(self):
        """Test that CORS response has correct structure"""
        def cors_response(status_code, body):
            return {
                'statusCode': status_code,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps(body)
            }
        
        response = cors_response(200, {'message': 'success'})
        
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Access-Control-Allow-Origin', response['headers'])
        self.assertEqual(response['headers']['Access-Control-Allow-Origin'], '*')
        self.assertIsInstance(response['body'], str)
        
        # Verify body is valid JSON
        body = json.loads(response['body'])
        self.assertEqual(body['message'], 'success')


class TestS3PathParsing(unittest.TestCase):
    """Test S3 path parsing logic"""
    
    def test_parse_s3_path(self):
        """Test parsing S3 paths"""
        def parse_s3_path(s3_path):
            path = s3_path.replace('s3://', '')
            bucket, key = path.split('/', 1)
            return bucket, key
        
        # Test valid path
        bucket, key = parse_s3_path('s3://my-bucket/folder/file.json')
        self.assertEqual(bucket, 'my-bucket')
        self.assertEqual(key, 'folder/file.json')
        
        # Test nested path
        bucket, key = parse_s3_path('s3://bucket/a/b/c/file.txt')
        self.assertEqual(bucket, 'bucket')
        self.assertEqual(key, 'a/b/c/file.txt')


class TestJSONParsing(unittest.TestCase):
    """Test JSON parsing and handling"""
    
    def test_parse_claude_response_with_markdown(self):
        """Test parsing Claude AI JSON response with markdown"""
        def parse_claude_json(response_text):
            # Remove markdown code blocks if present
            if response_text.strip().startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            return json.loads(response_text.strip())
        
        markdown_response = """```json
{
  "skills": ["Python", "AWS"],
  "count": 2
}
```"""
        result = parse_claude_json(markdown_response)
        self.assertEqual(result['skills'], ["Python", "AWS"])
    
    def test_parse_claude_response_without_markdown(self):
        """Test parsing clean JSON response"""
        def parse_claude_json(response_text):
            # Remove markdown code blocks if present
            if response_text.strip().startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            return json.loads(response_text.strip())
        
        clean_response = '{"skills": ["Python"], "count": 1}'
        result = parse_claude_json(clean_response)
        self.assertEqual(result['count'], 1)


if __name__ == '__main__':
    unittest.main()
