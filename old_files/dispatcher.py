#! /usr/bin/python

"""
Dispatcher

Reads messages from a defined stream
Sends messages to processor streams adding an offset field used 
by processors to release processed messages in the right order 


"""

import time
import os
import json
import traceback
from confluent_kafka import Producer, Consumer
from mapr.ojai.storage.ConnectionFactory import ConnectionFactory

import settings

import logging

logging.basicConfig(filename=settings.LOG_FOLDER + "dispatcher.log",
                    level=logging.INFO,
                    format='%(asctime)s :: %(levelname)s :: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()
logger.setLevel(settings.LOG_LEVEL)

############################       Settings        #########################



CLUSTER_IP = settings.CLUSTER_IP
SOURCE_STREAM = settings.VIDEO_STREAM
PROCESSORS_STREAM = settings.PROCESSORS_STREAM
PROCESSORS_TABLE = settings.PROCESSORS_TABLE
SECURE_MODE = settings.SECURE_MODE
username = settings.USERNAME
password = settings.PASSWORD
PEM_FILE = settings.PEM_FILE

def create_and_get_table(connection, table_path):
  if connection.is_store_exists(table_path):
    data_store = connection.get_store(table_path)
  else:
    data_store = connection.create_store(table_path)
  return data_store

# Initialize databases
if SECURE_MODE:
  connection_str = "{}:5678?auth=basic;" \
                           "user={};" \
                           "password={};" \
                           "ssl=true;" \
                           "sslCA={};" \
                           "sslTargetNameOverride={}".format(CLUSTER_IP,username,password,PEM_FILE,CLUSTER_IP)
else:
  connection_str = "{}:5678?auth=basic;user={};password={};ssl=false".format(CLUSTER_IP,username,password)
  
connection = ConnectionFactory().get_connection(connection_str=connection_str)
processors_table = create_and_get_table(connection, settings.BASE_PROCESSORS_TABLE)



#######################       MAIN FUNCTION       ##################

def main():

    # Reset processors table
    for proc in processors_table.find():
        # logging.info(proc)
        processors_table.delete(_id=proc["_id"])
        # logging.info("deleted")

    # Subscribe to source stream on given topics
    consumer_group = str(time.time())
    main_consumer = Consumer({'group.id': consumer_group,'default.topic.config': {'auto.offset.reset': 'latest'}})
    main_consumer.subscribe([SOURCE_STREAM + ":drone_1_source",SOURCE_STREAM + ":drone_2_source",SOURCE_STREAM + ":drone_3_source",]) 
    producer = Producer({'streams.producer.default.stream': PROCESSORS_STREAM})

    # Initialize offset
    try:
        offset = processors_table.find_by_id("offset")["offset"]
    except:
        offset = 0
        processors_table.insert_or_replace({"_id":"offset","offset":offset}) 
    
    start_time = time.time()
    current_sec = 0
    received_messages = 0
    sent_messages = 0
    logging.info("waiting for new data ... ")
    while True:
        try:
            msg = main_consumer.poll()
            if msg is None:
                continue
            if not msg.error():
                json_msg = json.loads(msg.value().decode('utf-8'))
                received_messages += 1
                # get the first available processor
                processed = False
                result = processors_table.find({"$where": {"$eq": {"status": "available"}},"$limit": 1})
                for doc in result:
                    # set the processor as "busy"
                    # the processor state will be reset as "available" by the processor itself 
                    # once the message has been processed 
                    doc["status"] = "busy"
                    processors_table.insert_or_replace(doc)

                    offset += 1
                    json_msg["offset"] = offset # Insert offset in the message. Used to release frames in order

                    # Push the frame to be processed in the processor topic
                    producer.produce(doc["_id"],json.dumps(json_msg))
                    sent_messages += 1

                # Print stats every second
                elapsed_time = time.time() - start_time
                if int(elapsed_time) != current_sec:
                    logging.info("Dispatching - Received {} msg/s , sent {} msg/s".format(received_messages,sent_messages))
                    received_messages = 0
                    sent_messages = 0
                    current_sec = int(elapsed_time)

        except Exception as ex:
            logging.exception("failed")


if __name__ == '__main__':
    main()
