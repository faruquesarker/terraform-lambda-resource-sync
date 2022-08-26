import os
import boto3
from botocore.exceptions import ClientError

TAG_KEY_ENV_NAME = "EnvironmentName"

def get_tag_values(rgta_client, tag_key=TAG_KEY_ENV_NAME):
    try:
        paginator = rgta_client.get_paginator('get_tag_values')

        # Create a PageIterator from the Paginator object
        page_iterator = paginator.paginate(Key=tag_key)

        # Return the list of values for a given tag
        tag_values = []
        for page in page_iterator:
            tag_values.extend(page["TagValues"])
        return tag_values
    except ClientError as e:
        raise Exception(f"boto3 client error in get_tag_values: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error in paginating get_tag_values: {e}")

def get_resources(rgta_client, env_name, tag_key=TAG_KEY_ENV_NAME):
    # Get a list of resources for a given env
    try:
        paginator = rgta_client.get_paginator('get_resources')

        # Create a PageIterator from the Paginator object
        tag_filters=[
            {
                'Key': tag_key,
                'Values': [env_name, ]
            },
        ]
        page_iterator = paginator.paginate(TagFilters=tag_filters)

        resource_tag_mapping = []
        for page in page_iterator:
            resource_tag_mapping.extend(page["ResourceTagMappingList"])        
        return resource_tag_mapping
    except ClientError as e:
        raise Exception(f"boto3 client error in get_tag_values: {e}")
    except Exception as e:
        raise Exception(f"Unexpected error in paginating get_tag_values: {e}")