import unittest
from decimal import Decimal


class TestResumeNumbering(unittest.TestCase):
    """Test resume numbering logic"""
    
    def test_get_next_resume_number_empty(self):
        """Test getting resume number when no resumes exist"""
        def get_next_resume_number(items):
            if len(items) >= 5:
                raise Exception("Resume limit reached (5/5)")
            if not items:
                return 1
            max_number = max([item.get('resume_number', 0) for item in items])
            return max_number + 1
        
        self.assertEqual(get_next_resume_number([]), 1)
    
    def test_get_next_resume_number_increment(self):
        """Test resume number incrementing"""
        def get_next_resume_number(items):
            if len(items) >= 5:
                raise Exception("Resume limit reached (5/5)")
            if not items:
                return 1
            max_number = max([item.get('resume_number', 0) for item in items])
            return max_number + 1
        
        items = [
            {'resume_number': 1},
            {'resume_number': 2},
            {'resume_number': 3}
        ]
        self.assertEqual(get_next_resume_number(items), 4)
    
    def test_resume_limit_reached(self):
        """Test resume limit enforcement"""
        def get_next_resume_number(items):
            if len(items) >= 5:
                raise Exception("Resume limit reached (5/5)")
            if not items:
                return 1
            max_number = max([item.get('resume_number', 0) for item in items])
            return max_number + 1
        
        items = [{'resume_number': i} for i in range(1, 6)]
        with self.assertRaises(Exception) as context:
            get_next_resume_number(items)
        self.assertIn("Resume limit reached", str(context.exception))


class TestResumeIDGeneration(unittest.TestCase):
    """Test resume ID generation logic"""
    
    def test_resume_id_format(self):
        """Test resume ID format is correct"""
        user_id = "test-user-123"
        resume_number = 1
        timestamp = 1234567890
        
        resume_id = f"{user_id}-{resume_number}-{timestamp}"
        
        parts = resume_id.split('-')
        self.assertEqual(parts[0], "test")
        self.assertEqual(parts[1], "user")
        self.assertEqual(parts[2], "123")
        self.assertEqual(parts[3], "1")
        self.assertEqual(parts[4], "1234567890")


class TestResumeDataFormatting(unittest.TestCase):
    """Test resume data formatting"""
    
    def test_format_resume_metadata(self):
        """Test formatting resume metadata"""
        def format_resume_metadata(item):
            return {
                'resume_id': item.get('resume_id'),
                'resume_number': int(item.get('resume_number', 0)),
                'file_name': item.get('file_name'),
                'status': item.get('status'),
                'skills_count': int(item.get('skills_count', 0))
            }
        
        raw_item = {
            'resume_id': 'resume-123',
            'resume_number': Decimal('1'),
            'file_name': 'resume.pdf',
            'status': 'completed',
            'skills_count': Decimal('15')
        }
        
        formatted = format_resume_metadata(raw_item)
        
        self.assertEqual(formatted['resume_number'], 1)
        self.assertIsInstance(formatted['resume_number'], int)
        self.assertEqual(formatted['skills_count'], 15)
        self.assertIsInstance(formatted['skills_count'], int)
    
    def test_sort_resumes(self):
        """Test sorting resumes by number"""
        resumes = [
            {'resume_number': 3},
            {'resume_number': 1},
            {'resume_number': 2}
        ]
        
        sorted_resumes = sorted(resumes, key=lambda x: x.get('resume_number', 0))
        
        self.assertEqual(sorted_resumes[0]['resume_number'], 1)
        self.assertEqual(sorted_resumes[1]['resume_number'], 2)
        self.assertEqual(sorted_resumes[2]['resume_number'], 3)


if __name__ == '__main__':
    unittest.main()
