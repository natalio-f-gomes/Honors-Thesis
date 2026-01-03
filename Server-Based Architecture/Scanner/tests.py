import json
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth.models import User
from django.test import RequestFactory
from io import BytesIO


class TestParseResumeJson:

    
    def test_parse_dict_input(self):
        """Test parsing when input is already a dict"""
        from views import _parse_resume_json
        
        input_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "skills": ["Python", "Django"]
        }
        
        result = _parse_resume_json(input_data)
        
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"
        assert result["skills"] == ["Python", "Django"]
    
    def test_parse_json_string(self):
        """Test parsing when input is a JSON string"""
        from views import _parse_resume_json
        
        input_data = '{"name": "Jane Smith", "email": "jane@example.com"}'
        
        result = _parse_resume_json(input_data)
        
        assert result["name"] == "Jane Smith"
        assert result["email"] == "jane@example.com"
    
    def test_parse_with_defaults(self):
        """Test that default values are set for missing fields"""
        from views import _parse_resume_json
        
        input_data = {"name": "Test User"}
        
        result = _parse_resume_json(input_data)
        
        assert result["name"] == "Test User"
        assert result["email"] == ""
        assert result["phone"] == ""
        assert result["skills"] == []
        assert result["education"] == []
        assert result["experience"] == []
    
    def test_parse_skills_string_to_list(self):
        """Test converting comma-separated skills string to list"""
        from views import _parse_resume_json
        
        input_data = {"skills": "Python, Django, JavaScript"}
        
        result = _parse_resume_json(input_data)
        
        assert result["skills"] == ["Python", "Django", "JavaScript"]
    
    def test_parse_invalid_json_string(self):
        """Test handling of invalid JSON string"""
        from views import _parse_resume_json
        
        input_data = "not valid json {"
        
        result = _parse_resume_json(input_data)
        
        assert result == {}
    
    def test_parse_error_in_data(self):
        """Test handling of error in parsed data"""
        from views import _parse_resume_json
        
        input_data = {"error": "Some error occurred"}
        
        result = _parse_resume_json(input_data)
        
        assert result == {}
    
    def test_parse_dict_to_list_conversion(self):
        """Test converting dict to list for education/experience/projects"""
        from views import _parse_resume_json
        
        input_data = {
            "education": {"degree": "BS", "school": "MIT"},
            "experience": {"title": "Developer", "company": "Tech Co"}
        }
        
        result = _parse_resume_json(input_data)
        
        assert isinstance(result["education"], list)
        assert len(result["education"]) == 1
        assert result["education"][0]["degree"] == "BS"
        
        assert isinstance(result["experience"], list)
        assert len(result["experience"]) == 1


class TestValidateResume:
    """Tests for validate_resume function"""
    
    def test_valid_resume(self):
        """Test validation with a valid resume"""
        from views import validate_resume
        
        resume_text = """
        John Doe
        john.doe@example.com
        123-456-7890
        
        SKILLS
        Python, Django, JavaScript
        
        EDUCATION
        BS Computer Science, MIT
        
        EXPERIENCE
        Software Engineer at Tech Corp
        Developed web applications
        
        SUMMARY
        Experienced developer with 5 years
        """
        
        result = validate_resume(resume_text)
        
        assert result is True
    
    def test_invalid_resume_no_keywords(self):
        """Test validation fails with insufficient keywords"""
        from views import validate_resume
        
        resume_text = "Just some random text without resume keywords"
        
        result = validate_resume(resume_text)
        
        assert result is False
    
    def test_invalid_resume_no_email(self):
        """Test validation fails without email"""
        from views import validate_resume
        
        resume_text = """
        John Doe
        123-456-7890
        SKILLS
        EDUCATION
        EXPERIENCE
        """
        
        result = validate_resume(resume_text)
        
        assert result is False
    
    def test_invalid_resume_no_phone(self):
        """Test validation fails without phone number"""
        from views import validate_resume
        
        resume_text = """
        John Doe
        john@example.com
        SKILLS
        EDUCATION
        EXPERIENCE
        """
        
        result = validate_resume(resume_text)
        
        assert result is False


class TestExtractTextFromPdf:
    """Tests for extract_text_from_pdf function"""
    
    @patch('views.PyPDF2.PdfReader')
    @patch('views.extract_resume_basic_data_fast')
    def test_successful_extraction(self, mock_claude, mock_pdf_reader):
        """Test successful PDF text extraction"""
        from views import extract_text_from_pdf
        
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Sample resume text with skills and experience"
        mock_pdf_reader.return_value.pages = [mock_page]
        
        # Mock Claude AI response
        mock_claude.return_value = {
            "name": "John Doe",
            "email": "john@example.com",
            "skills": ["Python", "Django"]
        }
        
        # Mock resume model
        mock_resume = Mock()
        mock_resume.id = 1
        mock_resume.resume_file.open.return_value.__enter__ = Mock(return_value=BytesIO(b"fake pdf"))
        mock_resume.resume_file.open.return_value.__exit__ = Mock(return_value=False)
        
        result = extract_text_from_pdf(mock_resume)
        
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"
        mock_claude.assert_called_once()
    
    @patch('views.PyPDF2.PdfReader')
    def test_empty_pdf_text(self, mock_pdf_reader):
        """Test handling of scanned PDF with no text"""
        from views import extract_text_from_pdf
        
        # Mock PDF reader returning empty text
        mock_page = Mock()
        mock_page.extract_text.return_value = ""
        mock_pdf_reader.return_value.pages = [mock_page]
        
        # Mock resume model
        mock_resume = Mock()
        mock_resume.id = 1
        mock_resume.resume_file.open.return_value.__enter__ = Mock(return_value=BytesIO(b"fake pdf"))
        mock_resume.resume_file.open.return_value.__exit__ = Mock(return_value=False)
        
        result = extract_text_from_pdf(mock_resume)
        
        assert result == -1
    
    @patch('views.PyPDF2.PdfReader')
    @patch('views.extract_resume_basic_data_fast')
    def test_claude_error_response(self, mock_claude, mock_pdf_reader):
        """Test handling of Claude AI error response"""
        from views import extract_text_from_pdf
        
        # Mock PDF reader
        mock_page = Mock()
        mock_page.extract_text.return_value = "Sample resume text"
        mock_pdf_reader.return_value.pages = [mock_page]
        
        # Mock Claude AI error response
        mock_claude.return_value = {"error": "API timeout"}
        
        # Mock resume model
        mock_resume = Mock()
        mock_resume.id = 1
        mock_resume.resume_file.open.return_value.__enter__ = Mock(return_value=BytesIO(b"fake pdf"))
        mock_resume.resume_file.open.return_value.__exit__ = Mock(return_value=False)
        
        result = extract_text_from_pdf(mock_resume)
        
        assert result == -1


class TestGetJobsForResume:
    """Tests for get_jobs_for_resume function"""
    
    @patch('views.get_rapid_api_response')
    def test_successful_job_retrieval(self, mock_api):
        """Test successful job retrieval"""
        from views import get_jobs_for_resume
        
        # Mock API response
        mock_jobs = [
            {"title": "Software Engineer", "company": "Tech Corp"},
            {"title": "Python Developer", "company": "Dev Co"}
        ]
        mock_api.return_value = mock_jobs
        
        # Mock resume model
        mock_resume = Mock()
        mock_resume.id = 1
        mock_resume.user.id = 123
        mock_resume.career_field = "Software Development"
        mock_resume.experience_level = "Mid-level"
        mock_resume.preferred_location = "New York"
        
        result = get_jobs_for_resume(mock_resume)
        
        assert len(result) == 2
        assert result[0]["title"] == "Software Engineer"
        mock_api.assert_called_once_with(
            user_id=123,
            career_field="Software Development",
            experience_level="Mid-level",
            job_location="New York"
        )
    
    @patch('views.get_rapid_api_response')
    def test_api_error_handling(self, mock_api):
        """Test handling of API errors"""
        from views import get_jobs_for_resume
        
        # Mock API raising exception
        mock_api.side_effect = Exception("API error")
        
        # Mock resume model
        mock_resume = Mock()
        mock_resume.id = 1
        mock_resume.user.id = 123
        
        result = get_jobs_for_resume(mock_resume)
        
        assert result == []


class TestExtractTextFromResume:
    """Tests for extract_text_from_resume function"""
    
    @patch('views.extract_text_from_pdf')
    def test_pdf_extraction(self, mock_extract_pdf):
        """Test PDF file extraction"""
        from views import extract_text_from_resume
        
        mock_extract_pdf.return_value = {"name": "John Doe"}
        
        mock_resume = Mock()
        mock_resume.id = 1
        mock_resume.resume_file.name = "resume.pdf"
        
        result = extract_text_from_resume(mock_resume)
        
        assert result == {"name": "John Doe"}
        mock_extract_pdf.assert_called_once_with(mock_resume)
    
    def test_non_pdf_file(self):
        """Test rejection of non-PDF files"""
        from views import extract_text_from_resume
        
        mock_resume = Mock()
        mock_resume.id = 1
        mock_resume.resume_file.name = "resume.docx"
        
        result = extract_text_from_resume(mock_resume)
        
        assert result == -1
    
    @patch('views.extract_text_from_pdf')
    def test_extraction_exception(self, mock_extract_pdf):
        """Test handling of extraction exceptions"""
        from views import extract_text_from_resume
        
        mock_extract_pdf.side_effect = Exception("Extraction failed")
        
        mock_resume = Mock()
        mock_resume.id = 1
        mock_resume.resume_file.name = "resume.pdf"
        
        result = extract_text_from_resume(mock_resume)
        
        assert result == -1

