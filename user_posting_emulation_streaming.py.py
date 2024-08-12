import requests
from time import sleep
import random
from multiprocessing import Process
import boto3
import json
import sqlalchemy
from sqlalchemy import text


random.seed(100)


class AWSDBConnector:

    def __init__(self):
        import yaml
        import json

        f = 'db_creds.yaml'
        creds = yaml.safe_load(open(f))
        # print('file content are::')
        # print(creds)

        self.HOST = creds['RDS_HOST']
        self.USER = creds['RDS_USER']
        self.PASSWORD =  creds['RDS_PASSWORD']
        self.DATABASE = creds['RDS_DATABASE']
        self.PORT = creds['RDS_PORT']
        
    def create_db_connector(self):
        engine = sqlalchemy.create_engine(f"mysql+pymysql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DATABASE}?charset=utf8mb4")
        return engine


new_connector = AWSDBConnector()


def run_infinite_post_data_loop():
    from collections import Counter
    
    choice = 'y'

    while choice == 'y':

        #choice = input("Another run? (y/n): ")
        if choice != 'y':
            break

        sleep(random.randrange(0, 2))
        random_row = random.randint(0, 11000)
        engine = new_connector.create_db_connector()

        with engine.connect() as connection:

            pin_string = text(f"SELECT * FROM pinterest_data LIMIT {random_row}, 1")
            pin_selected_row = connection.execute(pin_string)
            
            for row in pin_selected_row:
                pin_result = dict(row._mapping)

            geo_string = text(f"SELECT * FROM geolocation_data LIMIT {random_row}, 1")
            geo_selected_row = connection.execute(geo_string)
            
            for row in geo_selected_row:
                geo_result = dict(row._mapping)

            user_string = text(f"SELECT * FROM user_data LIMIT {random_row}, 1")
            user_selected_row = connection.execute(user_string)
            
            for row in user_selected_row:
                user_result = dict(row._mapping)

            print('\n## pin_result ##')
            #print(Counter(pin_result).most_common(3))
            #print(pin_result)

            # headers
            headers = {'Content-Type': 'application/json'}
            # invoke url for one record, if you want to put more records replace record with records
            invoke_url = "https://cvv4sqxyja.execute-api.us-east-1.amazonaws.com/Production/streams/{stream-name}/record"

            # To send JSON messages you need to follow this structure
            payload = json.dumps({
                "StreamName": "streaming-0affec486183-pin",
                "Data": pin_result,
                        "PartitionKey": "partition-1"
                        }, default=str)

            response = requests.request("PUT", invoke_url, headers=headers, data=payload)
            print(response.json)
            

            print('\n## geo_result ##')
            #print(Counter(geo_result).most_common(3))
            #print(geo_result)
            # headers
            headers = {'Content-Type': 'application/json'}
            # invoke url for one record, if you want to put more records replace record with records
            invoke_url = "https://cvv4sqxyja.execute-api.us-east-1.amazonaws.com/Production/streams/{stream-name}/record"

            # To send JSON messages you need to follow this structure
            payload = json.dumps({
                "StreamName": "streaming-0affec486183-geo",
                "Data": geo_result,
                        "PartitionKey": "partition-2"
                        }, default=str)
            print(payload)
            response = requests.request("PUT", invoke_url, headers=headers, data=payload)
            print(response.json)


            print('\n## user_result ##')
            #print(Counter(user_result).most_common(3))
            #print(user_result)
            # headers
            headers = {'Content-Type': 'application/json'}
            # invoke url for one record, if you want to put more records replace record with records
            invoke_url = "https://cvv4sqxyja.execute-api.us-east-1.amazonaws.com/Production/streams/{stream-name}/record"

            # To send JSON messages you need to follow this structure
            payload = json.dumps({
                "StreamName": "streaming-0affec486183-user",
                "Data": user_result,
                        "PartitionKey": "partition-3"
                        }, default=str)
            
            response = requests.request("PUT", invoke_url, headers=headers, data=payload)
            print(response.json)

if __name__ == "__main__":
    run_infinite_post_data_loop()
    print('Working')


