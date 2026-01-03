# UserAuth/models.py

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import secrets
import base64
import hashlib
import hmac


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    resume_limit = models.IntegerField(validators=[MaxValueValidator(5)], null=True, default=5)
    resume_uploaded = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username} profile"

    def increment_resume_upload(self):
        try:
            if self.resume_uploaded < self.resume_limit:
                self.__class__.objects.filter(pk=self.pk).update(resume_uploaded=self.resume_uploaded + 1)
                self.refresh_from_db()
            else:
                raise ValueError("Resume upload limit reached.")
        except Exception as error:
            print(error)

    def get_resume_uploaded(self):
        return self.resume_uploaded

    def set_resume_uploaded(self, amount):
        self.resume_uploaded = amount
        print(f"Resume uploaded: {self.resume_uploaded}. Amount {amount}")

    def get_resume_limit(self):
        return self.resume_limit


class PasswordResetTokenManager(models.Manager):
    """Manager for password reset token """

    def create_token_for_user(self, user):
        """Create or update reset token for user - production safe"""
        # Delete any existing tokens for this user
        self.filter(user=user).delete()

        # Create new token
        reset_token = self.create(user=user)
        return reset_token

    def get_valid_token(self, token_string):
        """Get token object if valid, None otherwise - production safe"""
        try:
            # Clean up expired tokens first
            self.cleanup_expired_tokens()

            token_obj = self.get(token=token_string)
            if not token_obj.is_expired():
                return token_obj
            else:
                # Delete expired token
                token_obj.delete()
                return None
        except self.model.DoesNotExist:
            return None

    def cleanup_expired_tokens(self):
        """Clean up all expired tokens"""
        expired_tokens = self.filter(
            models.Q(expires_at__lt=timezone.now()) | models.Q(is_used=True)
        )
        count = expired_tokens.count()
        expired_tokens.delete()
        return count


class PasswordResetToken(models.Model):
    """Model for secure password reset tokens"""

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    token = models.CharField(max_length=200, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    objects = PasswordResetTokenManager()

    def save(self, *args, **kwargs):
        """Override save to generate token on creation"""
        # Generate token only when creating (not updating)
        if not self.pk:
            self.token = self._generate_secure_token()
            # Set expiration time - default: 1 hour, can be configured
            expiry_minutes = getattr(settings, 'PASSWORD_RESET_TIMEOUT_MINUTES', 60)
            self.expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        super().save(*args, **kwargs)

    def _generate_secure_token(self):
        """Generate a cryptographically secure random token"""
        # Use secrets module for cryptographically strong random generation
        random_bytes = secrets.token_bytes(64)  # 64 bytes = 512 bits
        # Add timestamp and user info for additional uniqueness
        timestamp = str(timezone.now().timestamp()).encode()
        user_info = str(self.user.id).encode() if self.user else b'anonymous'

        # Combine all data
        token_data = random_bytes + timestamp + user_info

        # Create HMAC for additional security if SECRET_KEY is available
        if hasattr(settings, 'SECRET_KEY'):
            signature = hmac.new(
                settings.SECRET_KEY.encode(),
                token_data,
                hashlib.sha256
            ).digest()
            token_data = token_data + signature

        # Base64 encode and make URL safe
        token = base64.urlsafe_b64encode(token_data).rstrip(b'=').decode('utf-8')

        # Ensure uniqueness by checking database
        while PasswordResetToken.objects.filter(token=token).exists():
            # Regenerate if collision (extremely unlikely but safe)
            random_bytes = secrets.token_bytes(64)
            token_data = random_bytes + timestamp + user_info
            if hasattr(settings, 'SECRET_KEY'):
                signature = hmac.new(
                    settings.SECRET_KEY.encode(),
                    token_data,
                    hashlib.sha256
                ).digest()
                token_data = token_data + signature
            token = base64.urlsafe_b64encode(token_data).rstrip(b'=').decode('utf-8')

        return token

    def get_token(self):
        """Return the token if it's still valid"""
        if self.is_expired():
            return None
        return self.token

    def is_expired(self):
        """Check if token has expired"""
        return timezone.now() > self.expires_at or self.is_used

    def mark_as_used(self):
        """Mark token as used"""
        self.is_used = True
        self.save(update_fields=['is_used'])

    def set_request_metadata(self, request):
        """Store request metadata for security tracking"""
        self.ip_address = self.get_client_ip(request)
        self.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Limit length
        self.save(update_fields=['ip_address', 'user_agent'])

    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def __str__(self):
        return f"Reset token for {self.user.username if self.user else 'Unknown'} - {'Expired' if self.is_expired() else 'Valid'}"

    class Meta:
        verbose_name = "Password Reset Token"
        verbose_name_plural = "Password Reset Tokens"
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['created_at']),
        ]