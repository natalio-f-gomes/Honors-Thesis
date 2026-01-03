import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from Evaluator.utils.analyzer_with_claude import *
from Scanner.models import Resume
from UserAuth.models import UserProfile

# Set up logger
logger = logging.getLogger(__name__)


@login_required()
def jobs_matched_page_from_resume_file(request, username, resume_id):
    logger.info(f"[JOBS MATCHED] Request by user={request.user.username} for resume_id={resume_id}")

    if request.user.username != username:
        logger.warning(f"[JOBS MATCHED] Unauthorized access by {request.user.username} to resume owned by {username}")
        messages.error(request, "Please login to YOUR RESUME")
        return redirect("login")

    try:
        resume_file = Resume.objects.get(pk=resume_id, user=request.user)
    except Resume.DoesNotExist:
        messages.error(request, "Resume not found.")
        return redirect("home")

    # Get jobs data
    jobs_matched = resume_file.get_jobs_matched()

    # Debug logging
    logger.info(f"Jobs data type: {type(jobs_matched)}")
    logger.info(f"Number of jobs: {len(jobs_matched) if jobs_matched else 0}")

    if jobs_matched and len(jobs_matched) > 0:
        logger.info(f"First job keys: {list(jobs_matched[0].keys())}")

    context = {
        "resume_file": resume_file,
        "jobs_matched": jobs_matched,
        "resume_id": resume_id,
    }
    return render(request, "jobs_matched_from_resume_file_page.html", context)


def build_comprehensive_resume_data(resume_file):
    """
    Build comprehensive resume data including career field, experience level, and extracted text.
    """
    logger.info(f"[RESUME DATA] Building comprehensive data for resume_id={resume_file.id}")

    # Start with extracted text data
    resume_data = resume_file.get_extracted_text() or {}

    # Ensure resume_data is a dictionary
    if not isinstance(resume_data, dict):
        logger.warning(f"[RESUME DATA] Extracted text is not a dict, converting: {type(resume_data)}")
        resume_data = {}

    # Add career field and experience level (HIGH PRIORITY)
    if resume_file.career_field:
        resume_data["career_field"] = resume_file.career_field
        logger.info(f"[RESUME DATA] Added career field: {resume_file.career_field}")

    if resume_file.experience_level:
        resume_data["experience_level"] = resume_file.experience_level
        logger.info(f"[RESUME DATA] Added experience level: {resume_file.experience_level}")

    # Add preferred location
    if resume_file.preferred_location:
        resume_data["preferred_location"] = resume_file.preferred_location
        logger.info(f"[RESUME DATA] Added preferred location: {resume_file.preferred_location}")

    logger.debug(f"[RESUME DATA] Final resume data keys: {list(resume_data.keys())}")
    return resume_data


def normalize_jobs_data(jobs_data):
    """
    Normalize jobs data to ensure consistent structure for analysis.
    Expected output: List of job dictionaries
    """
    logger.info("[JOBS DATA] Starting normalization")
    logger.debug(f"Input jobs data type: {type(jobs_data)}")

    if not jobs_data:
        logger.warning("Jobs data is None or empty")
        return []

    # Case 1: jobs_data is already a list of jobs
    if isinstance(jobs_data, list):
        logger.info(f"Jobs data is already a list with {len(jobs_data)} jobs")
        return jobs_data

    # Case 2: jobs_data is a dict with 'data' key containing list
    if isinstance(jobs_data, dict) and 'data' in jobs_data:
        data = jobs_data['data']
        if isinstance(data, list):
            logger.info(f"Extracted {len(data)} jobs from 'data' key")
            return data
        elif isinstance(data, str):
            # Try to parse JSON string
            try:
                import json
                parsed_data = json.loads(data)
                if isinstance(parsed_data, list):
                    logger.info(f"Parsed JSON string to list with {len(parsed_data)} jobs")
                    return parsed_data
                else:
                    logger.warning(f"Parsed JSON is not a list: {type(parsed_data)}")
                    return [parsed_data] if parsed_data else []
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON string: {e}")
                return []

    # Case 3: jobs_data is a string (JSON)
    if isinstance(jobs_data, str):
        try:
            import json
            parsed_data = json.loads(jobs_data)
            if isinstance(parsed_data, list):
                logger.info(f"Parsed JSON string to list with {len(parsed_data)} jobs")
                return parsed_data
            elif isinstance(parsed_data, dict) and 'data' in parsed_data:
                return normalize_jobs_data(parsed_data)  # Recursive call
            else:
                return [parsed_data] if parsed_data else []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse jobs JSON string: {e}")
            return []

    # Case 4: Single job object
    if isinstance(jobs_data, dict):
        # Check if this looks like a single job
        job_indicators = ['job_title', 'job_description', 'employer_name', 'job_highlights']
        if any(key in jobs_data for key in job_indicators):
            logger.info("Jobs data appears to be a single job - wrapping in list")
            return [jobs_data]

    logger.error(f"Unknown jobs data structure: {type(jobs_data)}")
    return []


@login_required()
def recommendation_skills_page(request, username, resume_id):
    logger.info(
        f"[RECOMMENDATION] Request for skills recommendation by user={request.user.username} on resume_id={resume_id}")

    if request.user.username != username:
        logger.warning(
            f"[RECOMMENDATION] Unauthorized access attempt by {request.user.username} to resume of {username}")
        messages.error(request, "PLEASE LOGIN TO YOUR OWN ACCOUNT")
        return redirect("login")

    try:
        user_profile = UserProfile.objects.get(user=request.user)
        resume_file = get_object_or_404(Resume, id=resume_id, user__username=username)

        # Check if recommendations already exist
        existing_recommendations = resume_file.get_recommendation_skills()
        if existing_recommendations and not request.GET.get('refresh'):
            logger.info(f"[RECOMMENDATION] Using existing recommendations for resume_id={resume_id}")
            context = {
                "recommended_skills": existing_recommendations,
                "resume": resume_file,
                "user_profile": user_profile
            }
            return render(request, "recommended_skills.html", context)

        # Generate new recommendations
        logger.info(f"[RECOMMENDATION] Generating new recommendations for resume_id={resume_id}")

        try:
            # Build comprehensive resume data
            logger.debug("Building comprehensive resume data")
            extracted_resume_data = build_comprehensive_resume_data(resume_file)

            # Get and normalize jobs data
            logger.debug("Getting jobs data")
            raw_jobs_data = resume_file.get_jobs_matched()
            normalized_jobs_data = normalize_jobs_data(raw_jobs_data)

            # Debug logging
            logger.info(f"Resume data type: {type(extracted_resume_data)}")
            logger.info(f"Normalized jobs data: {len(normalized_jobs_data)} jobs")

            if extracted_resume_data:
                logger.info(f"Resume data keys: {list(extracted_resume_data.keys())}")
                logger.info(f"Career field: {extracted_resume_data.get('career_field', 'Not set')}")
                logger.info(f"Experience level: {extracted_resume_data.get('experience_level', 'Not set')}")

            if normalized_jobs_data:
                # Log sample job data
                sample_job = normalized_jobs_data[0]
                logger.info(f"Sample job keys: {list(sample_job.keys())}")
                logger.info(f"Sample job title: {sample_job.get('job_title', 'No title')}")

                # Check for job_highlights structure
                if 'job_highlights' in sample_job:
                    highlights = sample_job['job_highlights']
                    logger.info(
                        f"Job highlights keys: {list(highlights.keys()) if isinstance(highlights, dict) else 'Not a dict'}")
                    if isinstance(highlights, dict) and 'Qualifications' in highlights:
                        qualifications = highlights['Qualifications']
                        logger.info(
                            f"Sample qualifications count: {len(qualifications) if isinstance(qualifications, list) else 'Not a list'}")

            # Validate data before analysis
            if not extracted_resume_data:
                logger.error("No resume data available for analysis")
                messages.error(request, "No resume data found. Please upload a resume first.")
                return redirect("home")

            if not normalized_jobs_data:
                logger.error("No jobs data available for analysis")
                messages.error(request, "No job data found. Please ensure jobs are loaded first.")
                return redirect("jobs_matched_from_resume_file", username=username, resume_id=resume_id)

            # Run analysis with normalized data
            logger.info("Starting qualification gap analysis")
            result = analyze_resume_against_jobs(extracted_resume_data, normalized_jobs_data)

            if result and 'error' not in result:
                # Save successful results
                resume_file.set_recommendation_skills(result)
                logger.info(f"[RECOMMENDATION] Successfully saved recommendations for resume_id={resume_id}")

                # Log summary of recommendations
                if isinstance(result, dict):
                    for category, items in result.items():
                        if isinstance(items, list) and len(items) > 0:
                            logger.info(f"Found {len(items)} recommendations in {category}")

            else:
                error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                logger.warning(f"[RECOMMENDATION] Analysis failed: {error_msg}")
                messages.error(request, f"Analysis failed: {error_msg}")
                result = {"error": error_msg}

        except Exception as e:
            logger.error(f"[RECOMMENDATION] Exception during analysis: {str(e)}", exc_info=True)
            messages.error(request, f"Failed to analyze resume: {str(e)}")
            result = {"error": str(e)}

        context = {
            "recommended_skills": result,
            "resume": resume_file,
            "user_profile": user_profile
        }
        return render(request, "recommended_skills.html", context)

    except UserProfile.DoesNotExist:
        logger.error(f"[RECOMMENDATION] UserProfile does not exist for user={request.user.username}")
        messages.error(request, "User profile not found")
        return redirect("profile")

    except Exception as e:
        logger.error(f"[RECOMMENDATION] Unexpected error in view: {str(e)}", exc_info=True)
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect("home")