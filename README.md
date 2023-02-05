
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
If the command fails, you might have to change the version in `docker-compose.yml` according to the error message.
 
 3. Run the activate.sh script to setup the virtual env for python and install the dependencies.

    `./activate.sh`

 4. Run the start.sh script which activates the venv and starts the python script in the background.  
    `./start.sh`  
		Errors, if any, would appear in the `nohup.out` file.  
		To view the application logs:
    `tail -200f fetch-etl-server.log`
    
    To stop the python script:
    `./stop.sh`  
   
 5. As an alternate to steps 3 and 4, you can run the script directly:
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
 In the logfile `fetch-etl-server.log`, the message `Waiting for new message..` will be seen, which means there are no new messages left to be processed in the SQS queue.
 
 7. Run `docker-compose down` to shutdown the docker containers.
 
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


# Questions
1. *How would you deploy this application in production?*  
  
After making the changes mentioned in Next Steps, the app may be deployed into production. One of the ways to do so is to create (`docker build`) and publish the Docker image to a registry. A docker-compose file may then be deployed to the production environment which contains the image, ports, host details for the script, along with any other services which are to be deployed in the production server. `docker-compose up` may then be used to bring up the docker container(s).  

Another way is to use Kubernetes for deploying the docker image. The containers deployed can then be monitored and scaled up/down as needed, based on the volume of messages in the SQS queue. 
 
The process of deployment itself can be automated by using a CI/CD pipeline such as Jenkins.  
___
2. *What other components would you want to add to make this production ready?*  
  
  To make this ETL script production ready, the changes mentioned in the "Next Steps" section need to be implemented. Furthermore, the following components can be added:
  1. The polling frequency for new messages on SQS queue may be made more intelligent. This can be achieved with a combination of the following:    
      - Long Polling: By enabling long polling, the number of empty responses are reduced when there are no messages available to return in reply to a ReceiveMessage request sent to an Amazon SQS queue and eliminating false empty responses.  
      - Batch Processing: Poll for multiple messages at a time, instead of polling for one message at a time. This can be useful to save resources when the information is not immediately required by the downstream. The python script itself may be run as a batch process once every hour/day. This change depends on the feature requirement and the volume of messages in the incoming queue.  
  2. Creating a dead-letter queue  
       - In the current implementation, the messages that do not have a valid format are discared and lost. Some invalid messages may be relevant but may have improper format due to human error or a bug in the upsteam services. Depending on the importance of the messages, a dead-letter SQS queue can be created. The invalid messages will then be published to the dead-letter queue by the ETL script and can be consumed by the upstream again for re-processing or can be looked at manually for identifying the root cause of the invalid message.  
___
3. *How can this application scale with a growing dataset?*

SQS is a messaging queue where each message is received exactly once by its consumers. Hence, if multiple instances of the python script are deployed and are consuming from the same queue, they will essentially increase the message consumption throughput linearly. Source: [AWS Docs](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-throughput-horizontal-scaling-and-batching.html)
Hence, to scale the application with a growing dataset, the number of consumers and producers on the SQS queue can be increased, by using container orchestration tools such as Kubernetes as mentioned in Question 1.   
However, the database writes can become a bottleneck soon. This can be mitigated by writing to databases in batches instead of writing once for every message.

___
4. *How can PII be recovered later on?*

If masking is made in such a way that the downstream can be programatically recover the original data, then it is a bad masking mechanism. The masking technique used in the script is hashlib encryption, which is a one-way hash. In case it is absolutely necessary to recover the PII from the masked PII, one way is to store the mapping between the original value and the generated hashvalue in a database table. This table would have limited SELECT (view) permissions to specific profiles on a need-to-have basis.  
For ease of access, a REST API server can be setup with SSL certificate protected APIs to get the PII from the mapping table for the input masked PII.

___
5. *What are the assumptions made?*

- I have assumed that the following fields from the message are required/mandatory (cannot be null or absent from the message):
```
required_keys = ["user_id", "app_version", "device_type", "ip", "locale", "device_id"] 
```
- Only the field `locale` can hold null values.
- The appversion components range from 0-99.
- The invalid messages can be deleted from the queue and ignored by the application (after logging).
