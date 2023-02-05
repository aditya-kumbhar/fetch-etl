
# fetch-etl
A python script that consumes messages from a localstack SQS queue, performs data masking on PII and loads the messages into Postgres.

# Requirements

 - Python 3
 - pip
 - Docker Compose
 - Bash shell
 - postgresql-client

# Running the ETL Python Script

 1. Checkout the project and **cd to the project directory** in a bash shell (MacOS/Linux: terminal; Windows: git bash)
 
 2. Start the postgres and localstack containers:  
 `docker-compose up`
If the command fails, you may have to change the version in `docker-compose.yml` according to the error message.
 
 3. Run the activate.sh script to setup the virtual env for python and install the dependencies.

    `./activate.sh`

 4. Run the start.sh script which activates the venv and starts the python script in the background.  
    `./start.sh`  
		Errors, if any, would appear in the `nohup.out` file.  
		To view the application logs:
    `tail -200f fetch-etl-server.log`
    
    To stop the python script:
    `./stop.sh`  
   
 5. Alternatively, you can run the script directly:
   ```
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python3 fetch-etl-server.py
   ```
   The logs can be viewed in `fetch-etl-server.log`
   
 6. Upon successful execution, the messages from localstack SQS queue `login-queue` will be consumed one-by-one, the PII fields will be masked and the message would be stored in the `user_logins` table in Postgres, after which the message will be deleted from the queue.  
 Check the contents of the table:
 ```
 psql -d postgres -U postgres -p 5432 -h localhost -W
 #password: postgres
 select * from user_logins;
 select count(*) from user_logins;
 ```
 
 # Next Steps
 
 1. Currently, the aws_access_key_id, aws_secret_access_key, region_name are hardcoded in the python script:
 ```
 sqs_client = boto3.client("sqs", endpoint_url="http://localhost:4566", region_name= 'us-east-1', aws_access_key_id='test', aws_secret_access_key='test')
 ```
When connecting to an actual AWS SQS queue, the hardcoded values should not be left in the code. Instead, the `profile_name` argument can be used when creating the boto3 client. The profile is the one that is set in the AWS CLI configuration file: `~/.aws/config`
`sqs_client = boto3.client("sqs", profile_name='my_profile')`  
Alternatively, environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_DEFAULT_REGION` may be set in the environment where the script is being deployed to. These values will be used by default if not specified while creating the boto3 client:
```
sqs_client = boto3.client("sqs")
```

The queue_url can also be fetched from an environment variable as it may differ for every environent (DEV/UAT/PROD).

2. Similarly, the PostgreSQL hostname, username, password, should be stored in environment variables and then referenced in the code.
```
import configparser

config = configparser.ConfigParser()
config.read('db-config.ini')

PG_USERNAME = config['postgres']['username']
PG_HOST = config['postgres']['host']
PG_PASSWORD = config['postgres']['password']

# Use these configuration variables to connect to the database
conn = psycopg2.connect(
    host=PG_HOST,
    user=PG_USERNAME,
    password=PG_PASSWORD,
    database="mydatabase"
)

```

3. To be able to scale or deploy into container orchestration tools, a Dockerfile may be included to build an image for the script:
```
FROM python:3.7

WORKDIR /app
COPY . .
RUN ./activate.sh
RUN ./start.sh
```


