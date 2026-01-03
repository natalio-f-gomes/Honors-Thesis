
from django.db import models
from django.contrib.auth.models import User

class Feedback(models.Model):
    """Model for user feedback"""

    CATEGORY_CHOICES = [
        ('general', 'General Feedback'),
        ('ui', 'User Interface'),
        ('performance', 'Performance'),
        ('feature', 'Feature Request'),
        ('bug', 'Bug Report'),
        ('other', 'Other')
    ]

    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general', null=True, blank=True)
    message = models.TextField(null=True, blank=True)
    rating = models.IntegerField(choices=RATING_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Feedback'
        verbose_name_plural = 'Feedback'

    def __str__(self):
        return f"Feedback from {self.user.username if self.user else 'Anonymous'} - {self.category}"

class Contact(models.Model):
    """Model for contact messages"""

    CATEGORY_CHOICES = [
        ('general', 'General Inquiry'),
        ('support', 'Technical Support'),
        ('feedback', 'Feedback'),
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('other', 'Other')
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=100,null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    subject = models.CharField(max_length=200,null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'

    def __str__(self):
        return f"Contact from {self.name} - {self.subject}"