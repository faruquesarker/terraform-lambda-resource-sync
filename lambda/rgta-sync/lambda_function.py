import os
import json
import logging
import boto3
from botocore.config import Config

import resource_groups_tagging_api as rgta
import dynamodb

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

LOG.info('Loading Lambda function rgta_sync...')

rgta_client = boto3.client('resourcegroupstaggingapi')

dynamodb_client = boto3.client('dynamodb')
COST_REPORT_DDB_TABLE_NAME = os.environ.get("COST_REPORT_DDB_TABLE_NAME")

def get_resource_regions():
    resource_regions = []
    raw_resource_regions = os.environ.get('COST_REPORT_RESOURCE_REGIONS')
    if raw_resource_regions: 
        raw_resource_regions = raw_resource_regions[1:-1]
        resource_regions.extend([x for x in raw_resource_regions.split(",")])
        resource_regions = [x[1:-1] for x in resource_regions]
        LOG.info("Got regions: " + str(resource_regions))
    return resource_regions

def lambda_handler(event, context):    
    # Drop and re-create DynamoDB table
    table = dynamodb.recreate_table(dynamodb_client, COST_REPORT_DDB_TABLE_NAME)

    if not table:
        return {
        'statusCode': 404,
        'body': json.dumps('Failed to re-create DynamoDB table!')
    }
    
    for region in get_resource_regions():
        config = Config(region_name=region)
        rgta_client = boto3.client('resourcegroupstaggingapi', config=config)

        # Get a list if envs
        app_envs = rgta.get_tag_values(rgta_client)
        LOG.info(f"AWS Rgion: {region} -> Got app envs: {app_envs} ")

        ## Update DynamoDB Table
        for app_env in app_envs:
            resources = rgta.get_resources(rgta_client, app_env)
            LOG.info(f"App env: {app_env} has resource count: " + str(len(resources)))
            added_to_table = dynamodb.add_app_env(dynamodb_client, app_env, resources, COST_REPORT_DDB_TABLE_NAME)
            if added_to_table:
                LOG.info(f"App Env : {app_env} from region: {region} sync'd to DynamoDB table: " + str(len(resources)))

    
    return {
        'statusCode': 200,
        'body': json.dumps('Success running Lambda RGTA Sync To DynamoDB!')
    }

