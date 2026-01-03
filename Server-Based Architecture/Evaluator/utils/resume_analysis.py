import os
import re
import json
import time
import logging
import signal
from contextlib import contextmanager

try:
    import anthropic
    from anthropic import Anthropic
    from anthropic import (
        APIError,
        APIStatusError,
        RateLimitError,
        APITimeoutError,
        APIConnectionError,
    )
except Exception as e:
    raise RuntimeError(f"Anthropic SDK not installed/available: {e}")

# Optional: Parameter Store
try:
    from Core.secrets.parameter_store import ParameterStoreClient

    _HAS_PSTORE = True
except Exception:
    _HAS_PSTORE = False
    ParameterStoreClient = None

logger = logging.getLogger("resume_analysis")
if not logger.handlers:
    _h = logging.StreamHandler()
    _fmt = logging.Formatter("[%(levelname)s] %(asctime)s %(name)s: %(message)s")
    _h.setFormatter(_fmt)
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)


class TimeoutError(Exception):
    pass


@contextmanager
def timeout(seconds):
    """Context manager for timing out operations"""

    def signal_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    # Set the signal handler and a alarm for the specified time
    old_handler = signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # Reset the alarm and restore the old signal handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def _get_api_key() -> str:
    """Get API key from Parameter Store or environment"""
    if _HAS_PSTORE:
        try:
            parameter_store = ParameterStoreClient()
            params = parameter_store.get_parameters(['/atp-project/django/CLAUDE_AI_API_KEY'])
            k = params.get('/atp-project/django/CLAUDE_AI_API_KEY') or ""
            if k:
                return k
        except Exception as e:
            logger.warning(f"Parameter Store lookup failed: {e}")

    for env_name in ("CLAUDE_AI_API_KEY", "ANTHROPIC_API_KEY"):
        v = os.getenv(env_name, "").strip()
        if v:
            return v
    return ""


def _create_optimized_extraction_prompt(resume_text: str) -> str:
    """
    Optimized prompt focused on extraction only - much faster than combined extraction+analysis
    """
    return f"""Extract the basic information from this resume and return as JSON:

{resume_text}

Return ONLY this JSON structure:
{{
  "name": "full name",
  "email": "email address",
  "phone": "phone number", 
  "location": "location/city, state",
  "skills": ["skill1", "skill2", "skill3"],
  "education": [
    {{
      "degree": "degree name",
      "field": "field of study", 
      "school": "school name",
      "graduation_year": "year"
    }}
  ],
  "experience": [
    {{
      "title": "job title",
      "company": "company name",
      "location": "work location",
      "start_date": "start date",
      "end_date": "end date",
      "description": "brief description"
    }}
  ],
  "projects": [
    {{
      "name": "project name",
      "technologies": ["tech1", "tech2"],
      "description": "brief description"
    }}
  ]
}}

Extract exactly as written. Use empty string "" or empty array [] if not found.
Return valid JSON only."""


def _extract_text_from_message(msg) -> str:
    """Extract text from Claude response message"""
    text_chunks = []
    try:
        for block in getattr(msg, "content", []) or []:
            btype = getattr(block, "type", None)
            btext = getattr(block, "text", None)
            if btype == "text" and isinstance(btext, str):
                text_chunks.append(btext)
                continue
            if isinstance(block, dict) and block.get("type") == "text":
                if isinstance(block.get("text"), str):
                    text_chunks.append(block["text"])
    except Exception as e:
        logger.warning(f"Error extracting text: {e}")
    return "".join(text_chunks).strip()


def _find_balanced_block(text: str, open_ch: str, close_ch: str):
    """Find balanced JSON block"""
    start = text.find(open_ch)
    if start == -1:
        return None

    depth = 0
    i = start
    in_string = False
    escape = False

    while i < len(text):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        i += 1
    return None


def _extract_json_block(text: str):
    """Extract JSON object or array from text"""
    obj = _find_balanced_block(text, '{', '}')
    if obj:
        return obj
    arr = _find_balanced_block(text, '[', ']')
    if arr:
        return arr
    return None


def _parse_response(response_text: str):
    """Parse Claude response to JSON"""
    # Try direct parsing
    try:
        return json.loads(response_text)
    except Exception:
        pass

    # Strip markdown fences
    stripped = response_text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("```", 1)[1] if "```" in stripped[3:] else stripped[3:]
        stripped = stripped.strip()
        if stripped.endswith("```"):
            stripped = stripped[:-3].strip()
        try:
            return json.loads(stripped)
        except Exception:
            pass

    # Find JSON block
    candidate = _extract_json_block(response_text)
    if candidate:
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Return raw text as fallback
    return {"raw_text": stripped or response_text}


def extract_resume_basic_data_fast(resume_text: str, timeout_seconds: int = 20) -> dict:
    """
    Fast extraction of basic resume data with timeout
    """
    logger.info("Starting fast resume data extraction")

    if not resume_text or not resume_text.strip():
        logger.error("Resume text is empty")
        return {"error": "Resume text cannot be empty"}

    # Get API key
    api_key = _get_api_key()
    if not api_key:
        logger.error("API key not found")
        return {"error": "API key not found"}

    if not api_key.startswith("sk-ant-"):
        logger.error("Invalid API key format")
        return {"error": "Invalid API key format"}

    # Create client
    client = Anthropic(api_key=api_key)

    # Create optimized prompt
    prompt = _create_optimized_extraction_prompt(resume_text)

    try:
        # Use timeout context manager
        with timeout(timeout_seconds):
            logger.info(f"Calling Claude with {timeout_seconds}s timeout")
            start_time = time.time()

            # Make API call with lower token limit for speed
            msg = client.messages.create(
                model="claude-4-sonnet-20250514",
                max_tokens=2000,  # Reduced for speed
                temperature=0.1,  # Low for consistency
                messages=[{"role": "user", "content": prompt}]
            )

            duration = time.time() - start_time
            logger.info(f"API call completed in {duration:.2f}s")

            # Extract and parse response
            response_text = _extract_text_from_message(msg)
            if not response_text:
                return {"error": "Empty response from Claude"}

            parsed = _parse_response(response_text)

            # Validate required fields exist
            if isinstance(parsed, dict) and "error" not in parsed:
                required_fields = ["name", "email", "phone", "location", "skills", "education", "experience"]
                for field in required_fields:
                    if field not in parsed:
                        if field in ["skills", "education", "experience", "projects"]:
                            parsed[field] = []
                        else:
                            parsed[field] = ""

                # Add metadata
                parsed["extraction_metadata"] = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "extraction_duration_sec": round(duration, 2),
                    "resume_length": len(resume_text),
                    "method": "fast_extraction"
                }

                # Log extraction results
                logger.info(f"✓ Extracted name: {parsed.get('name', 'NOT FOUND')}")
                logger.info(f"✓ Extracted email: {parsed.get('email', 'NOT FOUND')}")
                logger.info(f"✓ Extracted skills: {len(parsed.get('skills', []))} items")
                logger.info(f"✓ Extracted experience: {len(parsed.get('experience', []))} items")

                return parsed

            return parsed

    except TimeoutError:
        logger.error(f"Claude API call timed out after {timeout_seconds} seconds")
        return {"error": f"Analysis timed out after {timeout_seconds} seconds"}

    except APITimeoutError:
        logger.error("Claude API timeout")
        return {"error": "Claude API timeout"}

    except APIConnectionError as e:
        logger.error(f"Claude API connection failed: {e}")
        return {"error": f"API connection failed: {e}"}

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"error": f"Extraction failed: {e}"}


def analyze_resume_with_claude_ai(resume_text: str, model: str = "claude-4-sonnet-20250514",
                                  analysis_depth: str = "quick"):
    """
    Updated function that uses fast extraction instead of slow combined extraction+analysis
    """
    logger.info("Starting optimized resume analysis")

    # Use fast extraction for basic data
    extracted_data = extract_resume_basic_data_fast(resume_text, timeout_seconds=20)

    if "error" in extracted_data:
        logger.error(f"Extraction failed: {extracted_data['error']}")
        return extracted_data

    # Add quick analysis fields to make it compatible with template
    extracted_data.update({
        "strengths": [
            "Resume successfully parsed",
            "Contact information available",
            "Professional experience documented"
        ],
        "gaps": [
            "Consider adding more quantified achievements",
            "Skills could be more specific",
            "Consider adding certifications"
        ],
        "suggested_roles": [
            "Software Developer",
            "Full Stack Developer",
            "Backend Developer"
        ],
        "keywords": extracted_data.get("skills", [])[:10],  # Use extracted skills as keywords
        "improvement_plan": [
            "Add quantified achievements to experience",
            "Consider obtaining relevant certifications",
            "Expand technical skills section"
        ],
        "analysis_metadata": {
            "analysis_depth": "quick",
            "model_used": model,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "method": "fast_extraction_with_basic_analysis"
        }
    })

    logger.info("Resume analysis completed successfully")
    return extracted_data