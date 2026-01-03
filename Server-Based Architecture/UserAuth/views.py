# UserAuth/views.py

from django.contrib.auth import authenticate, login, logout
from UserAuth.models import UserProfile, PasswordResetToken
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
import re

# Set up logger
logger = logging.getLogger(__name__)


def sign_in_user(request):
    logger.info("[SIGN IN] Sign-in attempt")
    username = request.POST.get("username")
    password = request.POST.get("password")
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        messages.success(request, "Logged In Successfully")
        logger.info(f"[SIGN IN] User {username} authenticated successfully")
        return redirect('home')
    else:
        messages.error(request, "Invalid Credentials")
        logger.warning(f"[SIGN IN] Failed login for username={username}")
        return render(request, 'login.html', {})


@login_required()
def sign_out_user(request):
    logger.info(f"[SIGN OUT] User {request.user.username} logging out")
    logout(request)
    messages.success(request, "Successfully Logged out")
    return redirect('home')


def register_user(request):
    logger.info("[REGISTER] Registration attempt")
    if request.method == 'POST':
        get_first_name = request.POST.get("first_name")
        get_last_name = request.POST.get("last_name")
        get_email = request.POST.get("email")
        get_username = request.POST.get("username")
        get_password = request.POST.get("password")
        get_confirm_password = request.POST.get("confirm_password")

        if get_password == get_confirm_password:
            if User.objects.filter(email=get_email).exists():
                messages.error(request, "This email is taken. Choose a different one")
                logger.warning(f"[REGISTER] Email {get_email} already in use")
                return redirect("register")
            try:
                new_user = User.objects.create_user(
                    first_name=get_first_name,
                    last_name=get_last_name,
                    email=get_email,
                    username=get_username,
                    password=get_password
                )
                user_profile = UserProfile.objects.create(user=new_user)
                user_profile.save()
                login(request, new_user)
                messages.success(request, "Registration Successful")
                logger.info(f"[REGISTER] User {get_username} registered and logged in")
                return redirect('home')
            except Exception as e:
                logger.error(f"[REGISTER] Registration error: {e}")
                messages.error(request, "This username is already taken. Please choose a new one.")
                return redirect('register')
        else:
            logger.warning("[REGISTER] Passwords do not match")
            messages.error(request, "Passwords do not match")
            return redirect('register')
    return render(request, 'register.html', {})


@login_required()
def reset_password(request, user_id):
    """Reset password for authenticated users (requires current password)"""
    logger.info(f"[RESET PASSWORD] Attempt to reset password for user_id={user_id}")
    try:
        current_user = User.objects.get(pk=user_id)
        if request.method == "POST":
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_new_password = request.POST.get('confirm_new_password')

            if current_user.check_password(current_password):
                if new_password == confirm_new_password:
                    current_user.set_password(new_password)
                    current_user.save()
                    login(request, current_user)
                    logger.info(f"[RESET PASSWORD] Password reset successful for user_id={user_id}")
                    return redirect("home")
                else:
                    logger.warning("[RESET PASSWORD] New passwords do not match")
                    messages.error(request, "The passwords do not match")
            else:
                logger.warning("[RESET PASSWORD] Incorrect current password")
                messages.error(request, "Incorrect Password")
    except User.DoesNotExist:
        logger.error(f"[RESET PASSWORD] User with ID {user_id} not found")
        messages.error(request, "You do not have access to this page")
        return redirect("home")

    return render(request, "reset_password_page.html", {})


@login_required()
def update_account_page(request, username):
    logger.info(f"[UPDATE PAGE] Request for update page by {request.user.username} for {username}")
    if request.user.username != username:
        logger.warning("[UPDATE PAGE] Unauthorized page access attempt")
        messages.error(request, "You do not have permissions to this page")
        return redirect("login")
    return render(request, "update_account_info.html", {})


@login_required()
def update_account_info(request, user_id):
    logger.info(f"[UPDATE INFO] Attempt to update account info for user_id={user_id}")
    if request.user.id != user_id:
        logger.warning(f"[UPDATE INFO] Unauthorized update attempt by the user={user_id}")
        messages.error(request, "You do not have permission to visit this website")
        return redirect("login")

    current_user = User.objects.get(pk=user_id)
    if request.method == "POST":
        new_first_name = request.POST.get("new_first_name")
        new_last_name = request.POST.get("new_last_name")
        new_email = request.POST.get("new_email")
        current_user.first_name = new_first_name
        current_user.last_name = new_last_name
        current_user.email = new_email
        current_user.save()
        logger.info(f"[UPDATE INFO] Account info updated for user_id={user_id}")
        return redirect("home")

    return render(request, "update_account_info.html", {"current_user": current_user})


@login_required()
@csrf_protect
@require_http_methods(["POST"])
def confirm_delete_account(request):
    """Handle password verification and account deletion via AJAX"""
    logger.info(f"[DELETE ACCOUNT] Password confirmation attempt by user_id={request.user.id}")

    try:
        password = request.POST.get('password', '').strip()

        if not password:
            logger.warning(f"[DELETE ACCOUNT] Empty password submitted by user_id={request.user.id}")
            return JsonResponse({
                'success': False,
                'error': 'Password is required'
            })

        # Verify the password
        user = authenticate(username=request.user.username, password=password)

        if user is None:
            logger.warning(f"[DELETE ACCOUNT] Invalid password attempt by user_id={request.user.id}")
            return JsonResponse({
                'success': False,
                'error': 'Invalid password. Please try again.'
            })

        # Password is correct, proceed with deletion
        logger.info(f"[DELETE ACCOUNT] Password verified for user_id={request.user.id}")

        # Store user info for logging before deletion
        user_id = request.user.id
        username = request.user.username
        email = request.user.email

        try:
            # Delete the user account (this will cascade and delete related data)
            request.user.delete()

            logger.info(
                f"[DELETE ACCOUNT] Successfully deleted account - user_id={user_id}, username={username}, email={email}")

            # Logout is automatic since the user object no longer exists
            logout(request)

            return JsonResponse({
                'success': True,
                'message': 'Your account has been successfully deleted.',
                'redirect_url': '/'
            })

        except Exception as delete_error:
            logger.error(f"[DELETE ACCOUNT] Error deleting user account user_id={user_id}: {str(delete_error)}")
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while deleting your account. Please try again or contact support.'
            })

    except Exception as e:
        logger.error(f"[DELETE ACCOUNT] Unexpected error in confirm_delete_account: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        })


# ============================================================================
# PASSWORD RECOVERY (FORGOT PASSWORD) VIEWS
# ============================================================================

@method_decorator([csrf_protect, never_cache], name='dispatch')
class PasswordResetRequestView(View):
    """Handle password reset requests for users who forgot their password"""
    template_name = 'password_reset_request.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        email = request.POST.get('email', '').strip().lower()

        # Input validation
        if not email:
            messages.error(request, 'Please enter an email address.')
            return render(request, self.template_name)

        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            messages.error(request, 'Please enter a valid email address.')
            return render(request, self.template_name)

        # Rate limiting check
        client_ip = PasswordResetToken.get_client_ip(request)
        recent_requests = PasswordResetToken.objects.filter(
            ip_address=client_ip,
            created_at__gte=timezone.now() - timedelta(minutes=5)
        ).count()

        if recent_requests >= 3:  # Max 3 requests per 5 minutes per IP
            messages.error(
                request,
                'Too many password reset requests. Please wait a few minutes before trying again.'
            )
            logger.warning(f"[PASSWORD RECOVERY] Rate limit exceeded for IP: {client_ip}")
            return render(request, self.template_name)

        try:
            # Check if user exists with this email
            try:
                user = User.objects.get(email=email, is_active=True)
                logger.info(f"[PASSWORD RECOVERY] Reset requested for user: {user.username}")

                # Create reset token
                reset_token = PasswordResetToken.objects.create_token_for_user(user)
                reset_token.set_request_metadata(request)

                token = reset_token.get_token()

                if token:
                    # Send email
                    self._send_reset_email(request, user, token)
                    logger.info(f"[PASSWORD RECOVERY] Reset email sent to {email}")
                else:
                    logger.error(f"[PASSWORD RECOVERY] Failed to generate token for {email}")

            except User.DoesNotExist:
                # For security, don't reveal if email exists or not
                logger.warning(f"[PASSWORD RECOVERY] Reset requested for non-existent email: {email}")

            # Always show success message (security best practice)
            messages.success(
                request,
                f'If {email} is associated with an account, you will receive a password reset link shortly.'
            )

        except Exception as e:
            messages.error(
                request,
                'An error occurred while processing your request. Please try again later.'
            )
            logger.error(f"[PASSWORD RECOVERY] Unexpected error for {email}: {str(e)}")

        return render(request, self.template_name)

    def _send_reset_email(self, request, user, token):
        """Send password reset email with proper template"""
        try:
            # Build reset URL
            reset_url = request.build_absolute_uri(
                f'/reset-password-confirm/{token}/'
            )

            # Email context
            context = {
                'user': user,
                'reset_url': reset_url,
                'site_name': getattr(settings, 'SITE_NAME', 'Resume Analyzer'),
                'expiry_hours': getattr(settings, 'PASSWORD_RESET_TIMEOUT_MINUTES', 60) // 60,
            }

            # Try to use HTML template if available
            try:
                html_message = render_to_string('UserAuth/password_reset_email.html', context)
                text_message = strip_tags(html_message)
            except:
                # Fallback to plain text
                text_message = f"""
Hello {user.first_name or user.username},

You requested a password reset for your account.

Click the link below to reset your password:
{reset_url}

This link will expire in {context['expiry_hours']} hour(s).

If you didn't request this, please ignore this email. Your password will not be changed.

Best regards,
{context['site_name']} Team
                """
                html_message = None

            # Send email
            send_mail(
                subject=f'Password Reset - {context["site_name"]}',
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

        except Exception as e:
            logger.error(f"[PASSWORD RECOVERY] Failed to send email to {user.email}: {str(e)}")
            raise


@method_decorator([csrf_protect, never_cache], name='dispatch')
class PasswordResetConfirmView(View):
    """Handle password reset confirmation with token"""
    template_name = 'password_reset_confirm.html'

    def get(self, request, token):
        logger.info(f"[PASSWORD RECOVERY] Reset confirmation page accessed")

        # Validate token
        reset_token = PasswordResetToken.objects.get_valid_token(token)

        if not reset_token:
            messages.error(
                request,
                'This password reset link is invalid or has expired. Please request a new one.'
            )
            logger.warning(f"[PASSWORD RECOVERY] Invalid/expired token accessed")
            return redirect('password_reset_request')

        # Check if user is still active
        if not reset_token.user.is_active:
            messages.error(request, 'This account is no longer active.')
            logger.warning(f"[PASSWORD RECOVERY] Reset attempted for inactive user: {reset_token.user.username}")
            return redirect('password_reset_request')

        logger.info(f"[PASSWORD RECOVERY] Valid token for user: {reset_token.user.username}")
        return render(request, self.template_name, {
            'token': token,
            'user': reset_token.user
        })

    def post(self, request, token):
        logger.info(f"[PASSWORD RECOVERY] Password reset form submission")

        # Validate token
        reset_token = PasswordResetToken.objects.get_valid_token(token)

        if not reset_token:
            messages.error(
                request,
                'This password reset link is invalid or has expired. Please request a new one.'
            )
            logger.warning(f"[PASSWORD RECOVERY] Invalid/expired token on form submission")
            return redirect('password_reset_request')

        # Check if user is still active
        if not reset_token.user.is_active:
            messages.error(request, 'This account is no longer active.')
            return redirect('password_reset_request')

        password1 = request.POST.get('password1', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()

        # Validate passwords
        if not password1 or not password_confirm:
            messages.error(request, 'Please fill in both password fields.')
            logger.warning(f"[PASSWORD RECOVERY] Empty password fields for user: {reset_token.user.username}")
            return render(request, self.template_name, {
                'token': token,
                'user': reset_token.user
            })

        if password1 != password_confirm:
            messages.error(request, 'The two passwords do not match. Please try again.')
            logger.warning(f"[PASSWORD RECOVERY] Password mismatch for user: {reset_token.user.username}")
            return render(request, self.template_name, {
                'token': token,
                'user': reset_token.user
            })

        # Use Django's built-in password validation
        try:
            validate_password(password1, reset_token.user)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            logger.warning(f"[PASSWORD RECOVERY] Password validation failed for user: {reset_token.user.username}")
            return render(request, self.template_name, {
                'token': token,
                'user': reset_token.user
            })

        try:
            # Reset password
            user = reset_token.user
            user.set_password(password1)
            user.save()

            # Mark token as used
            reset_token.mark_as_used()

            # Log successful reset
            logger.info(f"[PASSWORD RECOVERY] Password reset successful for user: {user.username}")

            # Optional: Log the user in automatically after reset
            if getattr(settings, 'AUTO_LOGIN_AFTER_PASSWORD_RESET', False):
                login(request, user)
                messages.success(
                    request,
                    'Password reset successfully! You have been logged in automatically.'
                )
                return redirect('home')
            else:
                messages.success(
                    request,
                    'Password reset successfully! You can now log in with your new password.'
                )
                return redirect('login')

        except Exception as e:
            messages.error(
                request,
                'An error occurred while resetting your password. Please try again or contact support.'
            )
            logger.error(f"[PASSWORD RECOVERY] Error resetting password for user {reset_token.user.username}: {str(e)}")
            return render(request, self.template_name, {
                'token': token,
                'user': reset_token.user
            })


# Legacy views for backward compatibility
@login_required()
def delete_account_legacy(request, user_id):
    """Legacy delete account function - deprecated"""
    logger.warning(f"[DELETE ACCOUNT] Legacy delete method accessed by user_id={user_id}")
    messages.warning(request, "Please use the account settings page to delete your account.")
    return redirect('user-account', user_id=request.user.id)


@login_required()
def confirm_deletion_legacy(request, username):
    """Legacy confirmation function - deprecated"""
    logger.warning(f"[DELETE ACCOUNT] Legacy confirm deletion method accessed by username={username}")
    messages.info(request, "Account deletion has been moved to the account settings page.")
    return redirect('user-account', user_id=request.user.id)