# UserAuth/management/commands/cleanup_password_tokens.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from UserAuth.models import PasswordResetToken


class Command(BaseCommand):
    help = 'Clean up expired password reset tokens'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Delete tokens older than this many days (default: 7)'
        )

    def handle(self, *args, **options):
        # Clean up expired tokens
        count = PasswordResetToken.objects.cleanup_expired_tokens()

        # Also clean up very old tokens (even if not expired)
        days = options['days']
        old_date = timezone.now() - timedelta(days=days)
        old_tokens = PasswordResetToken.objects.filter(created_at__lt=old_date)
        old_count = old_tokens.count()
        old_tokens.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted {count} expired tokens and {old_count} old tokens'
            )
        )