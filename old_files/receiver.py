#! /usr/bin/python
# TODO: Define this

import time
from mapr.ojai.storage.ConnectionFactory import ConnectionFactory
from confluent_kafka import Producer, KafkaError
import traceback
import sys
import base64
import settings
import logging
import os
import json
import numpy as np
import av



DRONE_ID = sys.argv[1]

logging.basicConfig(filename=settings.LOG_FOLDER + "receiver_{}.log".format(DRONE_ID),
                    level=logging.INFO,
                    format='%(asctime)s :: %(levelname)s :: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()
logger.setLevel(settings.LOG_LEVEL)

DATA_FOLDER = settings.DATA_FOLDER
BUFFER_TABLE = DATA_FOLDER + "{}_buffer".format(DRONE_ID)
CLUSTER_IP = settings.CLUSTER_IP
VIDEO_STREAM = settings.VIDEO_STREAM
SECURE_MODE = settings.SECURE_MODE
username = settings.USERNAME
password = settings.PASSWORD
PEM_FILE = settings.PEM_FILE

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
buffer_table = connection.get_or_create_store(BUFFER_TABLE)

logging.info("Producing video from records into {}".format(VIDEO_STREAM))
video_producer = Producer({'streams.producer.default.stream': VIDEO_STREAM})


go_on = False
while not go_on: 
    try:
        start_cleaning = time.time()
        logging.info("cleaning database")
        # Clean database
        for doc in buffer_table.find({"$select":["_id"]}):
            buffer_table.delete(_id=doc["_id"])
        go_on = True
        logging.info("db cleaned : {} s ".format(time.time()-start_cleaning))
    except:
        logging.exception("cleaning failed")


start_time = time.time()
received_frames = 0
current_sec = 0

time_tracker = {"min":1000,"max":0,"count":0,"avg":0}

while True:
    try:
        logging.info("new query")
        ids=[]
        for message in buffer_table.find({"$select":["_id"]}):
            ids.append(int(message["_id"]))

        logging.info(ids)

        for _id in sorted(ids):
            start_track_time = time.time() 
            _id = str(_id)
            message = buffer_table.find_by_id(_id)
            image_name = message["image_name"]
            enc_str = message["image_bytes"]
            image = base64.b64decode(enc_str)
            with open(image_name,'wb') as image_file:
                image_file.write(image)
            index = _id
            video_producer.produce(DRONE_ID + "_source", json.dumps({"drone_id":DRONE_ID,
                                                                     "index":index,
                                                                     "image":image_name}))
            buffer_table.delete(_id=_id)   

            received_frames += 1  

            duration = time.time() - start_track_time
            time_tracker["min"] = min(time_tracker["min"],duration)
            time_tracker["max"] = max(time_tracker["max"],duration)
            time_tracker["count"] += 1
            time_tracker["avg"] = (time_tracker["avg"] * (time_tracker["count"] - 1) + duration) / time_tracker["count"]

            # Print stats every second
            elapsed_time = time.time() - start_time
            if int(elapsed_time) != current_sec:
                logging.info("Elapsed : {} s, received {} fps".format(int(elapsed_time),received_frames))
                logging.info("Time tracker : {} ".format(time_tracker))
                received_frames = 0
                time_tracker["min"] = 100
                time_tracker["max"] = 0
                current_sec = int(elapsed_time)

        logging.info("sleep")
        time.sleep(1)
    except:
        logging.exception("failed")
                


