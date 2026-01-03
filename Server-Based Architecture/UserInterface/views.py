import logging
import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .forms import FeedbackForm, ContactForm
from Scanner.models import Resume
from UserAuth.models import UserProfile

# Set up logger
logger = logging.getLogger(__name__)


ADMIN_EMAIL = "admin@resume-analyzer.net" 
FEEDBACK_EMAIL_SUBJECT = 'New Feedback Received - Resume Analyzer'
CONTACT_EMAIL_SUBJECT = 'New Contact Message - Resume Analyzer'


def send_feedback_email(feedback_obj, user):
    """Send feedback notification email to admin - SIMPLIFIED VERSION"""
    try:
        # Get all the data we can
        user_info = f"Username: {user.username}\nEmail: {user.email}\nName: {user.first_name} {user.last_name}" if user else "Anonymous User"

        text_message = f"""
NEW FEEDBACK RECEIVED - Resume Analyzer

=== USER INFORMATION ===
{user_info}
User ID: {user.id if user else 'N/A'}

=== FEEDBACK DETAILS ===
Category: {getattr(feedback_obj, 'category', 'N/A')}
Rating: {getattr(feedback_obj, 'rating', 'N/A')}/5
Submitted: {getattr(feedback_obj, 'created_at', 'N/A')}

=== MESSAGE ===
{getattr(feedback_obj, 'message', 'No message found')}

=== ADMIN LINKS ===
User Profile: https://resume-analyzer.net/admin/auth/user/{user.id if user else 'N/A'}/change/

This notification was sent automatically from Resume Analyzer.
        """

        send_mail(
            subject='🎯 NEW FEEDBACK - Resume Analyzer',
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ADMIN_EMAIL],
            fail_silently=False, 
        )

        logger.info(f"[EMAIL SUCCESS] Feedback notification sent to {ADMIN_EMAIL}")
        return True

    except Exception as e:
        logger.error(f"[EMAIL ERROR] Failed to send feedback: {str(e)}")
        import traceback
        logger.error(f"[EMAIL ERROR] Full traceback: {traceback.format_exc()}")
        return False


def contact_function(request):
    logger.info(f"[CONTACT] Contact form accessed via {request.method}")

    if request.method == "POST":
        logger.info("[CONTACT] Processing POST request")

     
        logger.info(f"[CONTACT DEBUG] All POST data: {dict(request.POST)}")

        # Get form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        category = request.POST.get('category', '').strip()
        message = request.POST.get('message', '').strip()

        logger.info(f"[CONTACT DEBUG] Extracted data - Name: {name}, Email: {email}, Subject: {subject}")

        # Basic validation
        if not all([name, email, subject, message]):
            missing = []
            if not name: missing.append('name')
            if not email: missing.append('email')
            if not subject: missing.append('subject')
            if not message: missing.append('message')

            messages.error(request, f'Please fill in all required fields: {", ".join(missing)}')
            logger.warning(f"[CONTACT] Missing required fields: {missing}")
            return render(request, 'contact_page.html', {'contact_form': ContactForm()})

        try:
            # Check what fields the Contact model actualy has
            from .models import Contact
            contact_fields = [f.name for f in Contact._meta.fields]
            logger.info(f"[CONTACT DEBUG] Available Contact model fields: {contact_fields}")

            # Create contact object based on available fields
            contact_data = {
                'user': request.user if request.user.is_authenticated else None,
                'category': category or 'general',
            }

            # Map form fields to model fields flexibly
            if 'name' in contact_fields:
                contact_data['name'] = name
            elif 'user_first_name' in contact_fields:
                # Split name for old model
                name_parts = name.split(' ', 1)
                contact_data['user_first_name'] = name_parts[0]
                contact_data['user_last_name'] = name_parts[1] if len(name_parts) > 1 else ''

            if 'email' in contact_fields:
                contact_data['email'] = email
            elif 'user_email' in contact_fields:
                contact_data['user_email'] = email

            if 'subject' in contact_fields:
                contact_data['subject'] = subject
            elif 'subject_matter' in contact_fields:
                contact_data['subject_matter'] = subject

            if 'message' in contact_fields:
                contact_data['message'] = message
            elif 'message_body' in contact_fields:
                contact_data['message_body'] = message

            logger.info(f"[CONTACT DEBUG] Contact data to save: {contact_data}")

            # Create the contact object
            contact_obj = Contact.objects.create(**contact_data)
            logger.info(f"[CONTACT] Contact object created with ID: {contact_obj.id}")

            # Send email notification
            email_sent = send_contact_email(contact_obj, request.user if request.user.is_authenticated else None)

            if email_sent:
                messages.success(request, "Thank you! We have received your message and will get back to you soon!")
            else:
                messages.warning(request, "Your message was saved, but we had trouble sending the notification email.")

            return redirect('home')

        except Exception as e:
            logger.error(f"[CONTACT] Error creating contact: {str(e)}")
            import traceback
            logger.error(f"[CONTACT] Full traceback: {traceback.format_exc()}")
            messages.error(request, 'An error occurred while processing your message. Please try again.')

    return render(request, 'contact_page.html', {'contact_form': ContactForm()})


def send_contact_email(contact_obj, user):
    """Send contact notification email - flexible field access"""
    try:
        logger.info(f"[EMAIL DEBUG] Starting to send contact email...")

        # Get contact info flexibly based on available fields
        contact_fields = [f.name for f in contact_obj._meta.fields]
        logger.info(f"[EMAIL DEBUG] Contact object has fields: {contact_fields}")

        # Extract contact info based on available fields
        if hasattr(contact_obj, 'name'):
            contact_name = contact_obj.name
        elif hasattr(contact_obj, 'user_first_name'):
            first_name = getattr(contact_obj, 'user_first_name', '')
            last_name = getattr(contact_obj, 'user_last_name', '')
            contact_name = f"{first_name} {last_name}".strip()
        else:
            contact_name = 'Unknown'

        if hasattr(contact_obj, 'email'):
            contact_email = contact_obj.email
        elif hasattr(contact_obj, 'user_email'):
            contact_email = contact_obj.user_email
        else:
            contact_email = 'Unknown'

        if hasattr(contact_obj, 'subject'):
            contact_subject = contact_obj.subject
        elif hasattr(contact_obj, 'subject_matter'):
            contact_subject = contact_obj.subject_matter
        else:
            contact_subject = 'No subject'

        if hasattr(contact_obj, 'message'):
            contact_message = contact_obj.message
        elif hasattr(contact_obj, 'message_body'):
            contact_message = contact_obj.message_body
        else:
            contact_message = 'No message'

        contact_category = getattr(contact_obj, 'category', 'general')

        # Get user info
        if user and user.is_authenticated:
            user_info = f"""Registered User
Username: {user.username}
Email: {user.email}
Name: {user.first_name} {user.last_name}
User ID: {user.id}"""
        else:
            user_info = f"""Anonymous User
Name: {contact_name}
Email: {contact_email}"""

        # Create the email content
        text_message = f"""NEW CONTACT MESSAGE - Resume Analyzer

=== SENDER INFORMATION ===
{user_info}

=== MESSAGE DETAILS ===
Subject: {contact_subject}
Category: {contact_category}
Submitted: {contact_obj.created_at}

=== MESSAGE CONTENT ===
{contact_message}

=== ADMIN LINKS ==="""

        if user and user.is_authenticated:
            text_message += f"\nUser Profile: https://resume-analyzer.net/admin/auth/user/{user.id}/change/"
        else:
            text_message += f"\nAnonymous contact - no user profile"

        text_message += f"\n\nThis notification was sent automatically from Resume Analyzer."

        logger.info(f"[EMAIL DEBUG] Sending email to {ADMIN_EMAIL}")

        send_mail(
            subject='📧 NEW CONTACT MESSAGE - Resume Analyzer',
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ADMIN_EMAIL],
            fail_silently=False,
        )

        logger.info(f"[EMAIL SUCCESS] Contact notification sent successfully!")
        return True

    except Exception as e:
        logger.error(f"[EMAIL ERROR] Failed to send contact: {str(e)}")
        import traceback
        logger.error(f"[EMAIL ERROR] Full traceback: {traceback.format_exc()}")
        return False





def index(request):
    current_year = datetime.datetime.now().year
    logger.info(f"[INDEX] Rendered index.html for year {current_year}")
    return render(request, 'index.html', {'current_year': current_year})


def about_us(request):
    total_number_of_resumes = Resume.objects.count()
    logger.info(f"[The total number of resumes] returned is {total_number_of_resumes}")
    logger.info("[ABOUT US] Rendered about-us.html")
    return render(request, 'about-us.html', {"total_number_of_resumes": total_number_of_resumes})


@login_required
def feedback(request, user_id):
    logger.info(f"[FEEDBACK] Accessed feedback form for user_id={user_id}")
    if request.method == "POST":
        logger.debug("[FEEDBACK] Handling POST request")
        form = FeedbackForm(request.POST)
        if form.is_valid():
            logger.info("[FEEDBACK] Form is valid, saving feedback")
            feedback_obj = form.save(commit=False)
            feedback_obj.user = request.user
            feedback_obj.save()

            # Send email notification to admin
            email_sent = send_feedback_email(feedback_obj, request.user)

            if email_sent:
                messages.success(request,
                                 "Thank you for the feedback! We've received your message and will review it shortly.")
            else:
                messages.success(request, "Thank you for the feedback! Your message has been saved.")
                logger.warning(f"[FEEDBACK] Email notification failed for user {request.user.username}")

            return redirect('home')
        else:
            logger.warning("[FEEDBACK] Invalid form submission")
            messages.error(request, "Please correct the errors in the form.")
    else:
        logger.debug("[FEEDBACK] Handling GET request")
        form = FeedbackForm()
    return render(request, 'feedback.html', {'messages': messages, 'feedback_form': form, "user_id": user_id})


def feedback_page(request):
    user_id = request.user.id if request.user.is_authenticated else None
    logger.info(f"[FEEDBACK PAGE] Loaded feedback page for user_id={user_id}")
    return render(request, 'feedback.html', {'messages': messages, 'user_id': user_id, 'feedback_form': FeedbackForm})


def login_page(request):
    logger.info("[LOGIN PAGE] Rendered login.html")
    return render(request, 'login.html', {})


def register_page(request):
    logger.info("[REGISTER PAGE] Rendered register.html")
    return render(request, 'register.html', {})


def get_user_information(user_object: User):
    logger.debug(f"[USER INFO] Fetching info for user: {user_object.username}")
    return {
        "user_name": user_object.username,
        "first_name": user_object.first_name,
        "last_name": user_object.last_name,
        "email": user_object.email
    }


def custom_error_404(request):
    logger.warning("[ERROR 404] Page not found")
    messages.warning(request, "Page Not found")
    return render(request, 'error_404.html', {})


@login_required()
def user_account(request, user_id):
    logger.info(f"[USER ACCOUNT] Access attempt for user_id={user_id}")
    try:
        user = User.objects.get(pk=user_id)
        user_profile = UserProfile.objects.get(user=user)
        message = ""
        try:
            if user_profile.get_resume_uploaded() == user_profile.get_resume_limit():
                message = "You have reached the maximum resume uploaded per account"
            else:
                message = f"You can scan {user_profile.get_resume_limit() - user_profile.get_resume_uploaded()} more resumes."
            logger.info(f"[USER ACCOUNT] Resume status: {message}")
        except Exception as error:
            logger.error(f"[USER ACCOUNT] Resume status error: {error}")
        user_resumes = Resume.objects.filter(user_id=user_id)

        real_resume_count = user_resumes.count()
        if user_profile.get_resume_uploaded() != real_resume_count:
            logger.info(f"[USER ACCOUNT] Syncing resume count: {real_resume_count}")
            user_profile.set_resume_uploaded(real_resume_count)
            user_profile.save()

    except User.DoesNotExist:
        logger.error(f"[USER ACCOUNT] User with ID {user_id} does not exist")
        messages.error(request, "This user does not exist")
        return redirect("page_not_found")

    if user.id == request.user.id:
        user_info = get_user_information(user)
        return render(request, "user_account.html", {
            'user_profile': user_profile,
            "user_information": user_info,
            "user_resumes": user_resumes,
            "resume_message": message,
            "user_id": user.id,
            "username": user.username
        })
    else:
        logger.warning("[USER ACCOUNT] Unauthorized access attempt")
        messages.error(request, "You do not have access to this account")
        return redirect('home')


@login_required()
def reset_password_page(request, user_id):
    logger.info(f"[RESET PASSWORD] Reset attempt for user_id={user_id}")
    try:
        user_account = User.objects.get(pk=user_id)
        if user_account.id == request.user.id:
            logger.info("[RESET PASSWORD] Authorized password reset page load")
            user_info = get_user_information(user_account)
            return render(request, 'reset_password_page.html', {"user_info": user_info})
        else:
            logger.warning("[RESET PASSWORD] Unauthorized reset attempt")
            messages.error(request, "You do not have access to this account. Please Login into YOUR account.")
            return redirect('login')
    except User.DoesNotExist:
        logger.error(f"[RESET PASSWORD] User with ID {user_id} does not exist")
        messages.error(request, "This User does not exist")
        return redirect('login')


def terms_and_conditions(request):
    return render(request, "terms_and_conditions.html")



def contact_page(request):
    return render(request, "contact_page.html", {"contact_form": ContactForm})


def contact_function(request):
    logger.info(f"[CONTACT PAGE] Accessed!")
    if request.method == "POST":
        logger.debug("[MESSAGE] Handling POST request")
        form = ContactForm(request.POST)
        if form.is_valid():
            logger.info("[MESSAGE FORM] Form is valid, saving contact message")
            contact_obj = form.save(commit=False)
            contact_obj.user = request.user if request.user.is_authenticated else None
            contact_obj.save()

            # Send email notification to admin
            email_sent = send_contact_email(contact_obj, request.user if request.user.is_authenticated else None)

            if email_sent:
                messages.success(request, "We have received your message and will reach out to you soon!")
            else:
                messages.success(request, "We have received your message and will review it shortly.")
                logger.warning(f"[CONTACT] Email notification failed")

            return redirect('home')
        else:
            logger.warning("[CONTACT] Invalid form submission")
            messages.error(request, "Please correct the errors in the form.")
    else:
        logger.debug("[CONTACT] Handling GET request")
        form = ContactForm()
    return render(request, 'contact_page.html', {'messages': messages, 'contact_form': form})