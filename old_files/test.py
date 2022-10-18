import traceback
import time
from time import sleep
import os
import sys
try:
    import av
except:
    pass
import tellopy
import json
import threading
from random import randint
from confluent_kafka import Producer, Consumer, KafkaError
from mapr.ojai.storage.ConnectionFactory import ConnectionFactory
from math import atan2, sqrt, pi, floor
from shutil import copyfile
import base64
from io import BytesIO
import logging
import glob
# Configure consumer

def get_cluster_name():
  with open('/opt/mapr/conf/mapr-clusters.conf', 'r') as f:
    first_line = f.readline()
    return first_line.split(' ')[0]

def get_cluster_ip():
  with open('/opt/mapr/conf/mapr-clusters.conf', 'r') as f:
    first_line = f.readline()
    return first_line.split(' ')[2].split(':')[0]


CLUSTER_NAME = get_cluster_name()
CLUSTER_IP = get_cluster_ip()

PROJECT_FOLDER = "/teits/" # Project folder from the cluster root
ROOT_PATH = '/mapr/' + CLUSTER_NAME + '/projects' + PROJECT_FOLDER
BASE_PATH = '/projects' + PROJECT_FOLDER
BASE_PROJECTS = '/projects'
PROJECTS = '/mapr/' + CLUSTER_NAME + '/projects'
DATA_FOLDER = ROOT_PATH + "data/" # Folder to store the data
BASE_DATA_FOLDER = BASE_PATH + "data/"
RECORDING_FOLDER = DATA_FOLDER + "recording/" # Folder to store the reco>
BASE_RECORDING_FOLDER = BASE_DATA_FOLDER + "recording/"
LOG_FOLDER = ROOT_PATH + "logs/" # Folder to store the data
BASE_LOG_FOLDER = BASE_PATH + "logs/"
APPLICATION_FOLDER = ROOT_PATH + "Tello/" # Folder to python app code

# Ezmeral Data Fabric Stream names
POSITIONS_STREAM = DATA_FOLDER + 'positions_stream'   # Stream for stori>
BASE_POSITIONS_STREAM = BASE_DATA_FOLDER + 'positions_stream'   # Stream>

PROCESSORS_STREAM = DATA_FOLDER + 'processors_stream'   # Stream to feed>
BASE_PROCESSORS_STREAM = BASE_DATA_FOLDER + 'processors_stream'   # Stre>

VIDEO_STREAM = DATA_FOLDER + 'video_stream' # Stream for the video frame>
BASE_VIDEO_STREAM = BASE_DATA_FOLDER + 'video_stream' # Stream for the v>

RECORDING_STREAM = DATA_FOLDER + 'recording_stream' # Stream for the vid>
BASE_RECORDING_STREAM = BASE_DATA_FOLDER + 'recording_stream' # Stream f>


ALLOWED_LAG = 2 # Allowed lag between real time events and processed eve>
OFFSET_RESET_MODE = 'latest' # latest for running the demo, earliest can>
DISPLAY_STREAM_NAME = "processed" # source or processed- which default s>

UI_PORT = 9889

DRONE_ID = "drone_1"

IMAGE_FOLDER = ROOT_PATH + "/" + DRONE_ID + "/images/source/"

consumer_group = DRONE_ID + str(time.time())
consumer = Consumer({'group.id': consumer_group,'default.topic.config': {'auto.offset.reset': 'latest'}})
consumer.subscribe([VIDEO_STREAM + ":" + DRONE_ID])

producer = Producer({'streams.producer.default.stream': VIDEO_STREAM})

index = 0

while True:
        index = index + 1
        producer.produce(DRONE_ID, json.dumps({"drone_id":DRONE_ID,
                                                          "index":index,
                                                          "image":IMAGE_FOLDER + "frame-{}.jpg".format(index)}))
        print(index)
        time.sleep(1)

        msg = consumer.poll()
        if msg is None:
            continue
        else:
            received_msg = json.loads(msg.value().decode("utf-8"))

            print(recieved_msg)


