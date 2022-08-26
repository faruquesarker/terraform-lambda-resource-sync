def get_create_date(ec2_client, launch_template_id):
    # Get the creation date based on the LaunchTemplate creation time
    try:
        resp = ec2_client.describe_launch_template_versions(LaunchTemplateId=launch_template_id)
        laucn_template_data = resp["LaunchTemplateVersions"][0]
        return str(laucn_template_data["CreateTime"])
    except Exception as e:
        raise Exception(f"Unexpected error in fetching  LaunchTemplate info from EC2: {e}")