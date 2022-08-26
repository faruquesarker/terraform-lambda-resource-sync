import boto3
import ec2

partition_key = "EnvironmentName"
sort_key = "Creator"

TAG_KEY_CREATOR = "Creator"
TAG_KEY_ENV_NAME = "EnvironmentName"
TAG_VALUE_NO_CREATOR = "NoCreatorTag"


def recreate_table(dynamodb_client, table_name):
    """
    If DynamoDB `table_name` exists then drop it and then re-create
    """
    try:
        print(f"Re-creating DynamoDB table {table_name}")
        # Get the table details
        response = dynamodb_client.describe_table(TableName=table_name)

        dyn_resource = boto3.resource('dynamodb')

        if response:
            # Delete table if it exists
            table = dyn_resource.Table(table_name)
            table.delete()
            print(f"Deleting {table.name}...")
            table.wait_until_not_exists()

        else:
            print(f"DynaoDB table: {table_name} doesn't exist!")

        # Now re-create table
        params = {
        'TableName': table_name,
        'KeySchema': [
            { 'AttributeName': 'EnvironmentName', 'KeyType': 'HASH'},
            {'AttributeName': 'Creator', 'KeyType': 'RANGE'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'Creator', 'AttributeType': 'S'},
            {'AttributeName': 'EnvironmentName', 'AttributeType': 'S'}
        ],
        'BillingMode': 'PAY_PER_REQUEST'
        }
        table = dyn_resource.create_table(**params)
        print(f"Creating {table_name}...")
        table.wait_until_exists()
        return table    
    except Exception as e:
        raise Exception((f"Error re-creating DynamoDB table {table_name}: {e}"))



def add_app_env(dynamodb_client, ec2_client, app_env, resources, dynamodb_table_name):
    firt_resource = resources[0]
    res_arn = firt_resource.get('ResourceARN')
    tags = firt_resource.get("Tags")
    creator = None
    for tag in tags:        
        if tag.get('Key') == TAG_KEY_CREATOR:
            creator = tag.get('Value')
            break
            
    if not creator:
        print(f"Found env without Creator: {app_env}")
        creator = TAG_VALUE_NO_CREATOR
            
    try:
        print(f"Fetching App env data from DynamoDB {app_env}")
        response = dynamodb_client.get_item(
                    TableName=dynamodb_table_name,
                    Key={
                        "EnvironmentName": {"S": app_env },
                        "Creator": {"S": creator }
                        }
                   )
        item = response["Item"]
        print(f"Got from DynamoDB: {item}")
        return False
    except KeyError:
        print(f"KeyError - Fetching App env from DynamoDB {app_env}")
        create_date_updated = False
        create_date = ""
        # add the app_env to table 
        response =  dynamodb_client.put_item(
                        TableName=dynamodb_table_name,
                        Item={
                        "EnvironmentName": {"S": app_env },
                        "Creator": {"S": creator },
                        "CreationDate": {"S": create_date},
                        }
                    )
        print(f"Put item to DynamoDB table: {app_env} ")
        
        for res in resources:
            res_arn = res.get('ResourceARN')
            identifier = res_arn.split("/")[-1]
            [env_name, tag_name, env_id, env_type, expiration, owner, product, version, launched_by] = [str(x*0) for x in range(9) ]
            tags = res.get("Tags")
            for tag in tags:
                if tag.get('Key') == TAG_KEY_ENV_NAME:
                    env_name = tag.get('Value', '') 
                else:
                    print(f"Unprocessed tag: {tag}")

            service = res_arn.split(":")[2]
            type_tmp =  res_arn.split(":")[5]
            service_type = type_tmp.split('/')[0]
            if service_type == 'LaunchTemplate' and (not create_date_updated):
                create_date = ec2.get_create_date(ec2_client, identifier)
                create_date_updated = True
            region = res_arn.split(":")[3]
            resource = "Resource" + "." + identifier
            response =  dynamodb_client.update_item(
                            TableName=dynamodb_table_name,
                            Key={
                                "EnvironmentName": {"S": app_env },
                                 "Creator": {"S": creator }
                            },
                            AttributeUpdates={
                                "CreationDate": {
                                    'Value': { 'S': str(create_date) }
                                },
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
            print(f"Updated resource {identifier} to DynamoDB ")
        return True
    except Exception as e:
        print(e)
        raise Exception(f"Fetching App env data from DynamoDB {env_name}")