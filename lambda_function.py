from __future__ import print_function
import json
import boto3
print("Loading function")

snsclient = boto3.client('sns')

def lambda_handler(event, context):
    for record in event['Records']:
        print(record)
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        print("=======" + bucket)
        print("=======" + key)
        # snsclient.publish(PhoneNumber='+12067477252', Message=bucket+ ' '+key, Subject='Css490')
        snsclient.publish(TopicArn='arn:aws:sns:us-west-2:437777420713:css490storage_upload_topic', Message=bucket+ '/'+key, Subject='Css490')
    # TODO implement
    
    return 'Hello from Lambda'

