import os
import pandas as pd
from io import BytesIO, StringIO
import json
import boto3
import tempfile
from botocore.exceptions import NoCredentialsError, ClientError
import logging
from pathlib import Path
import streamlit as st
import tempfile


class S3FileManager:
    def __init__(self):
        # Initialize AWS credentials and S3 client
        self.aws_access_key_id = st.secrets["AWS_ACCESS_KEY"]
        self.aws_secret_access_key = st.secrets["AWS_SECRET_KEY"]
        self.bucket_name = st.secrets["AWS_BUCKET_NAME"]
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )

     # Method to upload a PDF file to S3
    def upload_pdf(self, file_obj, s3_file_name):
        s3_file_name = str(Path(s3_file_name).as_posix())
        try:
            self.s3_client.upload_fileobj(
                file_obj, self.bucket_name, s3_file_name)
            logging.info("PDF Uploaded")
            logging.info(
                f"PDF file uploaded successfully to S3 bucket '{self.bucket_name}' with name '{s3_file_name}'")
            return True
        except NoCredentialsError:
            logging.error("AWS credentials not available or incorrect.")
            return False
        except Exception as e:
            logging.error(f"upload_pdf: An error occurred: {e}")
            return False

    def upload_file(self, file_obj, s3_path):
        try:
            self.s3_client.upload_fileobj(file_obj, self.bucket_name, s3_path)
            return True
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return False

    def read_file(self, s3_file_name):
        s3_file_name = str(Path(s3_file_name).as_posix())
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name, Key=s3_file_name)
            pdf = response['Body']
            # pdf = response['Body'].read().decode('utf-8')
            logging.info(f"Successfully read from file: '{s3_file_name}'")
            return pdf
        except NoCredentialsError:
            logging.error("AWS credentials not available or incorrect.")
            return None
        except Exception as e:
            logging.error(f"read_file: An error occurred: {e}")
            return None

    # method to download a file from S3 bucket
    def download_file(self, s3_file_name, download_file_path):
        s3_file_name = str(Path(s3_file_name).as_posix())
        download_file_path = str(Path(download_file_path).as_posix())

        logging.info(f"{self.bucket_name}/{s3_file_name}")
        self.s3_client.download_file(
            self.bucket_name, s3_file_name, download_file_path)
        return True

    def save_mmd_file(self, mmd_file_contents, mmd_s3_file_name):
        mmd_s3_file_name = str(Path(mmd_s3_file_name).as_posix())
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name, Key=mmd_s3_file_name, Body=mmd_file_contents.encode('utf-8'))
            logging.info(
                f"MMD file generated and uploaded to S3 bucket '{self.bucket_name}' with key '{mmd_s3_file_name}'")
            return True
        except Exception as e:
            logging.error(f"AWS: save_mmd_file: An error occurred: {e}")
            return False

    def download_file_in_temp(self, input_file):
        '''returns temp_directory'''

        # Create a temporary directory
        logging.info("Creating Temp File")
        temp_dir = tempfile.mkdtemp()
        # Write the contents of the uploaded file to a temporary PDF file
        pdf_name = os.path.basename(input_file)
        temp_pdf_path = os.path.join(temp_dir, pdf_name)
        self.download_file(input_file, temp_pdf_path)
        logging.info(f"Temp File Created : {temp_pdf_path}")
        return temp_dir

    def get_reports_list(self, email):
        print(email)
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=f"qu-aedt/test/reports/{email}/")
            if 'Contents' in response:
                reports = []
                for obj in response['Contents']:
                    reports.append(
                        (obj['Key'], obj['LastModified'], obj['Size']))
                return reports
            else:
                return []
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return []

    def delete_report(self, report_name, email):
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name, Key=report_name)
            return True
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return False
