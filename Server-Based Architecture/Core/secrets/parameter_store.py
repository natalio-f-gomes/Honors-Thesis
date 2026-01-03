import boto3
import logging
from botocore.exceptions import ClientError
from django.conf import settings

logger = logging.getLogger(__name__)


class ParameterStoreClient:
    def __init__(self, region_name=None):
        self.region_name = region_name or getattr(settings, 'AWS_DEFAULT_REGION', 'us-east-1')
        self.ssm_client = boto3.client('ssm', region_name=self.region_name)

    def get_parameter(self, parameter_name, decrypt=True):
        """
        Retrieve a single parameter from Parameter Store
        """
        try:
            response = self.ssm_client.get_parameter(
                Name=parameter_name,
                WithDecryption=decrypt
            )
            return response['Parameter']['Value']
        except ClientError as e:
            logger.error(f"Error retrieving parameter {parameter_name}: {e}")
            raise

    def get_parameters(self, parameter_names, decrypt=True):
        """
        Retrieve multiple parameters from Parameter Store
        """
        try:
            response = self.ssm_client.get_parameters(
                Names=parameter_names,
                WithDecryption=decrypt
            )

            parameters = {}
            for param in response['Parameters']:
                parameters[param['Name']] = param['Value']

            # Log any invalid parameters
            if response['InvalidParameters']:
                logger.warning(f"Invalid parameters: {response['InvalidParameters']}")

            return parameters
        except ClientError as e:
            logger.error(f"Error retrieving parameters: {e}")
            raise

    def get_parameters_by_path(self, path, decrypt=True, recursive=True):
        """
        Retrieve all parameters under a specific path
        """
        try:
            parameters = {}
            paginator = self.ssm_client.get_paginator('get_parameters_by_path')

            for page in paginator.paginate(
                    Path=path,
                    Recursive=recursive,
                    WithDecryption=decrypt
            ):
                for param in page['Parameters']:
                    # Remove the path prefix from the parameter name for easier access
                    key = param['Name'].replace(path, '').lstrip('/')
                    parameters[key] = param['Value']

            return parameters
        except ClientError as e:
            logger.error(f"Error retrieving parameters by path {path}: {e}")
            raise



