

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

ROBOT_VIDEO_STREAM = DATA_FOLDER + 'robot_cam_stream' # Stream for the video frame>

ROBOT_STREAM = DATA_FOLDER + 'robot_stream'

STATIC_FOLDER = ROOT_PATH + "static/"


stream_topic = 'command'
consumer_group = str(time.time())
c = Consumer({'group.id': consumer_group, 'default.topic.config':{'auto.offset.reset':'latest'}})
c.subscribe([ROBOT_STREAM + ":" + stream_topic ])
video_producer = Producer({'streams.producer.default.stream': ROBOT_VIDEO_STREAM})
topic = 'video_feed'
robo = Robot()


def receipt(err,msg):
    if err is not None:
        print('Error: {}'.format(err))
    else:
        message = 'Produced message on topic {} with value of {}\n'.format(msg.topic(), msg.value().decode('utf-8'))
        logger.info(message)
        print(message)

def robotCamera(frame, i):
    savePath = STATIC_FOLDER + "robot_images/"
    fileName = savePath + "frame_" + str(i) + ".jpg"
    cv2.imwrite(fileName, frame)
    data = {
            'offset': time.time(),
            'frame': fileName,
        }
    m = json.dumps(data)
    video_producer.poll(0.2)
    video_producer.produce(topic, m.encode('utf-8'), callback=receipt)
    video_producer.flush()



print('Robot Control Starting...')     
i = 1
while True:
#    ret, frame = robo.cap.read()
 #   robotCamera(frame,i)
    if i == 20:
        i = 1 
    else:
        i = i + 1                 
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
 
robo.cap.release()
c.close()

