import unittest


class TestSNSMessageFormatting(unittest.TestCase):
    """Test SNS message formatting"""
    
    def test_contact_form_message_format(self):
        """Test contact form SNS message formatting"""
        def format_contact_message(name, email, subject, category, message):
            return f"""
New Contact Form Submission
From: {name}
Email: {email}
Category: {category}
Subject: {subject}
Message:
{message}
            """.strip()
        
        message = format_contact_message(
            'John Doe',
            'john@example.com',
            'Question',
            'general',
            'This is a test message'
        )
        
        self.assertIn('John Doe', message)
        self.assertIn('john@example.com', message)
        self.assertIn('Question', message)
        self.assertIn('test message', message)
    
    def test_contact_form_message_complete(self):
        """Test complete contact form message includes all fields"""
        def format_contact_message(name, email, subject, category, message):
            return f"""
New Contact Form Submission
From: {name}
Email: {email}
Category: {category}
Subject: {subject}
Message:
{message}
            """.strip()
        
        message = format_contact_message(
            'Jane Smith',
            'jane@test.com',
            'Bug Report',
            'technical',
            'Found a bug in the system'
        )
        
        self.assertIn('New Contact Form Submission', message)
        self.assertIn('From:', message)
        self.assertIn('Email:', message)
        self.assertIn('Category:', message)
        self.assertIn('Subject:', message)
        self.assertIn('Message:', message)


class TestFeedbackFormatting(unittest.TestCase):
    """Test feedback message formatting"""
    
    def test_feedback_star_rating_full(self):
        """Test star rating display - 5 stars"""
        def create_star_rating(rating):
            return '*' * rating + '-' * (5 - rating)
        
        self.assertEqual(create_star_rating(5), '*****')
    
    def test_feedback_star_rating_partial(self):
        """Test star rating display - partial ratings"""
        def create_star_rating(rating):
            return '*' * rating + '-' * (5 - rating)
        
        self.assertEqual(create_star_rating(3), '***--')
        self.assertEqual(create_star_rating(1), '*----')
    
    def test_feedback_star_rating_all_values(self):
        """Test star rating display - all possible values"""
        def create_star_rating(rating):
            return '*' * rating + '-' * (5 - rating)
        
        self.assertEqual(create_star_rating(1), '*----')
        self.assertEqual(create_star_rating(2), '**---')
        self.assertEqual(create_star_rating(3), '***--')
        self.assertEqual(create_star_rating(4), '****-')
        self.assertEqual(create_star_rating(5), '*****')


if __name__ == '__main__':
    unittest.main()
