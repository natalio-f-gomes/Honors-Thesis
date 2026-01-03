import requests
import logging
from Core.secrets.parameter_store import *

logger = logging.getLogger(__name__)

parameter_store = ParameterStoreClient()
def get_rapid_api_response(user_id,career_field, experience_level, job_location):
    logger.info(f"[{user_id}] attempted to retrieve job from RAPID API."
                f" {career_field} - {experience_level} - {job_location}")
    location = None
    if job_location:
        location = job_location

    else:
        location="United States"

    url = "https://jsearch.p.rapidapi.com/search"
    querystring = {
        "query": f" {experience_level} {career_field} ",

        "page": "1",
        "num_pages": "1",  # Only 1 page
        "size": "2",  # Limit to 10 jobs
        "remote_jobs_only": "false",
        "location": f"{location}"
    }



    try:
        parameter_store_credentials = parameter_store.get_parameters([
            '/atp-project/django/X_RAPID_API_KEY',
        ])

        X_RAPID_API_KEY = parameter_store_credentials.get('/atp-project/django/X_RAPID_API_KEY')
        headers = {
            "x-rapidapi-key": X_RAPID_API_KEY,
            "x-rapidapi-host": "jsearch.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()

        # Return the actual job data, not a JSON string
        if data.get('status') == 'OK' and data.get('data'):
            return data['data']  # This is the list of jobs
        else:
            logger.warning(f"No jobs found or API error: {data}")
            return []

    except Exception as e:
        logger.error(f"Error getting response from RAPID API: {e}")
        return []
