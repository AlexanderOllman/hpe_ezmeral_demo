

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

import settings


CLUSTER_NAME = settings.CLUSTER_NAME
CLUSTER_IP = settings.CLUSTER_IP

PROJECT_FOLDER = settings.PROJECT_FOLDER
ROOT_PATH = settings.ROOT_PATH
DATA_FOLDER = settings.DATA_FOLDER
VIDEO_STREAM = settings.VIDEO_STREAM
STATIC_FOLDER = settings.STATIC_FOLDER
ROBOT_STREAM = settings.ROBOT_STREAM
ROBOT_VIDEO_STREAM = settings.ROBOT_VIDEO_STREAM
ROBOT_IP = settings.ROBOT_IP

SECURE_MODE = settings.SECURE_MODE
username = settings.USERNAME
password = settings.PASSWORD
PEM_FILE = settings.PEM_FILE
STATS_TABLE = settings.STATS_TABLE
ROBOT_TABLE = settings.ROBOT_TABLE



logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='producer.log',
                    filemode='w')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


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
robot_table = connection.get_or_create_store(ROBOT_TABLE)


stream_topic = 'command'
consumer_group = str(time.time())
c = Consumer({'group.id': consumer_group, 'default.topic.config':{'auto.offset.reset':'latest'}})
c.subscribe([ROBOT_STREAM + ":" + stream_topic ])
video_producer = Producer({'streams.producer.default.stream': ROBOT_VIDEO_STREAM})
topic = 'video_feed'


if len(ROBOT_IP) > 1:
    robo = Robot(ip=ROBOT_IP)
else:
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
telemetry = []
while True:
#    ret, frame = robo.cap.read()
 #   robotCamera(frame,i)
    #create a count for every 10 seconds here
    telemetry = robo.returnPosition()
    mutation = {"$set": [{"x": telemetry[0]}, {"y": telemetry[1]}, {"z": telemetry[2]}]}
    robot_table.update(_id=1, mutation=mutation)
    
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

