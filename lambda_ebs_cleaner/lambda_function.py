import json
import boto3
import botocore
from datetime import datetime, timedelta
import pytz

def lambda_handler(event, context):

    # Iterate over regions
    regions = boto3.client('ec2').describe_regions().get('Regions', [])

    for region in regions:
        print("* Checking region  --   %s " % region['RegionName'])
        reg = region['RegionName']

    # List and remove non-attached EBS volumes
        client_ebs = boto3.resource('ec2', region_name=reg)

        for volume in client_ebs.volumes.all():
            if volume.state == 'available':
                 print(f"{volume.id} / Size: {volume.size}GiB / Volume Type:{volume.volume_type}")
                 volume.delete()
                 print(f"{volume.id} deleted")

    # List and remove snapshots older than 30 days
        account_id = boto3.client('sts').get_caller_identity().get('Account')
        client_ebs_snapshot = boto3.client('ec2', region_name=reg)
        response_client_ebs_snapshot = client_ebs_snapshot.describe_snapshots(OwnerIds=[account_id])
        utc = pytz.UTC  ## Convert datetime from naive to aware
        #snapshot_date = utc.localize(datetime.now() - timedelta(days=30))

        try:
            for snapshot in response_client_ebs_snapshot['Snapshots']:
                if snapshot['StartTime'] < utc.localize(datetime.now() - timedelta(days=30)):
                    print(f"SnapshotId: {snapshot['SnapshotId']} / Creation date: {snapshot['StartTime'].strftime('%Y-%m-%d')}")
                    client_ebs_snapshot.delete_snapshot(SnapshotId=snapshot['SnapshotId'])
                    print(f"{snapshot['SnapshotId']} deleted")
        except botocore.exceptions.ClientError as error:
            pass ## Snapshots attached to AMIs will fail, so pass

