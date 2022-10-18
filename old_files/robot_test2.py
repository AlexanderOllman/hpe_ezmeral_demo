

from confluent_kafka import Producer, Consumer
import json
import logging
import random

from flask import Flask, render_template, Response
from threading import Thread
from imutils.video import FPS

import cv2
import numpy as np
from collections import namedtuple
import robomasterpy
import time
from robot import Robot
# use 0 for web camera
#  for cctv camera use rtsp://username:password@ip_address:554/user=username_password='password'_channel=channel_number_stream=0.sdp' instead of camera
# for local webcam use cv2.VideoCapture(0)


logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='producer.log',
                    filemode='w')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


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

DATA_FOLDER = ROOT_PATH + "data/" # Folder to store the data

ROBOT_STREAM = DATA_FOLDER + 'robot_stream' # Stream for the video frame>

STATIC_FOLDER = ROOT_PATH + "static/"


p = Producer({'streams.producer.default.stream': ROBOT_STREAM})


print('Kafka Producer has been initiated...')

def receipt(err,msg):
    if err is not None:
        print('Error: {}'.format(err))
    else:
        message = 'Produced message on topic {} with value of {}\n'.format(msg.topic(), msg.value().decode('utf-8'))
        logger.info(message)
        print(message)

     

i = 0
while True:

    data = {
        'time': time.time(),
        'control': "l",
    }
    m = json.dumps(data)
    p.poll(1)
    p.produce('command', m.encode('utf-8'), callback=receipt)
    p.flush()

    time.sleep(1)

