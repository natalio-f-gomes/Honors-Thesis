# UserInterface/forms.py
from django import forms
from .models import Feedback, Contact


class FeedbackForm(forms.ModelForm):
    """Form for user feedback"""

    class Meta:
        model = Feedback
        fields = ['category', 'message', 'rating']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'style': 'border-radius: 10px;'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Share your feedback with us...',
                'style': 'border-radius: 10px;'
            }),
            'rating': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'style': 'border-radius: 10px;'
            })
        }
        labels = {
            'category': 'Feedback Category',
            'message': 'Your Feedback',
            'rating': 'Overall Rating'
        }


class ContactForm(forms.ModelForm):
    """Form for contact messages"""

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Your full name',
            'style': 'border-radius: 10px;'
        }),
        label='Full Name'
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'your.email@example.com',
            'style': 'border-radius: 10px;'
        }),
        label='Email Address'
    )

    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'What is this message about?',
            'style': 'border-radius: 10px;'
        }),
        label='Subject'
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Your message here...',
            'style': 'border-radius: 10px;'
        }),
        label='Message Content'
    )

    category = forms.ChoiceField(
        choices=[
            ('', 'Select category (optional)'),
            ('general', 'General Inquiry'),
            ('support', 'Technical Support'),
            ('feedback', 'Feedback'),
            ('bug', 'Bug Report'),
            ('feature', 'Feature Request'),
            ('other', 'Other')
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'style': 'border-radius: 10px;'
        }),
        label='Category'
    )

    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'category', 'message']