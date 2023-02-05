
# fetch-etl
A python script that consumes messages from a localstack SQS queue, performs data masking on PII and loads the messages into Postgres.

# Requirements

 - Python 3
 - Pip
 - Docker Compose
 - Bash shell

# Running the ETL Python Script

 1. Checkout the project and **cd to the project directory** in a bash shell (MacOS/Linux: terminal; Windows: git bash)
 2. Make the .sh files executable
 
    `chmod +x *.sh`
 
 3. Start the postgres and localstack containers:  
 `docker-compose up`
 
 4. Run the activate.sh script to setup the virtual env for python and install the dependencies.

    `./activate.sh`

 5. Run the start.sh script which activates the venv and starts the python script in the background.  
    `./start.sh`  
		Errors, if any, would appear in the `nohup.out` file.  
		To view the application logs:
    `tail -200f fetch-etl-server.log`
    
    To stop the python script:
    `./stop.sh`  
   
 6. Alternatively, you can run the script directly:
   ```
   source venv/bin/activate
   python3 fetch-etl-server.py
   ```
   The logs can be viewed in `fetch-etl-server.log`
   
 7. Upon successful execution, the messages from localstack SQS queue `login-queue` will be consumed one-by-one, the PII fields will be masked and the message would be stored in the `user_logins` table in Postgres, after which the message will be deleted from the queue.  
 Check the contents of the table:
 ```
 psql -d postgres -U postgres -p 5432 -h localhost -W
 select * from user_logins;
 select count(*) from user_logins;
 ```
