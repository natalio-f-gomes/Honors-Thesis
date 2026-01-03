#Evaluator/utils/Process_Data.py
import json

def process_job_data(job_data):
    """
    Process raw job data into a clean list of jobs with meaningful keys
    like title, location, salary, skills, description, etc.
    """
    try:
        if isinstance(job_data, str):
            job_data = json.loads(job_data)

        if not isinstance(job_data, dict) or 'data' not in job_data:
            return []

        processed_jobs = []

        for job in job_data['data']:
            if not isinstance(job, dict):
                continue

            clean_job = {}

            # Title (fallback to job_title or position if title is missing)
            clean_job["title"] = job.get("title") or job.get("job_title") or "Untitled Position"

            # Description
            clean_job["description"] = job.get("description", "")

            # Company name
            clean_job["company"] = job.get("company") or (job.get("company_object", {}).get("name"))

            # Location
            clean_job["location"] = job.get("long_location") or job.get("short_location") or job.get("location")

            # Salary
            clean_job["avg_annual_salary_usd"] = job.get("avg_annual_salary_usd")
            clean_job["salary_string"] = job.get("salary_string")

            # Employment info
            clean_job["employment_statuses"] = job.get("employment_statuses")
            clean_job["seniority"] = job.get("seniority")
            clean_job["date_posted"] = job.get("date_posted")

            # Remote/Hybrid tags
            clean_job["remote"] = job.get("remote", False)
            clean_job["hybrid"] = job.get("hybrid", False)

            # URLs (for buttons)
            clean_job["url"] = job.get("url")
            clean_job["final_url"] = job.get("final_url")
            clean_job["source_url"] = job.get("source_url")

            # Add only if there's meaningful content
            if any(clean_job.values()):
                processed_jobs.append(clean_job)

        return processed_jobs

    except Exception as e:
        print(f"Error processing job data: {e}")
        return []


def process_job_recommendation(jobs_matched):
    """
    Process raw job data into a clean list of jobs with meaningful keys
    """
    print("Input to process_job_recommendation:", type(jobs_matched))
    if isinstance(jobs_matched, str):
        print("Input is a string, first 100 chars:", jobs_matched[:100])
    elif isinstance(jobs_matched, dict):
        print("Input is a dict with keys:", jobs_matched.keys())
    try:
        if isinstance(jobs_matched, str):
            try:
                jobs_matched = json.loads(jobs_matched)
            except json.JSONDecodeError:
                print("Failed to parse jobs_matched as JSON")
                return []

            # Check if data is already in the expected format (flat dictionary with skill lists)
        if isinstance(jobs_matched, dict) and 'soft_skills' in jobs_matched and 'hard_skills' in jobs_matched:
            # Convert single item to list format expected by the rest of the code
            return [jobs_matched]

            # Original processing for {'data': [...]} format
        if not isinstance(jobs_matched, dict) or 'data' not in jobs_matched:
            return []

        recommendations = []

        for recommendation in jobs_matched['data']:
            if not isinstance(recommendation, dict):
                continue

            clean_recommendation = {}

            # Process education field
            education = recommendation.get("education") or []
            if isinstance(education, str):
                try:
                    education = json.loads(education)
                except:
                    education = [education] if education else []

            # Handle education items that are dictionaries
            education_list = []
            if isinstance(education, list):
                for edu in education:
                    if isinstance(edu, dict):
                        # If education item is a dictionary with degree and field_of_study
                        degree = edu.get('degree', '')
                        field = edu.get('field_of_study', '')
                        if degree and field:
                            education_list.append(f"{degree} in {field}")
                        elif degree:
                            education_list.append(degree)
                        elif field:
                            education_list.append(field)
                    else:
                        education_list.append(edu)
            else:
                education_list = [education] if education else []

            # Process hard_skills field
            hard_skills = recommendation.get("hard_skills") or []
            if isinstance(hard_skills, str):
                try:
                    hard_skills = json.loads(hard_skills)
                except:
                    hard_skills = [hard_skills] if hard_skills else []

            # Process soft_skills field
            soft_skills = recommendation.get("soft_skills") or []
            if isinstance(soft_skills, str):
                try:
                    soft_skills = json.loads(soft_skills)
                except:
                    soft_skills = [soft_skills] if soft_skills else []

            # Process certifications field
            certifications = recommendation.get("certifications") or []
            if isinstance(certifications, str):
                try:
                    certifications = json.loads(certifications)
                except:
                    certifications = [certifications] if certifications else []

            # Process license field
            license = recommendation.get("license") or []
            if isinstance(license, str):
                try:
                    license = json.loads(license)
                except:
                    license = [license] if license else []

            clean_recommendation["education"] = education_list
            clean_recommendation["hard_skills"] = hard_skills
            clean_recommendation["soft_skills"] = soft_skills
            clean_recommendation["certifications"] = certifications
            clean_recommendation["license"] = license

            recommendations.append(clean_recommendation)
        print("Recommendations from Identifier")
        return recommendations

    except Exception as e:
        print(f"Error processing job data: {e}")
        print("Nothing to show")
        return []