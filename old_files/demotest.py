


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



import settings

import cv2
import numpy as np
from collections import namedtuple
import robomasterpy

Rectangle = namedtuple('Rectangle', 'xmin ymin xmax ymax')

#print("Before URL")
cap = cv2.VideoCapture('rtsp://admin:Admin12345@192.168.100.131/Src/MediaInput/stream_2')
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
#print("After URL")

width = int(cap.get(3))
height = int(cap.get(4))

#ip = robomasterpy.get_broadcast_ip()
#robo = robomasterpy.Commander(ip)
#print(ip)
print("go!")

boolGo = True
total = 0
def area(a, b):  # returns None if rectangles don't intersect
    dx = min(a.xmax, b.xmax) - max(a.xmin, b.xmin)
    dy = min(a.ymax, b.ymax) - max(a.ymin, b.ymin)
    if (dx>=0) and (dy>=0):
        return dx*dy

def drawRectangle(frame, rect, colour):
    shapes = np.zeros_like(frame, np.uint8)
    if colour == 'white':
        col = (255,255,255)
    elif colour == 'blue':
        col = (0,0,255)
    elif colour == 'red':
        col = (255,0,0)
    elif colour == 'green':
        col = (0,255,0)

    cv2.rectangle(shapes, (rect.xmin, rect.ymin), (rect.xmax+rect.xmin, rect.ymax+rect.ymin), col, cv2.FILLED)
    alpha = 0.5
    mask = shapes.astype(bool)
    frame[mask] = cv2.addWeighted(frame, alpha, shapes, 1 - alpha, 0)[mask]


while True:
    start = time.time()
    #print('About to start the Read command')
    ret, frame = cap.read()
    #print('About to show frame of Video.')
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize =(250,250),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    # faces = full_cascade.detectMultiScale(gray, 1.1, 5)
    left = Rectangle(0,0,int(width/3),height)
    drawRectangle(frame, left, 'green')

    right = Rectangle(width-int(width/3), 0, width, height)
    drawRectangle(frame, right, 'red')

    x, y, w, h = 0, 0, 0, 0
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 4)
        # Grab ROI with Numpy slicing and blur
        face = Rectangle(x,y,x+w,y+h)
        if (area(left,face)) and boolGo:
            print("LEFT")
   #         robo.chassis_move(y=0.5)
            boolGo = False
        if (area(right,face)):
            print("RIGHT")
  #          robo.chassis_move(y=-0.5)
            boolGo = False
        # blur = cv2.GaussianBlur(ROI, (51, 51), 0)
        # print(area(ROI, sub_img))
        # Insert ROI back into image
        # frame[y:y + h, x:x + w] = blur


    fps = cap.get(5)
 #   cv2.imshow("Capturing",frame)
    #print('Running..')
    end = time.time()
    diff = end - start
    total = total + diff

    if total > 1:
        boolGo = True
        total = 0

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
#cv2.destroyAllWindows()


