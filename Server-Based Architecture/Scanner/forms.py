from .models import Resume
from django import forms
from .static_lists import career_fields, level_choices

from django import forms
from .models import Resume

from django import forms
from .models import Resume


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ["resume_file", "career_field", "experience_level", "preferred_location"]
        widgets = {
            "resume_file": forms.FileInput(attrs={
                "id": "fileInput",
                "name": "resume_file",
                "accept": ".pdf,.doc,.docx",  # Updated to accept PDF, DOC, and DOCX files
                "style": "display: none;",
                "required": True
            }),
            "career_field": forms.Select(attrs={
                "class": "form-select",
                "name": "work_field",
                "required": True,
                "style": "border: 2px solid #e9ecef; border-radius: 15px; padding: 0.75rem 1rem;"
            }),
            "experience_level": forms.Select(attrs={
                "class": "form-select",
                "name": "experience_level",
                "required": True,
                "style": "border: 2px solid #e9ecef; border-radius: 15px; padding: 0.75rem 1rem;"
            }),
            "preferred_location": forms.TextInput(attrs={
                "class": "form-select",
                "name": "preferred_location",
                "required": True,
                "width": "100%",
                "placeholder": "EX: UNITED STATES, BOSTON, MA",
                "style": "border: 2px solid #e9ecef; border-radius: 15px; padding: 0.75rem 1rem;"
            }),
        }

    def __init__(self, *args, **kwargs):
        super(ResumeForm, self).__init__(*args, **kwargs)

        # Set field labels
        self.fields["resume_file"].label = ""
        self.fields["career_field"].label = ""
        self.fields["experience_level"].label = ""
        self.fields["preferred_location"].label = ""

        # Set help text
        self.fields["resume_file"].help_text = ""

        # Update career field choices to match HTML template options
        # Update career field choices to match HTML template options
        self.fields["career_field"].choices = career_fields.CAREER_FIELDS
        # Update experience level choices to match HTML template options
        self.fields["experience_level"].choices = level_choices.LEVEL_CHOICES

    def clean_resume_file(self):
        """Custom validation for resume file to ensure only PDF and DOCX files are allowed"""
        file = self.cleaned_data.get('resume_file')
        if file:
            # Get file extension
            file_name = file.name.lower()
            valid_extensions = ['.pdf', '.doc', '.docx']

            if not any(file_name.endswith(ext) for ext in valid_extensions):
                raise forms.ValidationError(
                    "Only PDF, DOC, and DOCX files are allowed. Please upload a valid resume file."
                )

            # Check file size (optional - limit to 10MB)
            if file.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError(
                    "File size must be less than 10MB. Please upload a smaller file."
                )

        return file

