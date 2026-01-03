import unittest


class TestEmailValidation(unittest.TestCase):
    """Test email format validation"""
    
    def test_valid_emails(self):
        """Test valid email formats"""
        def is_valid_email(email):
            return '@' in email and '.' in email
        
        self.assertTrue(is_valid_email('test@example.com'))
        self.assertTrue(is_valid_email('user.name@domain.co.uk'))
    
    def test_invalid_emails(self):
        """Test invalid email formats"""
        def is_valid_email(email):
            return '@' in email and '.' in email
        
        self.assertFalse(is_valid_email('invalid'))
        self.assertFalse(is_valid_email('no-at-sign.com'))
        self.assertFalse(is_valid_email('no-dot@domain'))


class TestRatingValidation(unittest.TestCase):
    """Test rating validation (1-5)"""
    
    def test_valid_ratings(self):
        """Test valid rating values"""
        def is_valid_rating(rating):
            return 1 <= rating <= 5
        
        self.assertTrue(is_valid_rating(1))
        self.assertTrue(is_valid_rating(3))
        self.assertTrue(is_valid_rating(5))
    
    def test_invalid_ratings(self):
        """Test invalid rating values"""
        def is_valid_rating(rating):
            return 1 <= rating <= 5
        
        self.assertFalse(is_valid_rating(0))
        self.assertFalse(is_valid_rating(6))
        self.assertFalse(is_valid_rating(-1))


class TestMessageLengthValidation(unittest.TestCase):
    """Test message length validation"""
    
    def test_valid_message_length(self):
        """Test valid message length"""
        def is_valid_message_length(message, min_len=10, max_len=1000):
            return min_len <= len(message) <= max_len
        
        self.assertTrue(is_valid_message_length('This is a valid message'))
    
    def test_message_too_short(self):
        """Test message too short"""
        def is_valid_message_length(message, min_len=10, max_len=1000):
            return min_len <= len(message) <= max_len
        
        self.assertFalse(is_valid_message_length('Short'))
    
    def test_message_too_long(self):
        """Test message too long"""
        def is_valid_message_length(message, min_len=10, max_len=1000):
            return min_len <= len(message) <= max_len
        
        self.assertFalse(is_valid_message_length('x' * 1001))


class TestRequiredFieldsValidation(unittest.TestCase):
    """Test required fields validation"""
    
    def test_all_required_fields_present(self):
        """Test when all required fields are present"""
        def validate_required_fields(data, required_fields):
            missing = [field for field in required_fields if not data.get(field)]
            if missing:
                return {'error': f'Missing required fields: {", ".join(missing)}'}
            return None
        
        data = {'name': 'John', 'email': 'john@example.com', 'message': 'Hello'}
        required = ['name', 'email', 'message']
        
        error = validate_required_fields(data, required)
        self.assertIsNone(error)
    
    def test_missing_required_fields(self):
        """Test when required fields are missing"""
        def validate_required_fields(data, required_fields):
            missing = [field for field in required_fields if not data.get(field)]
            if missing:
                return {'error': f'Missing required fields: {", ".join(missing)}'}
            return None
        
        data = {'name': 'John', 'email': ''}
        required = ['name', 'email', 'message']
        
        error = validate_required_fields(data, required)
        self.assertIsNotNone(error)
        self.assertIn('email', error['error'])
        self.assertIn('message', error['error'])


class TestJobSearchParametersValidation(unittest.TestCase):
    """Test job search parameter validation"""
    
    def test_valid_search_params(self):
        """Test valid job search parameters"""
        def validate_search_params(params):
            required = ['career_field', 'experience_level']
            return all(params.get(field) for field in required)
        
        valid_params = {
            'career_field': 'Developer',
            'experience_level': 'Junior'
        }
        self.assertTrue(validate_search_params(valid_params))
    
    def test_invalid_search_params(self):
        """Test invalid job search parameters"""
        def validate_search_params(params):
            required = ['career_field', 'experience_level']
            return all(params.get(field) for field in required)
        
        invalid_params = {
            'career_field': 'Developer'
        }
        self.assertFalse(validate_search_params(invalid_params))


if __name__ == '__main__':
    unittest.main()
