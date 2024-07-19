# Import the required libraries
import boto3
import json
import streamlit as st
import os
from pathlib import Path
from src.common.logger import Logger

# Create the logger object
logger = Logger.get_logger()

def get_updated_config_list():
    bucket = 'qucoursify'
    prefix = "qu-examine"

    
    # Get the AWS credentials and the bucket name
    AWS_ACCESS_KEY = st.secrets["AWS_ACCESS_KEY"]
    AWS_SECRET_KEY = st.secrets["AWS_SECRET_KEY"]

    # Create the s3 client
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)

    # Get the json file from the S3 bucket
    response = s3.get_object(Bucket=bucket, Key=prefix+"/config_list.json")
    json_data = json.loads(response['Body'].read().decode('utf-8'))

    with open("data/config_list.json", "w") as f:
        json.dump(json_data, f)
    
    return json_data

def load_files_from_s3(prefix, local_file_path):
    """
    Functionality to download the files from the S3 bucket.

    Args:
    prefix: str: The prefix of the files to be downloaded
    local_file_path: str: The path where the files are to be downloaded
    """
    logger.info(f"Pulling resources for {prefix}")
    # Get the AWS credentials and the bucket name
    AWS_ACCESS_KEY = st.secrets["AWS_ACCESS_KEY"]
    AWS_SECRET_KEY = st.secrets["AWS_SECRET_KEY"]
    BUCKET_NAME = st.session_state.config_param["S3_BUCKET_NAME"]
    
    # Open the last_updated.json file to get the last updated time of the files
    last_updated = json.load(open("data/last_updated.json", "r"))
    
    # Open the local path where the files are to be downloaded
    local_file_path = "data/"+local_file_path
    Path(local_file_path).mkdir(parents=True, exist_ok=True)

    # Create the s3 client
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
    prefix_len = len(prefix)

    # If it is a directory, create the directory 
    for obj in s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)['Contents']:
        if obj['Key'].endswith('/'):
            Path(local_file_path+obj['Key'][prefix_len:]).mkdir(parents=True, exist_ok=True)

    # Else download the file
    for obj in s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=prefix)['Contents']:
        if "test/video" in obj['Key'] or "test/transcript" in obj['Key']:
            continue
        if not obj['Key'].endswith('/'):
            # If the file does not exist, download the file
            Path(local_file_path+obj['Key'][prefix_len:obj['Key'].rindex('/')+1]).mkdir(parents=True, exist_ok=True)
            if obj['Key'] not in last_updated:
                s3.download_file(BUCKET_NAME, obj['Key'], local_file_path+obj['Key'][prefix_len:])
                last_updated[obj['Key']] = obj['LastModified'].strftime("%Y-%m-%d %H:%M:%S")
            # If the file is not the latest one, download the file
            elif last_updated[obj['Key']]!=obj['LastModified'].strftime("%Y-%m-%d %H:%M:%S"):
                os.remove(local_file_path+obj['Key'][prefix_len:])
                s3.download_file(BUCKET_NAME, obj['Key'], local_file_path+obj['Key'][prefix_len:])
                last_updated[obj['Key']] = obj['LastModified'].strftime("%Y-%m-%d %H:%M:%S")


    # Save the last updated time of the files
    json.dump(last_updated, open("data/last_updated.json", 'w'))

            