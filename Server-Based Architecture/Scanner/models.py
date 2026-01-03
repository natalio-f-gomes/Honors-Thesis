import logging

from django.db import models
from django.contrib.auth.models import User

from Evaluator.utils.get_jobs import get_rapid_api_response
from .static_lists import career_fields, level_choices
import logging

logger = logging.getLogger(__name__)

# Create your models here.

class Resume(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    resume_file = models.FileField(upload_to="UserResumes/", blank=True, null=True)
    extracted_text = models.JSONField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    jobs_matched = models.JSONField(null=True, blank=True)
    recommendation_skills = models.JSONField(null=True, blank=True)


    career_field = models.CharField(
        max_length=200,
        choices=career_fields.CAREER_FIELDS,
        null=True,
        blank=True
    )

    experience_level = models.CharField(
        max_length=200,
        choices=level_choices.LEVEL_CHOICES,
        null=True,
        blank=True
    )

    preferred_location = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} Resume id: {self.id}"

    def get_extracted_text(self):
        return self.extracted_text

    def get_preferred_location(self):
        try:
            return self.preferred_location
        except Exception as e:
            logging.info(f"Error Attempting to return the preferred_location. \n{e}")
            return e

    def get_experience_level(self):
        try:
            return self.experience_level
        except Exception as e:
            print(f"FAILED TRYING TO GET THE USER: {e}")
            return None

    def get_career_field(self):
        try:
            return self.career_field
        except Exception as e:
            print(f"FAILED TRYING TO GET THE USER: {e}")
            return None

    def set_career_field(self, new_career_field):
        try:
            self.__class__.objects.filter(pk=self.pk).update(career_field=new_career_field)
            self.refresh_from_db()
        except Exception as error:
            print(error)
            return error

    def set_preferred_location(self, new_preferred_location):
        try:
            self.__class__.objects.filter(pk=self.pk).update(preferred_location=new_preferred_location)
            self.refresh_from_db()
        except Exception as error:
            print(error)
            return error

    def set_experience_level(self, new_experience_level):
        try:
            self.__class__.objects.filter(pk=self.pk).update(experience_level=new_experience_level)
            self.refresh_from_db()
        except Exception as error:
            print(error)
            return error

    @staticmethod
    def delete_resume_by_id(old_id):
        try:
            Resume.objects.filter(pk=old_id).delete()
            return True
        except Exception as error:
            print(error)
            return False

    def set_extracted_text(self, new_extracted_text):
        try:
            self.__class__.objects.filter(pk=self.pk).update(extracted_text=new_extracted_text)
            self.refresh_from_db()
        except Exception as error:
            print(error)
            return error

    def set_recommendation_skills(self, recommendation):
        try:
            self.__class__.objects.filter(pk=self.pk).update(recommendation_skills=recommendation)
            self.refresh_from_db()
        except Exception as error:
            print(error)
            return error

    def get_recommendation_skills(self):
        try:
            return self.recommendation_skills
        except Exception as error:
            print(error)

    def set_jobs_matched(self, new_jobs_matched):
        """Store jobs data as JSON in the database"""
        try:
            # Ensure we're storing a list, not a string
            if isinstance(new_jobs_matched, str):
                import json
                new_jobs_matched = json.loads(new_jobs_matched)

            self.__class__.objects.filter(pk=self.pk).update(jobs_matched=new_jobs_matched)
            self.refresh_from_db()
            logger.info(f"Successfully stored {len(new_jobs_matched)} jobs for resume {self.pk}")

        except Exception as error:
            logger.error(f"Error setting jobs_matched: {error}")
            return error

    def get_jobs_matched(self):
        """Get matching jobs for this resume"""
        try:
            # If jobs are already stored, return them
            if self.jobs_matched:
                return self.jobs_matched

            # Otherwise, fetch new jobs
            jobs_data = get_rapid_api_response(
                user_id=self.user.id,
                career_field=self.career_field,
                experience_level=self.experience_level,
                job_location=self.preferred_location
            )

            # Store the jobs data in the database
            if jobs_data:
                self.set_jobs_matched(jobs_data)

            return jobs_data

        except Exception as e:
            logger.error(f"Error getting jobs for resume {self.id}: {e}")
            return []
