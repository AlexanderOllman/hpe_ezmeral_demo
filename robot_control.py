

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


stream_topic = 'command'
consumer_group = str(time.time())
c = Consumer({'group.id': consumer_group, 'default.topic.config':{'auto.offset.reset':'latest'}})
c.subscribe([ROBOT_STREAM + ":" + stream_topic ])

robo = Robot()



print('Robot Control Starting...')     

while True:

    msg=c.poll(0.1) #timeout
    if msg is None:
        continue
    if msg.error():
        print('Error: {}'.format(msg.error()))
        continue
    else:
        data = json.loads(msg.value())
        command = data.get('control')
        print(command)
        if command == "l":
            robo.rotateLeft()
        if command == "r":
            robo.rotateRight()
        if command == "f":
            robo.moveForward()
        if command == "b":
            robo.moveBackward()
        if command == "s":
            robo.stop()

c.close()

