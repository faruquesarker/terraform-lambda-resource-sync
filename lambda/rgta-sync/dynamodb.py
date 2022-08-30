import logging
import boto3

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)

partition_key = "EnvironmentName"
sort_key = "Owner"

TAG_KEY_OWNER = "Owner"
TAG_KEY_ENV_NAME = "EnvironmentName"
TAG_VALUE_NO_OWNER = "NoOwnerTag"


def recreate_table(dynamodb_client, table_name):
    """
    If DynamoDB `table_name` exists then drop it and then re-create
    """
    try:
        LOG.info(f"Re-creating DynamoDB table {table_name}")
        # Get the table details
        response = dynamodb_client.describe_table(TableName=table_name)

        dyn_resource = boto3.resource('dynamodb')

        if response:
            # Delete table if it exists
            table = dyn_resource.Table(table_name)
            table.delete()
            LOG.info(f"Deleting {table.name}...")
            table.wait_until_not_exists()

        else:
            LOG.info(f"DynaoDB table: {table_name} doesn't exist!")

        # Now re-create table
        params = {
        'TableName': table_name,
        'KeySchema': [
            { 'AttributeName': 'EnvironmentName', 'KeyType': 'HASH'},
            {'AttributeName': 'Owner', 'KeyType': 'RANGE'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'Owner', 'AttributeType': 'S'},
            {'AttributeName': 'EnvironmentName', 'AttributeType': 'S'}
        ],
        'BillingMode': 'PAY_PER_REQUEST'
        }
        table = dyn_resource.create_table(**params)
        LOG.info(f"Creating {table_name}...")
        table.wait_until_exists()
        return table    
    except Exception as e:
        raise Exception((f"Error re-creating DynamoDB table {table_name}: {e}"))



def add_app_env(dynamodb_client, app_env, resources, dynamodb_table_name):
    first_resource = resources[0]
    res_arn = first_resource.get('ResourceARN')
    tags = first_resource.get("Tags")
    owner = None
    for tag in tags:        
        if tag.get('Key') == TAG_KEY_OWNER:
            owner = tag.get('Value')
            break
            
    if not owner:
        LOG.info(f"Found env without Owner: {app_env}")
        owner = TAG_VALUE_NO_OWNER
            
    try:
        LOG.info(f"Fetching App env data from DynamoDB {app_env}")
        response = dynamodb_client.get_item(
                    TableName=dynamodb_table_name,
                    Key={
                        "EnvironmentName": {"S": app_env },
                        "Owner": {"S": owner }
                        }
                   )
        item = response["Item"]
        LOG.info(f"Got from DynamoDB: {item}")
        return False
    except KeyError:
        LOG.info(f"KeyError - Fetching App env from DynamoDB {app_env}")
        # add the app_env to table 
        response =  dynamodb_client.put_item(
                        TableName=dynamodb_table_name,
                        Item={
                        "EnvironmentName": {"S": app_env },
                        "Owner": {"S": owner }
                        }
                    )
        LOG.info(f"Put item to DynamoDB table: {app_env} ")
        
        for res in resources:
            res_arn = res.get('ResourceARN')
            identifier = res_arn.split("/")[-1]
            [env_name, owner] = [str(x*0) for x in range(2) ]
            tags = res.get("Tags")
            for tag in tags:
                if tag.get('Key') == TAG_KEY_ENV_NAME:
                    env_name = tag.get('Value', '')
                elif tag.get('Key') == TAG_KEY_OWNER:
                    owner = tag.get('Value', '') 
                else:
                    LOG.DEBUG(f"Unprocessed tag: {tag}")

            service = res_arn.split(":")[2]
            type_tmp =  res_arn.split(":")[5]
            service_type = type_tmp.split('/')[0]
            region = res_arn.split(":")[3]
            resource = "Resource" + "." + identifier
            response =  dynamodb_client.update_item(
                            TableName=dynamodb_table_name,
                            Key={
                                "EnvironmentName": {"S": app_env },
                                 "Owner": {"S": owner }                                 
                            },
                            AttributeUpdates={
                                "Region": {"S": region },
                                resource : {
                                    'Value': {
                                       'M': {
                                        "Identifier": {"S": identifier},
                                        "Region": {"S": region},
                                        "Service": {"S": service },
                                        "Type": {"S": service_type},                                        
                                     }
                                    }
                                }
                            }
                        )
            LOG.info(f"Updated resource {identifier} to DynamoDB ")
        return True
    except Exception as e:
        LOG.info(e)
        raise Exception(f"Fetching App env data from DynamoDB {env_name}")