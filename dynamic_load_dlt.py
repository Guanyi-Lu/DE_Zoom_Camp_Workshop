## this is extra homework to download files to bcp buckets then read it to  big query studio dataset_name="taxi_data",
#this script is more dynamic than the dlt_gcp.py since this script enable users to input color/year/month
#dlt hub handles data extract normalize and load

import json
import os
import toml
import requests
import dlt
from dlt.sources.filesystem import filesystem, read_parquet
from google.cloud import storage

# Load the TOML file
# the TOML file should follow below format:
#[credentials]
#project_id = "your project id"
#private_key = "your sevice account key"
#client_email = "email"
config = toml.load("secrets.toml")

# Set environment variables
os.environ["CREDENTIALS__PROJECT_ID"] = config["credentials"]["project_id"]
os.environ["CREDENTIALS__PRIVATE_KEY"] = config["credentials"]["private_key"]
os.environ["CREDENTIALS__CLIENT_EMAIL"] = config["credentials"]["client_email"]

# Initialize GCS client
storage_client = storage.Client.from_service_account_json("google_credentials.json")
bucket_name = "homework_4_bucket"  # Replace with your GCS bucket name
subfolder = "green_2019_2020/"
bucket = storage_client.bucket(bucket_name)

# Function to generate URLs based on user input for the date range and trip color
def generate_urls(color, start_year, end_year, start_month, end_month):
    base_url = "https://d37ci6vzurychx.cloudfront.net/trip-data/"
    urls = []

# Generate the list of URLs based on the specified date range and color

    for year in range(start_year, end_year + 1):
        for month in range(start_month, end_month + 1):
            # Format the month to ensure two digits
            month_str = f"{month:02d}"
            url = f"{base_url}{color}_tripdata_{year}-{month_str}.parquet"
            #https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2020-01.parquet
            urls.append(url)

    return urls

# User input for time range and trip color
color = input("Enter color (green, yellow): ").lower()  
start_year = int(input("Enter the start year (e.g., 2019): "))
end_year = int(input("Enter the end year (e.g., 2022): "))
start_month = int(input("Enter the start month (1-12): "))
end_month = int(input("Enter the end month (1-12): "))

# Generate URLs based on user input
urls = generate_urls(color, start_year, end_year, start_month, end_month)


# Debug: Print generated URLs
print("Generated URLs:")
for url in urls:
    print(url)

# Download files and upload them to GCS
gcs_files = []
#for url in urls:
    #file_name = url.split("/")[-1]  # Extract the file name from the URL
    #gcs_blob = bucket.blob(file_name)

    #print(f"Downloading {url} and uploading to GCS as {file_name}")
    #response = requests.get(url)
    #gcs_blob.upload_from_string(response.content)
    #gcs_files.append(f"gs://{bucket_name}/{file_name}")


for url in urls:
    file_name = url.split("/")[-1]  # Extract the filename from the URL
    gcs_blob = bucket.blob(f"{subfolder}{file_name}")  # Include the subfolder

    print(f"Downloading {url} and uploading to GCS as {subfolder}{file_name}")
    response = requests.get(url)
    gcs_blob.upload_from_string(response.content)
    gcs_files.append(f"gs://{bucket_name}/{file_name}")

@dlt.resource(name="rides", write_disposition="replace")
def parquet_source():
    #Use filesystem to load files from GCS and apply read_parquet transformation
    files = filesystem(bucket_url="gs://dlt_bucket_test/", file_glob="*.parquet")
    reader = (files | read_parquet()).with_name("tripdata")

    # Iterate through the rows from the reader and yield them
    row_count = 0
    for row in reader:
        row_count += 1
        if row_count <= 5:  # debugging
            print(f"Yielding row: {row}")
        yield row
    print(f"Total rows yielded: {row_count}")

#Create the pipeline
pipeline = dlt.pipeline(
    pipeline_name="test_taxi",
    dataset_name="taxi_data",
    destination="bigquery"
)

# Run the pipeline
info = pipeline.run(parquet_source())
print(info)
