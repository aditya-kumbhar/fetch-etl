
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
