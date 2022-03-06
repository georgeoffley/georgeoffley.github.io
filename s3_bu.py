"""
Script for backing up posts to S3

Requires:
- Boto3
- python-dotenv
"""

import boto3
import os

from dotenv import load_dotenv


# Setup
load_dotenv()
ACCESS_KEY = os.getenv('ACCESS_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')

CLIENT = boto3.client('s3',
    aws_access_key_id = ACCESS_KEY,
    aws_secret_access_key = SECRET_KEY
)

#def grabLatestDate():
#object = boto3.client('s3').head_object(Bucket = 'blogpostbu', Key = '.pdf')['LastModified']

#print(object)


# TODO: Figure out how .list_objects orders objects and figure out how to get last uploaded item
#       Also figure out how we can just get the metadata using .head_object
#       See how .head_object works and how you can pass in wildcards and how it orders the returns
response = CLIENT.list_objects(
    Bucket = 'blogpostbu'
)

print(response)

