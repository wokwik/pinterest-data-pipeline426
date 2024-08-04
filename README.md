# pinterest-data-pipeline426

# Table of content
- Description
- Installation instructions
- Usage instructions
- File structure of the project
- License information
  
# Description
This project is about replicating a data processing pipeline similar to ones used at Pinterest for processing the post requests generated when a user uploads data (content) to the Pinterest Platform.

The post requests consists of three related events: pinterest_data, geolocation_data, and user_data. Due to the sheer volume we expect Pinterest is expected to process per unit of time, the infrastructure is expected to handle large volumes, exhibit high robustiness, and be scalabile to meet demand in real time.

AWS cloud is chosen to implement this project as it is well known for providing highly available, highly scalable, and always available infrastructure that is able to meet the toughest of demand. Also AWS service inlcudes robust and very capable services for this type of project namely MSK, EC2, S3, API Gateway, and Kinesis. 

AWS MSK is fully managed Apache Kafka service to process data, which significantly reduces the effort and time required to setup and manange Apache Kafka in production environments. Apache Kafka is an open-source technology for distributed data storage that is designed to be optimised for ingesting and processing streaming data in real-time. We will create Kafka custom Plugins using Confluent.io for connecting to S3, Add Kafka plugins for using AWS IAM roles to communicate with an S3 bucket instance, and create a Kafka Connector for sending data to the S3 bucket.

AWS EC2 is cloud hosted server that can be created within the MSK Cluster and configured bespoke as powerful as required processing, RAM, and storage specifications. EC2 will act as an Apache Kafka client and used for creating topics in the MSK cluster.


# Installation instruction

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
        chmod <pem-file-name>.pem 
        Then you can use this command to connect to EC2:
        ssh -i <pem-file-name>.pem ec2-user@<EC2-connection-string>.amazonaws.com

    - Install Kafka on EC2 instance:
        Firstly you need to install Java-1.8.0 using this command
        sudo yum install java-1.8.0

        Secondly you want to install Kafka using these commands:
        wget https://archive.apache.org/dist/kafka/2.8.1/kafka_2.12-2.8.1.tgz
        tar -xzf kafka_2.12-2.8.1.tgz

        Thirdly you want to install a plugin to enable EC2 Kafka client to authenticate and authorise on the MSK cluster:
        browse to libs directory within the Kafka installation folder using:
        cd ~/kafka_2.12-2.8.1/libs/

        install AWS MSK IAM AUTH package using:
        wget https://github.com/aws/aws-msk-iam-auth/releases/download/v1.1.5/aws-msk-iam-auth-1.1.5-all.jar

        Forthly make the AWS MSK IAM AUTH package available on the environment path by adding to the .bashrc file, using these commands:
        nano ~/.bashrc
        add the following line in the .bashrc file and save
        export CLASSPATH=/home/ec2-user/kafka_2.12-2.8.1/libs/aws-msk-iam-auth-1.1.5-all.jar

        Remeber to end SSH session and start again to see the above .bahsrc change taking effect for your session.

        Finally configure Kafka client to use AWS IAM
        Navigate to Kafka installation folder bin directory
        cd ~/kafka_2.12-2.8.1/bin/

        and create a client.properties file using this command:
        nano client.properties
        
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
        ./kafka-topics.sh --bootstrap-server <BootstrapServerString> --command-config client.properties --create --topic <topic_name>

        Create 3 topics for each of the event types
        <chosen_prefix>.pin for the Pinterest posts data
        <chosen_prefix>.geo for the post geolocation data
        <chosen_prefix>.user for the post user data

    - Create a Custom Plugin with MSK Connect
        Connect to your EC2 Client instance using SSH client and run the following commands:
        # assume admin user privileges
        sudo -u ec2-user -i
        # create directory where we will save our connector 
        mkdir kafka-connect-s3 && cd kafka-connect-s3
        # download connector from Confluent
        wget https://d2p6pa21dvn84.cloudfront.net/api/plugins/confluentinc/kafka-connect-s3/versions/10.0.3/confluentinc-kafka-connect-s3-10.0.3.zip
        # copy connector to our S3 bucket
        aws s3 cp ./confluentinc-kafka-connect-s3-10.0.3.zip s3://<BUCKET_NAME>/kafka-connect-s3/

        Which should add the object in your S3 Bucket: /kafka-connect-s3/confluentinc-kafka-connect-s3-10.0.3.zip

        Navigate to MSK Console, and select MSK Connect => Customised plugins, then create a custom plugin. Choose the Confluent connector ZIP file you uploaded above in your S3 bucket. Give the plugin a name like so <chosen_prefix>-plugin
    
    - Create a Connector with MSK Connect
        Navigate to MSK Connect => Connectors, and click to create new Connector.
        
        Give your connector a name like <chosen_prefix>-connector
        
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


-  


# File structure
The directory includes a number of files:
- __file.py__: This file is the main file to use for running selected components of the pipeline, or the entire pipeline at once.


# License information
This code is released under the Creative Common CC BY 4.0 DEED License. 

