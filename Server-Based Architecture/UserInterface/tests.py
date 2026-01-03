"""
Path: ATP-PROJECT/UserInterface/tests.py
Good old Unit Tests for the UserInterface app models and view functions

"""

from django.test import TestCase, RequestFactory, Client
from .views import *
from django.urls import reverse
from .models import *
from django.contrib.auth.hashers import check_password


class TestFeedbackModel(TestCase):
    def setUp(self):
        self.test_user_one = User.objects.create_user(username="user_one", first_name = "Jacob", last_name="Lii", email="jacob_lii@email.com", password="mypassword")

        Feedback.objects.create(
            user=self.test_user_one,
            feedback="This is a great project.",
            rating=5
        )

        self.get_user_one = Feedback.objects.get(pk=1)

    def test_correct_user(self):
        self.assertEqual(self.get_user_one.user_id, 1)

    def test_feedback_field(self):
        self.assertEqual(self.get_user_one.feedback, "This is a great project.")

    def test_rating_field(self):
        self.assertEqual(self.get_user_one.rating, 5)

    def test_user_creation(self):
        self.assertEqual(self.get_user_one.user.username, "user_one")
        self.assertEqual(self.get_user_one.user.first_name, "Jacob")
        self.assertEqual(self.get_user_one.user.last_name, "Lii")
        self.assertEqual(self.get_user_one.user.email, "jacob_lii@email.com")
        self.assertTrue(check_password("mypassword", self.get_user_one.user.password) )

class TestViewFunctions(TestCase):
    def setUp(self):
        self.client = Client()
        self.index_view = self.client.get(reverse('home'))
        self.about_view = self.client.get((reverse('about')))
        self.feedback_page_view = self.client.get(reverse('feedback_page'))
        self.login_page_view = self.client.get(reverse('login'))
        self.register_page_view = self.client.get(reverse('register'))


    def test_views_status(self):
        """By accessing a specific name view, what is the response status"""
        self.assertEqual(self.index_view.status_code, 200)
        self.assertEqual(self.about_view.status_code, 200)
        self.assertEqual(self.feedback_page_view.status_code, 200)
        self.assertEqual(self.login_page_view.status_code, 200)
        self.assertEqual(self.register_page_view.status_code, 200)


    def test_views_templates(self):
        """assertTemplateUsed checks the view function template"""
        self.assertTemplateUsed(self.index_view, 'index.html')
        self.assertTemplateUsed(self.about_view, "about-us.html")
        self.assertTemplateUsed(self.feedback_page_view,"feedback.html")
        self.assertTemplateUsed(self.login_page_view, "login.html")
        self.assertTemplateUsed(self.register_page_view, "register.html")




