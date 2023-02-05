import boto3
import hashlib
import json
import psycopg2
import time
import logging
from datetime import datetime

sqs_client = boto3.client("sqs", endpoint_url="http://localhost:4566", region_name= 'us-east-1', aws_access_key_id='test', aws_secret_access_key='test')


queue_url = "http://localhost:4566/000000000000/login-queue"

# Connect to the AWS SQS queue and retrieve messages
def retrieve_sqs_messages():
    messages = sqs_client.receive_message(QueueUrl=queue_url)
    if "Messages" in messages:
        return messages['Messages']
    else:
        return []


# Returns a boolean value based on whether the message is valid or not
def validate_message(data):
    required_keys = ["user_id", "app_version", "device_type", "ip", "locale", "device_id"] #keys that are required in message
    null_keys = ["locale"]  #keys that can be null
    for key in required_keys:
        if key not in data:
            logging.info("Invalid message: %s \nMandatory field: %s does not exist", data, key)
            return False
        if key not in null_keys and data[key] == None:
            logging.info("Invalid message: %s \nField: %s is null", data, key)
            return False
    return True
    

# Mask the PII data (device_id and ip)
def mask_pii_data(data):
    # Hash the device_id and ip fields
    hashed_device_id = hashlib.sha256(data["device_id"].encode()).hexdigest()
    hashed_ip = hashlib.sha256(data["ip"].encode()).hexdigest()

    # Replace the original values with the hashed values
    data["device_id"] = hashed_device_id
    data["ip"] = hashed_ip

    return data

# Convert appversion to int for storing in the table
def get_int_appversion(appversion):
    return int(appversion.split('.')[0])

# Write the data to the PostgreSQL database
def write_to_postgres(data, receipt_handle):
    
    insert_statement = "INSERT INTO user_logins (user_id, device_type, masked_ip, masked_device_id, locale, app_version, create_date) VALUES (%s, %s, %s, %s, %s, %s, %s)"
    values = (data["user_id"], data["device_type"], data["ip"], data["device_id"], data["locale"], get_int_appversion(data["app_version"]), datetime.now().date())
    try: 
        conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="postgres"
        )
        cursor = conn.cursor()
        logging.info("Inserting data into user_logins for user_id: %s", data["user_id"])
        cursor.execute(insert_statement, values)
        conn.commit()
        delete_from_sqs(receipt_handle)
    except (Exception, psycopg2.Error) as error:
        logging.error("Error occurred while inserting to user_logins table: %s", error)
    finally:
        cursor.close()
        conn.close()
        

# Delete message from SQS 
def delete_from_sqs(receipt_handle):
    sqs_client.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )

def run_etl_process():
    sleep_time = 0
    while True:
        # Retrieve messages from the AWS SQS queue
        messages = retrieve_sqs_messages()
        
        #add a wait time if no messages received
        if messages == []:
            sleep_time = 5
        else:
            sleep_time = 0
            
        # Loop over the messages and perform the ETL process
        for message in messages:
            print(message)
            receipt_handle = message['ReceiptHandle']
            data = json.loads(message['Body'])
            if validate_message(data):
                # Mask the PII data
                masked_data = mask_pii_data(data)
                # Log the data after masking
                logging.info("Received message from SQS: %s", masked_data)
                # Write the data to the PostgreSQL database and delete message from SQS on successful processing
                write_to_postgres(masked_data, receipt_handle)
            else:
                delete_from_sqs(receipt_handle) # Delete the invalid message from SQS
        
        # Wait for a short period of time before checking for new messages
        if sleep_time > 0:
            logging.info("Waiting for new message..")
            time.sleep(sleep_time)

if __name__ == "__main__":
    #initialize logging
    logging.basicConfig(level=logging.INFO, filename="fetch-etl-server.log", filemode="a+",
                format="%(asctime)-15s %(levelname)-8s %(message)s")
    run_etl_process()
    