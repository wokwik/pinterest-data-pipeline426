# pinterest-data-pipeline426
  
# Description
This project is about replicating a data processing pipeline similar to ones used at Pinterest for processing the post requests generated when a user uploads data (content) to the Pinterest Platform. It demonistrates using two types of processing:
- Batch processing using Kafka from AWS MSK
- Stream processing using AWS Kinesis

The post requests consists of three related events: pinterest_data, geolocation_data, and user_data. Due to the sheer volume we expect Pinterest is expected to process per unit of time, the infrastructure is expected to handle large volumes, exhibit high robustiness, and be scalabile to meet demand in real time.

AWS cloud is chosen to implement this project as it is well known for providing highly available, highly scalable, and always available infrastructure that is able to meet the toughest of demand. Also AWS service inlcudes robust and very capable services for this type of project namely MSK, EC2, S3, API Gateway, and Kinesis. 

AWS MSK is fully managed Apache Kafka service to process data, which significantly reduces the effort and time required to setup and manange Apache Kafka in production environments. Apache Kafka is an open-source technology for distributed data storage that is designed to be optimised for ingesting and processing streaming data in real-time. We will create Kafka custom Plugins using Confluent.io for connecting to S3, Add Kafka plugins for using AWS IAM roles to communicate with an S3 bucket instance, and create a Kafka Connector for sending data to the S3 bucket.

AWS EC2 is cloud hosted server that can be created within the MSK Cluster and configured bespoke as powerful as required processing, RAM, and storage specifications. EC2 will act as an Apache Kafka client and used for creating topics in the MSK cluster.

AWS Kinesis can collect streaming data such as event logs, social media feeds, application data, and IoT sensor data in real time or near real-time. Kinesis enables you to process and analyze this data as soon as it arrives, allowing you to respond instantly and gain timely analytics insights.
    A Kinesis Data Stream is a set of Shards. A shard contains:
    - a sequence of *Data Records*, which in turn are composed of:
    - a *Sequence Number*
    - a *Partition Key*
    - a *Data Blob* (which is an immutable sequence of bytes)

Databricks is a powerful solution for managing data at scale, offering a comprehensive environment that goes beyond data storage. It encompasses a wide range of tasks and capabilities, including efficient data ingestion, storage, ETL operations, and unified analytics supporting multiple programming languages. Users can seamlessly perform diverse activities, from building end-to-end machine learning pipelines to real-time streaming analytics, within this holistic platform.

Databricks is built upon *Apache Spark*, a powerful open-source distributed computing system that enables parallel processing of large datasets.

# Architecture Diagram

This diagram summarises the architecture:

![Alt text](CloudPinterestPipeline%20-%20architecture%20diagram.png?raw=true "Architecture Diagram - Pinterest Lambda Architecture")

# Installation instruction

## Create a Batch Processing Pipeline
- Create MSK Kafka Cluster
    Login to AWS console and use the UI for creating the AWS MSK Cluster.
    Give the MSK cluster a name like so <chosen_prefix>-msk-cluster
    Decide best configuration for your usecase. But, mainly you will need to provision two key elements the broker instances and broker storage.

- Create S3 Bucket
    Use AWS Console for creating an S3 bucket, give the bucket a name like so <chosen_prefix>-bucket

    In the steps create a new Policy with name like <chosen_prefix>-policy and from the IAM permission tab configure it with these permissions:
    ```
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": [
                    "s3:ListBucket",
                    "s3:DeleteObject",
                    "s3:GetBucketLocation"
                ],
                "Resource": [
                    "arn:aws:s3:::<DESTINATION_BUCKET>",
                    "arn:aws:s3:::<DESTINATION_BUCKET>/*"
                ]
            },
            {
                "Sid": "VisualEditor1",
                "Effect": "Allow",
                "Action": [
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:ListBucketMultipartUploads",
                    "s3:AbortMultipartUpload",
                    "s3:ListMultipartUploadParts"
                ],
                "Resource": "*"
            },
            {
                "Sid": "VisualEditor2",
                "Effect": "Allow",
                "Action": "s3:ListAllMyBuckets",
                "Resource": "*"
            }
        ]
    }
    ```

    Once the IAM role is created, you can add the following JSON code In the Trusted entities tab under the Trust Relationships IAM role tab:
    ```
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "kafkaconnect.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    ```

- Create IAM Roles and policies
    Use AWS Console for creating the required IAM role and assign policies to allow interacting with MSK, EC2, and S3 buckets.

- Create and Configure the EC2 Kafka Client
    - Create the EC2 Instance using AWS Console
    - Assign IAM role policy to access and manage the EC2 instance
    - Allocate the key pair associated with the EC2 instance and save locally
    - Use key pair for connecting to EC2 using SSH Client from your local machine:
        Save the .pem file in your working directory Where you are working from within your local terminal/cmd and run the following cmd line once to make the .pem private outside your SSH session:
        ```
        chmod <pem-file-name>.pem 
        ```
        Then you can use this command to connect to EC2:
        ```
        ssh -i <pem-file-name>.pem ec2-user@<EC2-connection-string>.amazonaws.com
        ```

    - Install Kafka on EC2 instance:
        Firstly you need to install Java-1.8.0 using this command:
        ```
        sudo yum install java-1.8.0
        ```

        Secondly you want to install Kafka using these commands:
        ```
        wget https://archive.apache.org/dist/kafka/2.8.1/kafka_2.12-2.8.1.tgz
        tar -xzf kafka_2.12-2.8.1.tgz
        ```

        Thirdly you want to install a plugin to enable EC2 Kafka client to authenticate and authorise on the MSK cluster:
        browse to libs directory within the Kafka installation folder using:
        ```
        cd ~/kafka_2.12-2.8.1/libs/
        ```
        install AWS MSK IAM AUTH package using:
        ```
        wget https://github.com/aws/aws-msk-iam-auth/releases/download/v1.1.5/aws-msk-iam-auth-1.1.5-all.jar
        ```

        Forthly make the AWS MSK IAM AUTH package available on the environment path by adding to the .bashrc file, using these commands:
        ```
        nano ~/.bashrc
        ```
        add the following line in the .bashrc file and save
        ```
        export CLASSPATH=/home/ec2-user/kafka_2.12-2.8.1/libs/aws-msk-iam-auth-1.1.5-all.jar
        ```
        Remeber to end SSH session and start again to see the above .bahsrc change taking effect for your session.

        Finally configure Kafka client to use AWS IAM
        Navigate to Kafka installation folder bin directory
        ```
        cd ~/kafka_2.12-2.8.1/bin/
        ```
        and create a client.properties file using this command:
        ```
        nano client.properties
        ```

        add the following content:

        ```
        # Sets up TLS for encryption and SASL for authN.
        security.protocol = SASL_SSL

        # Identifies the SASL mechanism to use.
        sasl.mechanism = AWS_MSK_IAM

        # Binds SASL client implementation.
        sasl.jaas.config = software.amazon.msk.auth.iam.IAMLoginModule required awsRoleArn="<add your Your Access Role>";

        # Encapsulates constructing a SigV4 signature based on extracted credentials.
        # The SASL client bound by "sasl.jaas.config" invokes this class.
        sasl.client.callback.handler.class = software.amazon.msk.auth.iam.IAMClientCallbackHandler
        ```

    - Create Kafka Topics on the Kafka Client EC2
        Optain the BootstrapServerString from the MSK Cluster console main page => View client information

        You can now create topics on the Kafka Client EC2 instance using this command, while in the ~/kafka_2.12-2.8.1/bin/ folder:
        ```
        ./kafka-topics.sh --bootstrap-server <BootstrapServerString> --command-config client.properties --create --topic <topic_name>
        ```

        Create 3 topics for each of the event types
        **<chosen_prefix>.pin** for the Pinterest posts data
        **<chosen_prefix>.geo** for the post geolocation data
        **<chosen_prefix>.user** for the post user data

- Create a Custom Plugin with MSK Connect
    Connect to your EC2 Client instance using SSH client and run the following commands:
    ```
    # assume admin user privileges
    sudo -u ec2-user -i
    # create directory where we will save our connector 
    mkdir kafka-connect-s3 && cd kafka-connect-s3
    # download connector from Confluent
    wget https://d2p6pa21dvn84.cloudfront.net/api/plugins/confluentinc/kafka-connect-s3/versions/10.0.3/confluentinc-kafka-connect-s3-10.0.3.zip
    # copy connector to our S3 bucket
    aws s3 cp ./confluentinc-kafka-connect-s3-10.0.3.zip s3://<BUCKET_NAME>/kafka-connect-s3/
    ```
    Which should add the object in your S3 Bucket: /kafka-connect-s3/confluentinc-kafka-connect-s3-10.0.3.zip

    Navigate to MSK Console, and select MSK Connect => Customised plugins, then create a custom plugin. Choose the Confluent connector ZIP file you uploaded above in your S3 bucket. Give the plugin a name like so __<chosen_prefix>-plugin__

- Create a Connector with MSK Connect
    Navigate to MSK Connect => Connectors, and click to create new Connector.
    
    Give your connector a name like __<chosen_prefix>-connector__
    
    In the connector configuration settings add the following configuration code:
    ```
    connector.class=io.confluent.connect.s3.S3SinkConnector
    # same region as our bucket and cluster
    s3.region=us-east-1
    flush.size=1
    schema.compatibility=NONE
    tasks.max=3
    # include nomeclature of topic name, given here as an example will read all data from topic names starting with msk.topic....
    topics.regex=<chosen_prefix>.*
    format.class=io.confluent.connect.s3.format.json.JsonFormat
    partitioner.class=io.confluent.connect.storage.partitioner.DefaultPartitioner
    value.converter.schemas.enable=false
    value.converter=org.apache.kafka.connect.json.JsonConverter
    storage.class=io.confluent.connect.s3.storage.S3Storage
    key.converter=org.apache.kafka.connect.storage.StringConverter
    s3.bucket.name=<BUCKET_NAME>
    ```
    Leave the rest of the configurations as default, except for:
    __Connector type__ change to Provisioned and make sure both the MCU count per worker and Number of workers are set to 1
    __Worker Configuration__, select Use a custom configuration, then pick confluent-worker
    __Access permissions__, where you should select the IAM role you have created previously
    Skip the rest of the pages until you get to Create connector button page. Once your connector is up and running you will be able to visualise it in the Connectors tab in the MSK console.

- Configure an proxy API in AWS API Gateway
    - Create an new API in AWS API Gateway, give it the name <chosen_prefix>-api
    - Create a new resource with Resource path equals to / and Resource name equal to {proxy+}
    - Edit integration, an select HTTP, and for HTTP method select ANY. It is important to edit that the Endpoint URL so that it captures
        - EC2 Instance Public DNS, plus
        - port and proxy resource type
        combined together like this: http://KafkaClientEC2InstancePublicDNS:8082/{proxy}
    - Install Confluent package for REST proxy on EC2
        - SSH login to EC2
        - Run the following commands
            - sudo wget https://packages.confluent.io/archive/7.2/confluent-7.2.0.tar.gz
            - tar -xvzf confluent-7.2.0.tar.gz
        - Configure the REST proxy to communicate with the MSK cluster and perform IAM authentication, run the following commands:
            - cd confluent-7.2.0/etc/kafka-rest
            - nano kafka-rest.properties
        - Modify the Boostrap server string and Plaintext Apache Zookeeper connection string respectively in your kfka-rest.properties file to capture the MSK cluster Bootstap server string and Apache Zookeepr connection string
        ```
        #schema.registry.url=http://localhost:8081
        zookeeper.connect=<Apache Zookeeper connetion (Plaintext)>
        #localhost:2181
        bootstrap.servers=<MSK Private Endpoint (single-VPC)>
        #PLAINTEXT://localhost:9092
        ```
        - Add the following configurations at the bottom of the file, and replace <Your Access Role> with the role name from first steps:
        ```
        # Sets up TLS for encryption and SASL for authN.
        client.security.protocol = SASL_SSL

        # Identifies the SASL mechanism to use.
        client.sasl.mechanism = AWS_MSK_IAM

        # Binds SASL client implementation.
        client.sasl.jaas.config = software.amazon.msk.auth.iam.IAMLoginModule required awsRoleArn="<Your Access Role>";

        # Encapsulates constructing a SigV4 signature based on extracted credentials.
        # The SASL client bound by "sasl.jaas.config" invokes this class.
        client.sasl.client.callback.handler.class = software.amazon.msk.auth.iam.IAMClientCallbackHandler
        ```
    - go back to AWS and deploy the <chosen_prefix>-api API in AWS Console, and note down the environment name <env>, you have chosen 
        - Note down the Invoke URL. The url should look like this:
        'https://<invoke-url-sub-domain>.amazonaws.com/<env>/topics/<chosen_prefix>.pin'

    - To send messages to the API Gateway, you need to start the REST proxy, by running the following command, like so:
        - cd confluent-7.2.0/bin
        - ./kafka-rest-start /home/ec2-user/confluent-7.2.0/etc/kafka-rest/kafka-rest.properties

    - The python code to send events to the proxy server are:
        ```
        headers = {'Content-Type': 'application/vnd.kafka.json.v2+json'}
        invoke_url = 'https://<invoke-url-sub-domain>.amazonaws.com/<env>/topics/<chosen_prefix>.pin'
        payload = json.dumps({
                            "records": [
                                {
                                #Data should be send as pairs of column_name:value, with different columns separated by commas       
                                "value": pin_result
                                }
                            ]
                        }, default=str)
        print(payload)
        response = requests.post(invoke_url, headers=headers, data=payload)
        print(response.json)
        ```
    - Running the above code for the first time, should result into seeig those Kafka Topics appearing in the S3 bucket, like so:
    topics/<chosen_prefix>.pin/partition=0/

    - __user_posting_emulation.py__ contains code for sending this projects Pinterest like data to Kafka

- Setting Up Databricks to Read Kafka Topics from S3:
    - Set you a new Databricks account, if you don't have one
    - Configure Databricks to store the S3 access_key and secret_key credentials
        - Download S3 credentials.csv file from AWS console
        - In the Databricks UI, click the Catalog icon and then click + Add --> Add data button.
        - Click on Create or modify table and then drop the credentials file you have just downloaded from AWS. Once the file has been successfully uploaded, click Create table to finalize the process.
        - The S3 credentials will be uploaded and available to access in the following location: *dbfs:/user/hive/warehouse/*
        ```
        # Read the Delta table to a Spark DataFrame
        aws_keys_df = spark.read.format("delta").load("dbfs:/user/hive/warehouse/authentication_credentials")
        # Get the AWS access key and secret key from the spark dataframe
        ACCESS_KEY = aws_keys_df.select('Access key ID').collect()[0]['Access key ID']
        SECRET_KEY = aws_keys_df.select('Secret access key').collect()[0]['Secret access key']
        # Encode the secret key
        ENCODED_SECRET_KEY = urllib.parse.quote(string=SECRET_KEY, safe="")
        ```
    - You can then mount the S3 bucket using this code:
    ```
    # AWS S3 bucket name
    AWS_S3_BUCKET = "<prefix>-bucket"
    # Mount a chosen path name for the bucket
    MOUNT_PATH = "/mnt/mount_path"
    # Source url
    SOURCE_URL = "s3n://{0}:{1}@{2}".format(ACCESS_KEY, ENCODED_SECRET_KEY, AWS_S3_BUCKET)
    # Mount the drive
    dbutils.fs.mount(SOURCE_URL, MOUNT_PATH)
    ```
    - see file.ipthon notebook for how you would use this setup to authenticate to AWS S3 and load data from the Kafka topics stored in this S3 bucket.

- Data Analysis using PySpark
    - file.ipthon shows the code for loading the three topics into separate PySpark dataframe (df_pin, df_geo, df_user)

    - Disable format checks during the reading of delta tables:
    ```
    %sql
    --Disable format checks during the reading of Delta tables
    SET spark.databricks.delta.formatCheck.enabled=false
    ```
    - Load a dataframe like this
    ```
    # File location and type
    # Asterisk(*) indicates reading all the content of the specified file that have .json extension
    file_location = "/mnt/mount_path/topics/0affec486183.pin/partition=0/*.json"
    file_type = "json"
    # Ask Spark to infer the schema
    infer_schema = "true"
    # Read in JSONs from mounted S3 bucket
    df_pin = spark.read.format(file_type).option("inferSchema", infer_schema).load(file_location)
    # Display Spark dataframe to check its content
    display(df_pin)
    ```

    - PySpark is then used to clean, tidy, and analyse the data for insights. The included file.ipython file has the full sourcecode for reference.

## Create a Data Steaming Pipeline

- Configure AWS Kinesis
    - Create Kinesis Streams
    Open your already setup AWS Kinesis
    Create 3 different streams with the following names:
    **streaming-<chosen_prefix>-pin**
    **streaming-<chosen_prefix>-geo**
    **streaming-<chosen_prefix>-user**

    - Create IAM Roles and Policies to invoke Kinesis
    Assign your existing IAM role permissions to invoke Kinesis
    Create a IAM policy with permissions to invoke Kinesis actions
    role name should be <chosen_prefix>-Kinesis-policy
    
    - Configure EC2 instance RESt API to invoke Kinesis actions:

    1- List streams
    
        - Navigate to the **Resources** tab of the previously created API. Use the **Create resource**
        - Under **Resource Name**, type **streams**. Leave the rest as default and then click the **Create resource** button
        
        - Choose the created **streams** resource, and then select the **Create method** button. Select `GET` as the method type.
        - For **Integration type** select **AWS Service**
        - For **AWS Region** choose *us-east-1*
        - For **AWS Service** select **Kinesis**,
        - For **HTTP method** select `POST` (as we will have to invoke Kinesis's `ListStreams` action)
        - For **Action Type** select **User action name**
        - For **Action name** type `ListStreams`
        - For **Execution role** you should copy the ARN of your Kinesis Access Role (created in the previous section)
        - Finally, click **Create method** to finalize provisioning this method

        - Go to the **Method Execution** page. From here select the **Integration request** panel, click on the **Edit** button at the bottom of the page.
        - Expand the **URL request headers parameters** panel and select the following options:
            - Under **Name** type **Content-Type**
            - Under **Mapped form** type **'application/x-amz-json-1.1'**
            - Click the **Add request header parameter** button
        - Expand the **Mapping Templates** panel and select the following options:
            - Choose **Add mapping template** button
            - Under **Content-Type** type **application/json**
            - Under **Template body** type `{}` in the template editor
        - Click on the **Save** button to save the changes
        
    2- Create, describe and delete streams in Kinesis

        - Navigate to **Resources** tab of the previously created API. Under the `streams` resource create a new child resource with the **Resource name** `{stream-name}`.
        - Create the following three **Methods** for `{stream-name}` resource: `POST`, `GET` and `DELETE`.
        - Setting up the `GET` method.
            1. In the **Create method** page you will need to define the following:

            - For **Integration type** select **AWS Service**
            - For **AWS Region** choose us-east-1
            - For **AWS Service** select **Kinesis**
            - For **HTTP method** select `POST`
            - For **Action Type** select **User action name**
            - For **Action name** type `DescribeStream`
            - For **Execution role** you should use the same ARN as in the previous step

            Finally, click **Create method**. This will redirect you to the **Method Execution** page.

            2. From here select the **Integration Request** panel, and then **Edit**. Expand the **URL request headers parameters** panel and select the following options:

            - Click on the **Add request header parameter** button
            - Under **Name** type **Content-Type**
            - Under **Mapped form** type **'application/x-amz-json-1.1'**

            3. Expand the **Mapping Ttemplates** panel and select the following options:

            - Click on the **Add mapping template** button
            - Under **Cotent-Type** type **application/json**
            - In the **Template body** include the following: 
            ```
            {
                "StreamName": "$input.params('stream-name')"
            }
            ```

        - Setting up the `POST` method.
            1. In the **Create method** page you will need to define the following:

            - For **Integration type** select **AWS Service**
            - For **AWS Region** choose us-east-1
            - For **AWS Service** select **Kinesis**
            - For **HTTP method** select `POST`
            - For **Action Type** select **User action name**
            - For **Action name** type `CreateStream`
            - For **Execution role** you should use the same ARN as in the previous step

            Finally, click **Create method**. This will redirect you to the **Method Execution** page.

            2. From here select the **Integration Request** panel, and then **Edit**. Expand the **URL request headers parameters** panel and select the following options:

            - Click on the **Add request header parameter** button
            - Under **Name** type **Content-Type**
            - Under **Mapped form** type **'application/x-amz-json-1.1'**

            3. Expand the **Mapping Ttemplates** panel and select the following options:

            - Click on the **Add mapping template** button
            - Under **Cotent-Type** type **application/json**
            - In the **Template body** include the following: 
            ```
            {
                "ShardCount": #if($input.path('$.ShardCount') == '') 5 #else $input.path('$.ShardCount') #end,
                "StreamName": "$input.params('stream-name')"
            }
            ```

        - Setting up the `DELETE` method.
            1. In the **Create method** page you will need to define the following:

            - For **Integration type** select **AWS Service**
            - For **AWS Region** choose us-east-1
            - For **AWS Service** select **Kinesis**
            - For **HTTP method** select `POST`
            - For **Action Type** select **User action name**
            - For **Action name** type `DeleteStream`
            - For **Execution role** you should use the same ARN as in the previous step

            Finally, click **Create method**. This will redirect you to the **Method Execution** page.

            2. From here select the **Integration Request** panel, and then **Edit**. Expand the **URL request headers parameters** panel and select the following options:

            - Click on the **Add request header parameter** button
            - Under **Name** type **Content-Type**
            - Under **Mapped form** type **'application/x-amz-json-1.1'**

            3. Expand the **Mapping Ttemplates** panel and select the following options:

            - Click on the **Add mapping template** button
            - Under **Cotent-Type** type **application/json**
            - In the **Template body** include the following: 
            ```
            {
                "StreamName": "$input.params('stream-name')"
            }
            ```
    3- Add records to streams in Kinesis
        - Under the `{stream-name}` resource create a two new child resources with the **Resource Name**, `record` and `records`. For both resources create a `PUT` method.
        - Setting up the record `PUT` method.
            1. In the **Create method** page you will need to define the following:

            - For **Integration type** select **AWS Service**
            - For **AWS Region** choose us-east-1
            - For **AWS Service** select **Kinesis**
            - For **HTTP method** select `POST`
            - For **Action Type** select **User action name**
            - For **Action name** type `PutRecord`
            - For **Execution role** you should use the same ARN as in the previous step

            Finally, click **Create method**. This will redirect you to the **Method Execution** page.

            2. From here select the **Integration Request** panel, and then **Edit**. Expand the **URL request headers parameters** panel and select the following options:

            - Click on the **Add request header parameter** button
            - Under **Name** type **Content-Type**
            - Under **Mapped form** type **'application/x-amz-json-1.1'**

            3. Expand the **Mapping Ttemplates** panel and select the following options:

            - Click on the **Add mapping template** button
            - Under **Cotent-Type** type **application/json**
            - In the **Template body** include the following: 
            ```
            {
                "StreamName": "$input.params('stream-name')",
                "Data": "$util.base64Encode($input.json('$.Data'))",
                "PartitionKey": "$input.path('$.PartitionKey')"
            }
            ```
        - Setting up the records `PUT` method.
            1. In the **Create method** page you will need to define the following:

            - For **Integration type** select **AWS Service**
            - For **AWS Region** choose us-east-1
            - For **AWS Service** select **Kinesis**
            - For **HTTP method** select `POST`
            - For **Action Type** select **User action name**
            - For **Action name** type `PutRecords`
            - For **Execution role** you should use the same ARN as in the previous step

            Finally, click **Create method**. This will redirect you to the **Method Execution** page.

            2. From here select the **Integration Request** panel, and then **Edit**. Expand the **URL request headers parameters** panel and select the following options:

            - Click on the **Add request header parameter** button
            - Under **Name** type **Content-Type**
            - Under **Mapped form** type **'application/x-amz-json-1.1'**

            3. Expand the **Mapping Ttemplates** panel and select the following options:

            - Click on the **Add mapping template** button
            - Under **Cotent-Type** type **application/json**
            - In the **Template body** include the following: 
            ```
            {
                "StreamName": "$input.params('stream-name')",
                "Records": [
                #foreach($elem in $input.path('$.records'))
                    {
                        "Data": "$util.base64Encode($elem.data)",
                        "PartitionKey": "$elem.partition-key"
                    }#if($foreach.hasNext),#end
                    #end
                ]
            }
            ```
- Send Events to Kinesis Streams
    - You can now send records to kinesis streams using the following code example:
    ```
    import requests
    import json

    example_df = {"index": 1, "name": "Maya", "age": 25, "role": "engineer"}

    # invoke url for one record, if you want to put more records replace record with records
    invoke_url = "https://YourAPIInvokeURL/<YourDeploymentStage>/streams/<stream_name>/record"

    #To send JSON messages you need to follow this structure
    payload = json.dumps({
        "StreamName": "YourStreamName",
        "Data": {
                #Data should be send as pairs of column_name:value, with different columns separated by commas
                "index": example_df["index"], "name": example_df["name"], "age": example_df["age"], "role": example_df["role"]
                },
                "PartitionKey": "desired-name"
                })

    headers = {'Content-Type': 'application/json'}

    response = requests.request("PUT", invoke_url, headers=headers, data=payload)
    ```
    The file __user_posting_emulation_streaming.py__ shows an example python code for sending actual events through the stream using this project's Pinterest like Data.

- Processing Kinesis Streams in Databricks
    The file __Processing Kensis Streams 2024-08-12 12_16_08.ipynb__ shows an example python code for processing Kinesis Streams in databricks and saving them to Delta Tables.


# License information
This code is released under the Creative Common CC BY 4.0 DEED License. 

