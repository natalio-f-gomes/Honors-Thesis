import logging
import os
import re
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .forms import ResumeForm
from .models import Resume
from UserAuth.models import UserProfile

import PyPDF2

# Updated import - use the fast extraction function
from Evaluator.utils.resume_analysis import extract_resume_basic_data_fast
from Evaluator.utils.get_jobs import get_rapid_api_response

logger = logging.getLogger(__name__)


def _parse_resume_json(raw):
    """
    Ensure we return a dict with the keys the template expects.
    Accepts dict or JSON string; coerces fields to the right types.
    """
    logger.info(f"[PARSE JSON] Received raw data type: {type(raw)}")

    data = {}
    if isinstance(raw, dict):
        data = raw
        logger.info("[PARSE JSON] Data is already a dict")
    elif isinstance(raw, str):
        try:
            data = json.loads(raw)
            logger.info("[PARSE JSON] Successfully parsed JSON string")
        except Exception as e:
            logger.exception(f"[PARSE JSON] Failed to json-parse extracted_text: {e}")
            return {}
    else:
        logger.warning(f"[PARSE JSON] Unexpected data type: {type(raw)}")
        return {}

    # Check for error in data
    if "error" in data:
        logger.error(f"[PARSE JSON] Error in parsed data: {data['error']}")
        return {}

    # Log the keys we found
    logger.info(f"[PARSE JSON] Available keys in parsed data: {list(data.keys())}")

    # Coerce types / provide defaults the template expects
    data.setdefault("name", "")
    data.setdefault("email", "")
    data.setdefault("phone", "")
    data.setdefault("location", "")
    data.setdefault("skills", [])
    data.setdefault("education", [])
    data.setdefault("experience", [])
    data.setdefault("projects", [])
    data.setdefault("job_search_request", {})

    # Log what we found for each field
    logger.info(f"[PARSE JSON] Name: {data.get('name', 'MISSING')}")
    logger.info(f"[PARSE JSON] Name: {data.get('email', 'MISSING')}")
    logger.info(f"[PARSE JSON] Phone: {data.get('phone', 'MISSING')}")
    logger.info(f"[PARSE JSON] Skills count: {len(data.get('skills', []))}")
    logger.info(f"[PARSE JSON] Education count: {len(data.get('education', []))}")
    logger.info(f"[PARSE JSON] Experience count: {len(data.get('experience', []))}")

    # If a provider returned a comma-separated string for skills, make it a list
    if isinstance(data["skills"], str):
        data["skills"] = [s.strip() for s in data["skills"].split(",") if s.strip()]
        logger.info(f"[PARSE JSON] Converted skills string to list: {len(data['skills'])} items")

    # Ensure education/experience/projects are lists (some LLMs return dict or None)
    for key in ("education", "experience", "projects"):
        if isinstance(data[key], dict):
            data[key] = [data[key]]
            logger.info(f"[PARSE JSON] Converted {key} from dict to list")
        elif not isinstance(data[key], list):
            data[key] = []
            logger.info(f"[PARSE JSON] Set {key} to empty list (was {type(data[key])})")

    logger.info(f"[PARSE JSON] Final data structure ready for template")
    return data


def get_jobs_for_resume(resume_model):
    """Get relevant jobs using your existing RAPID API"""
    logger.info(f"[GET JOBS] Getting jobs for resume ID {resume_model.id}")
    try:
        jobs = get_rapid_api_response(
            user_id=resume_model.user.id,
            career_field=resume_model.career_field,
            experience_level=resume_model.experience_level,
            job_location=resume_model.preferred_location
        )
        logger.info(f"[GET JOBS] Found {len(jobs)} jobs")
        return jobs
    except Exception as e:
        logger.error(f"[GET JOBS] Error getting jobs: {e}")
        return []


def validate_resume(extracted_text: str) -> bool:
    """Light sanity check that the text looks like a resume."""
    logger.debug("[VALIDATE RESUME] Validating resume text")
    resume_keywords = [
        "skills", "experience", "education", "references", "work history",
        "objective", "summary", "portfolio", "contact", "email", "phone"
    ]
    keyword_count = sum(extracted_text.lower().count(keyword) for keyword in resume_keywords)

    name_pattern = r"[A-Z][a-z]+\s[A-Z][a-z]+"
    phone_pattern = r"\d{3}-\d{3}-\d{4}"
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    section_pattern = r"(SKILLS|EDUCATION|EXPERIENCE|Work History|Portfolio|Summary|Objective)"

    name_matches = len(re.findall(name_pattern, extracted_text))
    phone_matches = len(re.findall(phone_pattern, extracted_text))
    email_matches = len(re.findall(email_pattern, extracted_text))
    section_matches = len(re.findall(section_pattern, extracted_text, re.IGNORECASE))

    logger.info(
        f"[VALIDATE RESUME] Keywords: {keyword_count}, Name: {name_matches}, "
        f"Phone: {phone_matches}, Email: {email_matches}, Sections: {section_matches}"
    )

    return (
            keyword_count >= 3 and
            name_matches >= 1 and
            phone_matches >= 1 and
            email_matches >= 1 and
            section_matches >= 2
    )


def extract_text_from_pdf(resume_model):
    """Extract text from PDF resume and run fast Claude analysis."""
    logger.info(f"[EXTRACT PDF] Extracting text for resume ID {resume_model.id}")
    try:
        file_field = resume_model.resume_file
        with file_field.open('rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            logger.debug(f"[EXTRACT PDF] PDF has {len(pdf_reader.pages)} pages")

            text = []
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text() or ""
                logger.debug(f"[EXTRACT PDF] Page {i + 1} text length: {len(page_text)}")
                text.append(page_text)

            full_text = "".join(text)
            logger.info(f"[EXTRACT PDF] Total extracted text length: {len(full_text)}")

            # Debug: Show first 500 characters of extracted text
            logger.info(f"[EXTRACT PDF] First 500 chars: {full_text[:500]}...")

            # Guard: scanned PDFs often yield empty text without OCR
            if not full_text.strip():
                logger.warning("[EXTRACT PDF] No selectable text; likely a scanned PDF.")
                return -1

            # Call fast Claude AI extraction with timeout
            logger.info("[EXTRACT PDF] Sending to Claude AI for fast extraction...")
            claude_result = extract_resume_basic_data_fast(full_text, timeout_seconds=20)

            # Debug: Log Claude AI response
            logger.info(f"[EXTRACT PDF] Claude AI response type: {type(claude_result)}")

            # Check for errors
            if isinstance(claude_result, dict) and "error" in claude_result:
                logger.error(f"[EXTRACT PDF] Claude AI error: {claude_result['error']}")
                return -1

            logger.info("[EXTRACT PDF] Claude AI extraction successful")
            return claude_result

    except Exception as error:
        logger.error(f"[EXTRACT PDF] Error extracting PDF text: {error}")
        return -1


def extract_text_from_resume(resume_model):
    """
    PDF-only extraction. Returns processed text (dict) or -1 on error.
    """
    logger.info(f"[EXTRACT RESUME] Starting extraction for resume ID {resume_model.id}")
    try:
        file_name = resume_model.resume_file.name.lower()
        file_extension = os.path.splitext(file_name)[1]
        logger.info(f"[EXTRACT RESUME] File extension: {file_extension}")

        if file_extension != '.pdf':
            logger.error(f"[EXTRACT RESUME] Unsupported file type for PDF-only mode: {file_extension}")
            return -1

        return extract_text_from_pdf(resume_model)

    except Exception as error:
        logger.error(f"[EXTRACT RESUME] Error extracting resume text: {error}")
        return -1


@login_required()
def resume_upload_page(request, username):
    logger.info(f"[UPLOAD PAGE] Resume upload page access for username={username}")
    if request.user.username == username:
        return render(request, "resume_upload_page.html", {"form": ResumeForm()})
    else:
        messages.error(request, "You do not have access to this website")
        logger.warning("[UPLOAD PAGE] Unauthorized access attempt")
        return redirect('login')


@login_required()
def resume_file_upload(request, username):
    logger.info(f"[FILE UPLOAD] Uploading resume for username={username}")

    if request.user.username != username:
        logger.warning("[FILE UPLOAD] Unauthorized upload attempt")
        messages.error(request, "Please login to your account!")
        return redirect("login")

    try:
        user_profile = UserProfile.objects.get(user=request.user)
    except UserProfile.DoesNotExist:
        logger.error(f"[FILE UPLOAD] UserProfile does not exist for user={request.user.username}")
        messages.error(request, "User profile not found")
        return redirect("profile")

    # Enforce upload limits
    if user_profile.resume_uploaded >= user_profile.resume_limit:
        logger.warning(f"[FILE UPLOAD] Resume upload limit reached for user {username}")
        messages.error(request, "Upload limit reached")
        return redirect("home")

    if request.method == "POST":
        resume_form = ResumeForm(request.POST, request.FILES)

        if resume_form.is_valid():
            try:
                # Save the resume with all form data
                resume = resume_form.save(commit=False)
                resume.user = request.user
                resume.save()

                logger.info(f"[FILE UPLOAD] Resume uploaded for user {username} (ID={resume.id})")
                logger.info(f"[FILE UPLOAD] Career field: {resume.career_field}")
                logger.info(f"[FILE UPLOAD] Experience level: {resume.experience_level}")
                logger.info(f"[FILE UPLOAD] Preferred Location: {resume.preferred_location}")

                # Enforce PDF-only immediately
                file_extension = os.path.splitext(resume.resume_file.name.lower())[1]
                logger.info(f"[FILE UPLOAD] File type: {file_extension}")

                if file_extension != '.pdf':
                    logger.warning("[FILE UPLOAD] Non-PDF upload rejected in PDF-only mode")
                    messages.error(request, "Only PDF resumes are supported. Please upload a .pdf file.")
                    # Do not increment; delete the placeholder resume
                    resume.delete()
                    return redirect("resume_upload_page", request.user.username)

                # PDF accepted; processing happens later on detail page
                messages.success(request, "PDF resume uploaded successfully!")

                # Increment user's upload count ONLY on success
                user_profile.increment_resume_upload()

                # Redirect to detail page where extraction will occur
                return redirect("resume_detail_page", request.user.username, resume.id)

            except Exception as error:
                logger.error(f"[FILE UPLOAD] Error saving resume: {error}")
                messages.error(request, f"Error uploading resume: {str(error)}")

        else:
            # Form validation failed
            logger.warning(f"[FILE UPLOAD] Invalid resume form. Errors: {resume_form.errors}")
            for field, errors in resume_form.errors.items():
                for error in errors:
                    if field == 'resume_file':
                        messages.error(request, f"File upload error: {error}")
                    elif field == 'career_field':
                        messages.error(request, f"Career field error: {error}")
                    elif field == 'experience_level':
                        messages.error(request, f"Experience level error: {error}")
                    else:
                        messages.error(request, f"{field}: {error}")
    else:
        # GET request - show empty form
        resume_form = ResumeForm()

    return render(request, "resume_upload_page.html", {"form": resume_form})


@login_required()
def resume_detail_page(request, username, resume_id):
    logger.info(f"[DETAIL PAGE] Resume detail request for resume_id={resume_id} by {username}")

    if request.user.username != username:
        logger.warning("[DETAIL PAGE] Unauthorized detail access attempt")
        messages.error(request, "Please login to YOUR account!")
        return redirect("login")

    resume_obj = get_object_or_404(Resume, id=resume_id, user__username=username)

    file_extension = os.path.splitext(resume_obj.resume_file.name.lower())[1]
    logger.debug(f"[DETAIL PAGE] Resume file type: {file_extension}")

    # If not already extracted, do it now with timeout
    if not resume_obj.get_extracted_text():
        try:
            logger.info(f"[DETAIL PAGE] Extracting text for resume ID {resume_id}")
            extracted_data = extract_text_from_resume(resume_obj)

            if not extracted_data or extracted_data == -1:
                logger.warning(f"[DETAIL PAGE] Resume extraction failed for {file_extension} file")
                if file_extension == '.pdf':
                    error_msg = (
                        "Failed to process PDF resume. This could be due to a timeout or "
                        "the PDF containing scanned images without selectable text."
                    )
                else:
                    error_msg = "Only PDF files are supported."
                messages.error(request, error_msg)

                try:
                    user_profile = UserProfile.objects.get(user=request.user)
                    if user_profile.resume_uploaded > 0:
                        user_profile.resume_uploaded -= 1
                        user_profile.save()
                    resume_obj.delete_resume_by_id(resume_id)
                    logger.info(f"[DETAIL PAGE] Deleted invalid resume ID {resume_id}")
                except Exception as e:
                    logger.error(f"[DETAIL PAGE] Failed to delete resume ID {resume_id}: {e}")

                return redirect("resume_upload_page", request.user.username)

            # Check if extraction returned an error
            if isinstance(extracted_data, dict) and "error" in extracted_data:
                logger.error(f"[DETAIL PAGE] Extraction error: {extracted_data['error']}")

                # Handle timeout specifically
                if "timeout" in extracted_data["error"].lower():
                    error_msg = "Resume processing timed out. Please try uploading again or contact support."
                else:
                    error_msg = f"Resume processing failed: {extracted_data['error']}"

                messages.error(request, error_msg)

                try:
                    user_profile = UserProfile.objects.get(user=request.user)
                    if user_profile.resume_uploaded > 0:
                        user_profile.resume_uploaded -= 1
                        user_profile.save()
                    resume_obj.delete_resume_by_id(resume_id)
                    logger.info(f"[DETAIL PAGE] Deleted failed resume ID {resume_id}")
                except Exception as e:
                    logger.error(f"[DETAIL PAGE] Failed to delete resume ID {resume_id}: {e}")

                return redirect("resume_upload_page", request.user.username)

            # Save processed data
            resume_obj.set_extracted_text(extracted_data)
            logger.info(f"[DETAIL PAGE] Successfully extracted and saved text for resume ID {resume_id}")

        except Exception as e:
            logger.error(f"[DETAIL PAGE] Exception while extracting PDF resume: {e}")
            messages.error(request, f"Error processing PDF resume: {str(e)}")
            return redirect("resume_upload_page", request.user.username)

    # Parse JSON/dict into a dict for the template
    raw = resume_obj.get_extracted_text()
    logger.info(f"[DETAIL PAGE] Raw extracted text type: {type(raw)}")

    parsed = _parse_resume_json(raw)

    if not parsed:
        logger.error("[DETAIL PAGE] Failed to parse extracted data")
        messages.error(request, "Failed to parse resume data. Please try uploading again.")
        return redirect("resume_upload_page", request.user.username)

    logger.info(f"[DETAIL PAGE] Parsed data keys: {list(parsed.keys())}")

    return render(request, "resume_detail_page.html", {
        # The template expects 'resume_file' to be an object/dict with fields
        "resume_file": parsed,
        # Keep the actual model available as 'resume' (used for get_*_display)
        "resume": resume_obj,
        "username": username,
        "resume_id": resume_obj.id,
    })