#Evaluator/utils/analyzer_with_claude.py


import os
import json
from Core import settings
import anthropic
from typing import Dict, List, Optional, Union
import logging
import time
from Core.secrets.parameter_store import *


parameter_store = ParameterStoreClient()

# Get logger for this module
logger = logging.getLogger(__name__)



def extract_resume_text_from_data(resume_data: Union[str, Dict]) -> str:
    """
    Extract resume text from various input formats.
    """
    logger.debug("Starting extract_resume_text_from_data function")
    logger.debug(f"Input type: {type(resume_data)}")

    if isinstance(resume_data, str):
        logger.debug("Input is already a string")
        return resume_data.strip()

    elif isinstance(resume_data, dict):
        logger.debug("Input is a dictionary - extracting text content")
        logger.debug(f"Dictionary keys: {list(resume_data.keys())}")

        extracted_text = ""
        text_parts = []

        # Try direct text field first
        if 'text' in resume_data:
            logger.debug("Found 'text' field in resume data")
            return str(resume_data['text']).strip()

        # Extract career field and experience level (high priority)
        if 'career_field' in resume_data:
            text_parts.append(f"Career Field: {resume_data['career_field']}")
        if 'experience_level' in resume_data:
            text_parts.append(f"Experience Level: {resume_data['experience_level']}")

        # Personal info
        if 'personal_info' in resume_data:
            personal = resume_data['personal_info']
            if isinstance(personal, dict):
                name = personal.get('name', '')
                email = personal.get('email', '')
                phone = personal.get('phone', '')
                location = personal.get('location', '')
                if name: text_parts.append(f"Name: {name}")
                if email: text_parts.append(f"Email: {email}")
                if phone: text_parts.append(f"Phone: {phone}")
                if location: text_parts.append(f"Location: {location}")

        # Summary/Objective
        if 'summary' in resume_data and resume_data['summary']:
            text_parts.append(f"Summary: {resume_data['summary']}")

        # Experience
        if 'experience' in resume_data and resume_data['experience']:
            text_parts.append("Experience:")
            for exp in resume_data['experience']:
                if isinstance(exp, dict):
                    title = exp.get('title', '')
                    company = exp.get('company', '')
                    duration = exp.get('duration', '')
                    description = exp.get('description', '')

                    exp_text = f"- {title} at {company}"
                    if duration: exp_text += f" ({duration})"
                    if description: exp_text += f": {description}"
                    text_parts.append(exp_text)

        # Education
        if 'education' in resume_data and resume_data['education']:
            text_parts.append("Education:")
            for edu in resume_data['education']:
                if isinstance(edu, dict):
                    degree = edu.get('degree', '')
                    institution = edu.get('institution', '')
                    year = edu.get('year', '')
                    edu_text = f"- {degree}"
                    if institution: edu_text += f" from {institution}"
                    if year: edu_text += f" ({year})"
                    text_parts.append(edu_text)

        # Skills
        if 'skills' in resume_data and resume_data['skills']:
            if isinstance(resume_data['skills'], list):
                skills_text = "Skills: " + ", ".join(resume_data['skills'])
                text_parts.append(skills_text)
            elif isinstance(resume_data['skills'], str):
                text_parts.append(f"Skills: {resume_data['skills']}")

        # Certifications
        if 'certifications' in resume_data and resume_data['certifications']:
            if isinstance(resume_data['certifications'], list):
                cert_text = "Certifications: " + ", ".join(resume_data['certifications'])
                text_parts.append(cert_text)

        # Languages
        if 'languages' in resume_data and resume_data['languages']:
            if isinstance(resume_data['languages'], list):
                lang_text = "Languages: " + ", ".join(resume_data['languages'])
                text_parts.append(lang_text)

        extracted_text = "\n".join(text_parts)
        logger.debug(f"Extracted text length: {len(extracted_text)} characters")
        return extracted_text.strip()

    else:
        logger.error(f"Unsupported resume data type: {type(resume_data)}")
        return ""


def extract_job_qualifications(jobs_list: List[Dict]) -> List[str]:
    """
    Extract all qualifications from job postings, specifically focusing on the qualifications field.
    """
    logger.info(f"Extracting qualifications from {len(jobs_list)} job postings")

    all_qualifications = []

    for i, job in enumerate(jobs_list):
        logger.debug(f"Processing job {i + 1}: {job.get('job_title', 'No title')}")

        # Extract from job_highlights.Qualifications (primary source)
        if 'job_highlights' in job and isinstance(job['job_highlights'], dict):
            qualifications = job['job_highlights'].get('Qualifications', [])
            if isinstance(qualifications, list):
                logger.debug(f"Found {len(qualifications)} qualifications in job_highlights")
                all_qualifications.extend(qualifications)

        # Also extract from job description as backup
        job_description = job.get('job_description', '')
        if job_description:
            # Look for qualification keywords in description
            qual_keywords = [
                'bachelor', 'master', 'degree', 'certification', 'certified',
                'experience', 'years', 'knowledge of', 'proficiency in',
                'skilled in', 'familiar with', 'expertise in'
            ]

            description_lower = job_description.lower()
            for keyword in qual_keywords:
                if keyword in description_lower:
                    # Extract sentences containing qualification keywords
                    sentences = job_description.split('.')
                    for sentence in sentences:
                        if keyword in sentence.lower() and len(sentence.strip()) > 10:
                            all_qualifications.append(sentence.strip())
                            break  # Only add one sentence per keyword per job

    logger.info(f"Extracted {len(all_qualifications)} total qualifications")

    # Remove duplicates while preserving order
    unique_qualifications = []
    seen = set()
    for qual in all_qualifications:
        qual_lower = qual.lower().strip()
        if qual_lower not in seen and len(qual_lower) > 5:  # Filter out very short qualifications
            seen.add(qual_lower)
            unique_qualifications.append(qual.strip())

    logger.info(f"After deduplication: {len(unique_qualifications)} unique qualifications")

    # Log sample qualifications for debugging
    for i, qual in enumerate(unique_qualifications[:5]):
        logger.debug(f"Sample qualification {i + 1}: {qual[:100]}...")

    return unique_qualifications


def get_qualification_gap_analysis_prompt(resume_text: str, qualifications: List[str]) -> str:
    """
    Generate a focused prompt for analyzing qualification gaps.
    """
    logger.debug("Generating qualification gap analysis prompt")
    logger.debug(f"Resume text length: {len(resume_text)} characters")
    logger.debug(f"Number of qualifications to analyze: {len(qualifications)}")

    # Limit qualifications to avoid token limits (keep most relevant ones)
    max_qualifications = 50
    if len(qualifications) > max_qualifications:
        qualifications = qualifications[:max_qualifications]
        logger.debug(f"Limited to {max_qualifications} qualifications to stay within token limits")

    qualifications_text = "\n".join([f"- {qual}" for qual in qualifications])

    prompt = f"""
You are a career counselor analyzing a candidate's resume against job market requirements. 

RESUME:
{resume_text}

JOB MARKET QUALIFICATIONS REQUIRED:
{qualifications_text}

Analyze what this candidate is MISSING based on the job qualifications above. Be specific and actionable.

Return ONLY a clean JSON object with exactly this structure:

{{
  "missing_technical_skills": [
    "specific skill name",
    "another missing skill"
  ],
  "missing_education": [
    "specific degree requirement",
    "additional education needed"
  ],
  "missing_certifications": [
    "certification name",
    "another certification"
  ],
  "missing_experience": [
    "specific experience type",
    "years of experience gap"
  ],
  "missing_soft_skills": [
    "communication skill",
    "leadership requirement"
  ],
  "recommended_actions": [
    "Take course in X",
    "Get certified in Y",
    "Gain experience in Z"
  ]
}}

IMPORTANT RULES:
- Only include what the candidate is actually MISSING (not what they have)
- Be specific with skill names and requirements
- Focus on the most important gaps for career advancement
- Maximum 8 items per category
- Return valid JSON only, no explanations
- If a category has no gaps, return an empty array []
"""

    logger.debug(f"Generated prompt length: {len(prompt)} characters")
    return prompt


def chat_with_claude(prompt: str) -> Optional[Dict]:
    """
    Send prompt to Claude and return parsed response.
    """
    logger.info("Starting chat_with_claude function")
    logger.debug(f"Prompt length: {len(prompt)} characters")

    try:
        # Get API key
        logger.debug("Retrieving Claude AI API key from environment")

        parameter_store_credentials = parameter_store.get_parameters([
                '/atp-project/django/CLAUDE_AI_API_KEY',
                ])

        CLAUDE_AI_API_KEY = parameter_store_credentials.get('/atp-project/django/CLAUDE_AI_API_KEY')


        if not CLAUDE_AI_API_KEY:
            logger.error("CLAUDE_AI_API_KEY not found in environment variables")
            raise ValueError("CLAUDE_AI_API_KEY not found in environment variables")

        # Validate API key format
        if not CLAUDE_AI_API_KEY.startswith('sk-ant-'):
            logger.error(f"Invalid API key format. Key starts with: {CLAUDE_AI_API_KEY[:10]}...")
            raise ValueError("Invalid API key format. Should start with 'sk-ant-'")

        logger.info(f"✓ API Key validated successfully")

        # Create Anthropic client
        logger.debug("Creating Anthropic client")
        client = anthropic.Anthropic(api_key=CLAUDE_AI_API_KEY)

        # API call parameters
        model_name = "claude-4-sonnet-20250514"
        max_tokens = 4000
        temperature = 0.1

        logger.info(f"Making API call to Claude with model: {model_name}")

        # Record start time
        start_time = time.time()

        # Make API call
        message = client.messages.create(
            model=model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Calculate duration
        duration = time.time() - start_time
        logger.info(f"✓ API call completed successfully in {duration:.2f} seconds")

        # Extract text content
        response_text = ""
        for content_block in message.content:
            if hasattr(content_block, 'text'):
                response_text += content_block.text

        logger.info(f"✓ Response length: {len(response_text)} characters")
        logger.debug(f"Response preview: {response_text[:200]}...")

        # Parse JSON response
        try:
            cleaned_response = response_text.strip()
            parsed_response = json.loads(cleaned_response)
            logger.info("✓ Successfully parsed JSON response")

            # Log summary of parsed content
            if isinstance(parsed_response, dict):
                for key, value in parsed_response.items():
                    if isinstance(value, list):
                        logger.debug(f"'{key}': {len(value)} items")
                        # Log first item if exists
                        if len(value) > 0:
                            logger.debug(f"  First {key}: {value[0]}")

            return parsed_response

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {str(e)}")
            logger.debug(f"Raw response: {response_text[:500]}...")

            # Try to extract JSON using regex
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)

            if json_match:
                logger.debug("Found potential JSON content in response")
                extracted_json = json_match.group()
                try:
                    parsed_response = json.loads(extracted_json)
                    logger.info("✓ Successfully parsed extracted JSON")
                    return parsed_response
                except json.JSONDecodeError:
                    logger.error("Failed to parse extracted JSON")

            # Return error response
            return {
                "error": "Failed to parse response",
                "raw_response": response_text[:1000],
                "response_length": len(response_text)
            }

    except anthropic.APIError as e:
        logger.error(f"❌ Anthropic API Error: {str(e)}")
        return {"error": f"API Error: {str(e)}"}

    except Exception as e:
        logger.error(f"❌ Unexpected error in chat_with_claude: {str(e)}")
        logger.exception("Full traceback:")
        return {"error": f"Unexpected error: {str(e)}"}


def analyze_resume_against_jobs(resume_data: Union[str, Dict], jobs_data: Dict) -> Optional[Dict]:
    """
    Main function to analyze resume against job postings, focusing on qualifications gaps.
    """
    logger.info("Starting qualification-focused resume analysis")
    logger.debug(f"Resume data type: {type(resume_data)}")
    logger.debug(f"Jobs data type: {type(jobs_data)}")

    # Convert resume data to text
    try:
        resume_text = extract_resume_text_from_data(resume_data)
        logger.debug(f"Resume text length: {len(resume_text)} characters")
    except Exception as e:
        logger.error(f"Error converting resume data: {str(e)}")
        return {"error": f"Failed to process resume data: {str(e)}"}

    # Validate resume text
    if not resume_text or not resume_text.strip():
        logger.error("Resume text is empty after conversion")
        return {"error": "Resume text is empty or could not be extracted"}

    # Validate and extract jobs data
    try:
        if not jobs_data or not isinstance(jobs_data, (dict, list)):
            logger.error("Invalid jobs data format")
            return {"error": "Invalid job data format"}

        # Handle different jobs data formats
        if isinstance(jobs_data, list):
            jobs_list = jobs_data
        elif isinstance(jobs_data, dict) and 'data' in jobs_data:
            jobs_list = jobs_data['data']
        else:
            logger.error("Jobs data structure not recognized")
            return {"error": "Unrecognized job data structure"}

        if not jobs_list or not isinstance(jobs_list, list):
            logger.error("No valid jobs list found")
            return {"error": "No valid job data found"}

        logger.info(f"Processing {len(jobs_list)} job postings")

    except Exception as e:
        logger.error(f"Error processing jobs data: {str(e)}")
        return {"error": f"Failed to process job data: {str(e)}"}

    try:
        # Extract qualifications from all jobs
        logger.info("Extracting qualifications from job postings")
        qualifications = extract_job_qualifications(jobs_list)

        if not qualifications:
            logger.warning("No qualifications extracted from job postings")
            return {"error": "No qualifications found in job postings"}

        # Generate focused prompt
        logger.info("Generating qualification gap analysis prompt")
        prompt = get_qualification_gap_analysis_prompt(resume_text, qualifications)

        # Get analysis from Claude
        logger.info("Sending qualification gap analysis to Claude")
        start_time = time.time()

        result = chat_with_claude(prompt)

        analysis_time = time.time() - start_time
        logger.info(f"Qualification gap analysis completed in {analysis_time:.2f} seconds")

        # Validate result
        if result and 'error' not in result:
            logger.info("✓ Qualification gap analysis completed successfully")

            # Log summary of gaps found
            if isinstance(result, dict):
                for category, items in result.items():
                    if isinstance(items, list) and len(items) > 0:
                        logger.info(f"Found {len(items)} gaps in {category}")

        return result

    except Exception as e:
        logger.error(f"❌ Error in qualification analysis: {str(e)}")
        logger.exception("Full traceback:")
        return {"error": f"Analysis failed: {str(e)}"}


def extract_resume_data_with_claude_ai(resume_text: str, model: str = "claude-4-sonnet-20250514"):
    """
    Extract structured data from resume text using Claude AI.

    Args:
        resume_text: The resume text to analyze
        model: Claude model to use (default: claude-3-5-sonnet-20241022)

    Returns:
        Parsed resume data or error string
    """
    logger.info("Starting extract_resume_data_with_claude_ai function")
    logger.debug(f"Resume text length: {len(resume_text)} characters")
    logger.debug(f"Using model: {model}")

    if not resume_text or not resume_text.strip():
        logger.error("Resume text is empty")
        return "Error: Resume text cannot be empty"

    # Create structured prompt for resume extraction
    prompt = f"""
Extract the following information from this resume and return it as valid JSON:

Resume Text:
{resume_text}

Please extract and return ONLY a JSON object with these fields:
{{
  "personal_info": {{
    "name": "Full Name",
    "email": "email@domain.com",
    "phone": "phone number",
    "location": "city, state/country"
  }},
  "summary": "Professional summary or objective",
  "experience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "duration": "Start Date - End Date",
      "description": "Job description and achievements"
    }}
  ],
  "education": [
    {{
      "degree": "Degree Type",
      "institution": "School Name",
      "year": "Graduation Year",
      "details": "Additional details if any"
    }}
  ],
  "skills": ["skill1", "skill2", "skill3"],
  "certifications": ["certification1", "certification2"],
  "languages": ["language1", "language2"]
}}

IMPORTANT RULES:
- Return only valid JSON, no explanations or additional text
- If information is not found, use null or empty arrays as appropriate
- Ensure all JSON keys are present even if values are empty
- Be accurate and extract information exactly as it appears in the resume
- For experience and education, extract all entries found
"""

    logger.debug(f"Generated extraction prompt length: {len(prompt)} characters")

    try:
        # Get API key from credentials
        parameter_store_credentials = parameter_store.get_parameters([
            '/atp-project/django/CLAUDE_AI_API_KEY',
        ])

        CLAUDE_AI_API_KEY = parameter_store_credentials.get('/atp-project/django/CLAUDE_AI_API_KEY')

        if not CLAUDE_AI_API_KEY:
            logger.error("CLAUDE_AI_API_KEY not found in credentials")
            return "Error: CLAUDE_AI_API_KEY not found in environment variables"

        if not CLAUDE_AI_API_KEY.startswith('sk-ant-'):
            logger.error(f"Invalid API key format. Key starts with: {CLAUDE_AI_API_KEY[:10]}...")
            return "Error: Invalid API key format. Should start with 'sk-ant-'"

        logger.info(f"✓ API Key validated successfully for resume extraction")

        # Create Anthropic client
        logger.debug("Creating Anthropic client for resume extraction")
        client = anthropic.Anthropic(api_key=CLAUDE_AI_API_KEY)

        # API call parameters optimized for resume extraction
        max_tokens = 3000  # Sufficient for detailed resume data
        temperature = 0.1  # Low temperature for consistent extraction

        logger.info(f"Making API call to Claude for resume extraction with model: {model}")

        # Record start time
        start_time = time.time()

        # Make API call
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Calculate duration
        duration = time.time() - start_time
        logger.info(f"✓ Resume extraction API call completed in {duration:.2f} seconds")

        # Extract text content
        response_text = ""
        for content_block in message.content:
            if hasattr(content_block, 'text'):
                response_text += content_block.text

        logger.info(f"✓ Resume extraction response length: {len(response_text)} characters")
        logger.debug(f"Response preview: {response_text[:200]}...")

        # Parse JSON response
        try:
            cleaned_response = response_text.strip()

            # Remove any markdown code blocks if present
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response.replace('```json', '').replace('```', '').strip()
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response.replace('```', '').strip()

            parsed_response = json.loads(cleaned_response)
            logger.info("✓ Successfully parsed resume extraction JSON response")

            # Validate the structure
            required_fields = ['personal_info', 'summary', 'experience', 'education', 'skills', 'certifications',
                               'languages']
            missing_fields = [field for field in required_fields if field not in parsed_response]

            if missing_fields:
                logger.warning(f"Missing fields in extracted data: {missing_fields}")
                # Add missing fields with default values
                for field in missing_fields:
                    if field in ['experience', 'education', 'skills', 'certifications', 'languages']:
                        parsed_response[field] = []
                    elif field == 'personal_info':
                        parsed_response[field] = {}
                    else:
                        parsed_response[field] = None

            # Log summary of extracted data
            if isinstance(parsed_response, dict):
                logger.info("Resume extraction summary:")
                if 'personal_info' in parsed_response and parsed_response['personal_info']:
                    name = parsed_response['personal_info'].get('name', 'Not found')
                    logger.info(f"  Name: {name}")

                if 'experience' in parsed_response:
                    logger.info(f"  Experience entries: {len(parsed_response['experience'])}")

                if 'education' in parsed_response:
                    logger.info(f"  Education entries: {len(parsed_response['education'])}")

                if 'skills' in parsed_response and isinstance(parsed_response['skills'], list):
                    logger.info(f"  Skills found: {len(parsed_response['skills'])}")

            return parsed_response

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response for resume extraction: {str(e)}")
            logger.debug(f"Raw response: {response_text[:500]}...")

            # Try to extract JSON using regex
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)

            if json_match:
                logger.debug("Found potential JSON content in resume extraction response")
                extracted_json = json_match.group()
                try:
                    parsed_response = json.loads(extracted_json)
                    logger.info("✓ Successfully parsed extracted JSON from resume extraction")
                    return parsed_response
                except json.JSONDecodeError:
                    logger.error("Failed to parse extracted JSON from resume extraction")

            # Return error message
            error_msg = f"Error: Failed to parse resume extraction response - {str(e)}"
            logger.error(error_msg)
            return error_msg

    except anthropic.APIError as e:
        error_msg = f"Error: Anthropic API Error during resume extraction - {str(e)}"
        logger.error(error_msg)
        return error_msg

    except Exception as e:
        error_msg = f"Error: Unexpected error in resume extraction - {str(e)}"
        logger.error(error_msg)
        logger.exception("Full traceback:")
        return error_msg


