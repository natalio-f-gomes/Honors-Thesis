import unittest


class TestPromptCreation(unittest.TestCase):
    """Test prompt creation for Claude AI"""
    
    def test_recommendation_prompt_structure(self):
        """Test that recommendation prompt includes all necessary data"""
        def create_simple_prompt(resume_data, jobs_data):
            return f"""Analyze resume: {resume_data.get('name')}
Skills: {', '.join(resume_data.get('skills', []))}
Jobs: {len(jobs_data.get('jobs', []))}"""
        
        resume_data = {
            'name': 'John Doe',
            'skills': ['Python', 'AWS', 'Docker']
        }
        
        jobs_data = {
            'jobs': [
                {'title': 'Software Engineer'},
                {'title': 'DevOps Engineer'}
            ]
        }
        
        prompt = create_simple_prompt(resume_data, jobs_data)
        
        self.assertIn('John Doe', prompt)
        self.assertIn('Python', prompt)
        self.assertIn('AWS', prompt)
        self.assertIn('2', prompt)


class TestJobSearchQuery(unittest.TestCase):
    """Test job search query building"""
    
    def test_build_job_search_query(self):
        """Test building job search query"""
        def build_query(career_field, experience_level):
            return f"{experience_level} {career_field}"
        
        query = build_query("Software Engineer", "Senior")
        self.assertEqual(query, "Senior Software Engineer")
    
    def test_build_job_search_query_variations(self):
        """Test building job search query with different inputs"""
        def build_query(career_field, experience_level):
            return f"{experience_level} {career_field}"
        
        self.assertEqual(build_query("Developer", "Junior"), "Junior Developer")
        self.assertEqual(build_query("Data Scientist", "Mid-Level"), "Mid-Level Data Scientist")


if __name__ == '__main__':
    unittest.main()
