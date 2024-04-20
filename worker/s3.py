from minio import Minio
import os
from minio.error import S3Error

# Replace these with your AWS credentials and S3 bucket and file information
aws_access_key_id = 'oJTJnZIz0lJ8RblZMLbb'
aws_secret_access_key = 'nyAeRaWm1vo9mBBwgKqhLzP1Yjws7V5IpVrfKPEe'
host = "144.91.123.186:32771"
secure = False

class S3:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.access_key = aws_access_key_id
        self.secret_key = aws_secret_access_key
        self.host = host
        self.secure = secure
        
        # Initialize Minio client
        self.client = Minio(
            self.host,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )

    def download_file(self, file_key, local_file_path):
        try:
            # Ensure the local directory exists
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            # Download object to local file
            self.client.fget_object(self.bucket_name, file_key, local_file_path)
            print(f"File downloaded successfully to {local_file_path}")
        except Exception as e:
            print(f"Error downloading file: {e}")

    def upload_file(self, local_file_path, file_key):
        try:
            # Upload local file to the bucket
            self.client.fput_object(self.bucket_name, file_key, local_file_path)
            print(f"File uploaded successfully to S3 key: {file_key}")
        except Exception as e:
            print(f"Error uploading file: {e}")

    def remove_file(self, file_key):
        try:
            # Remove object from the bucket
            self.client.remove_object(self.bucket_name, file_key)
            print(f"File '{file_key}' deleted from bucket '{self.bucket_name}'")
        except S3Error as e:
            print(f"An error occurred: {e}")

# Uncomment the following lines to use the download and upload functions
# download_file(file_key, local_file_path)
# upload_file(file_key, local_file_path)
