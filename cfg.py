import os
from dotenv import load_dotenv

load_dotenv()


s3cfg = {
    'access_key': os.getenv('access_key'),
    'secret_key': os.getenv('secret_key'),
    'endpoint_url': os.getenv('endpoint_url'),
    'bucket_name': os.getenv('bucket_name'),
}

db = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_DATABASE'),
}

googleAuth = {
    'CLIENT_ID': os.getenv('CLIENT_ID'),
    'CLIENT_SECRET': os.getenv('CLIENT_SECRET'),
    'REDIRECT_URI': os.getenv('REDIRECT_URI')
}
