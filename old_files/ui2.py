#! /usr/bin/python

import math
import io
import os
import json
import time
import argparse
import traceback
from random import randint
from shutil import copyfile
from copy import deepcopy
import logging
import settings
import cv2

from flask import Flask, render_template, request, Response, flash, redirect, url_for
from mapr.ojai.storage.ConnectionFactory import ConnectionFactory
from confluent_kafka import Producer, Consumer, KafkaError

import settings


logging.basicConfig(filename=settings.LOG_FOLDER + "teits_ui.log",
                    level=logging.INFO,
                    format='%(asctime)s :: %(levelname)s :: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()
logger.setLevel(settings.LOG_LEVEL)

#### Kill previous instances
current_pid = os.getpid()
all_pids = os.popen("ps aux | grep 'teits_ui.py' | awk '{print $2}'").read().split('\n')[:-1]
for pid in all_pids:
    if int(pid) != current_pid:
        logging.info("killing {}".format(pid))
        #os.kill(pid, signal.SIGKILL)
        os.system("kill -9 {}".format(pid))


CLUSTER_NAME = settings.CLUSTER_NAME
CLUSTER_IP = settings.CLUSTER_IP

PROJECT_FOLDER = settings.PROJECT_FOLDER
ROOT_PATH = CLUSTER_NAME + settings.PROJECT_FOLDER
RECORDING_FOLDER = settings.RECORDING_FOLDER

DRONEDATA_TABLE = settings.DRONEDATA_TABLE
ZONES_TABLE = settings.ZONES_TABLE
CONTROLS_TABLE = settings.CONTROLS_TABLE

VIDEO_STREAM = settings.VIDEO_STREAM
POSITIONS_STREAM = settings.POSITIONS_STREAM
RECORDING_STREAM = settings.RECORDING_STREAM
OFFSET_RESET_MODE = settings.OFFSET_RESET_MODE
DISPLAY_STREAM_NAME = settings.DISPLAY_STREAM_NAME

SECURE_MODE = settings.SECURE_MODE
username = settings.USERNAME
password = settings.PASSWORD
PEM_FILE = settings.PEM_FILE
DRONE_MODE = settings.DRONE_MODE


app = Flask(__name__)



def gen_frames():  # generate frame by frame from camera
    cap = cv2.VideoCapture('rtsp://admin:Admin12345@192.168.100.131/Src/MediaInput/stream_2')
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

    while True:
        # Capture frame-by-frame
        success, frame = cap.read()  # read the camera frame
        if not success:
            break
        #else:
         #   gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
          #  faces = face_cascade.detectMultiScale(
           #     gray,
            #    scaleFactor=1.1,
             #   minNeighbors=5,
              #  minSize=(100, 100),
               # flags=cv2.CASCADE_SCALE_IMAGE
    #        )
     #       x, y, w, h = 0, 0, 0, 0
      #      for (x, y, w, h) in faces:
       #         cv2.rectangle(frame, (x, y), (x + w, y + h), (130, 169, 1), 4)
                # Grab ROI with Numpy slicing and blur
            
        ret, buffer = cv2.imencode('.jpg', frame)

        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result



###################################
#####         MAIN UI         #####
###################################

# Main UI
@app.route('/')
def home():
  return render_template("teits_ui.html",)




@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')



# Video player
@app.route('/intro')
def intro():
    # return render_template("intro.html")
    return """
    <a href="/">Go to Demo</a>
    <iframe src="https://www.youtube.com/embed/iV40iGZzfYQ" width="100%" height="100%" frameborder="0" allowfullscreen></iframe>
    """



# Streams images from the video stream
@app.route('/video_stream/<drone_id>')
def video_stream(drone_id):
  return Response(stream_video(drone_id), mimetype='multipart/x-mixed-replace; boundary=frame')



# Changes DISPLAY stream
@app.route('/set_video_stream',methods=["POST"])
def set_video_stream():
  global DISPLAY_STREAM_NAME
  DISPLAY_STREAM_NAME = request.form["stream"]
  return "Display stream changed to {}".format(DISPLAY_STREAM_NAME)



# Resets drone position to home_base:landed in the database and the positions stream
@app.route('/reset_position',methods=["POST"])
def reset_position():
    drone_id = request.form["drone_id"]
    dronedata_table.update(_id=drone_id,mutation={"$put": {'position.zone': "home_base"}})
    dronedata_table.update(_id=drone_id,mutation={"$put": {'position.status': "landed"}})
    return "Reset position for {}".format(drone_id)





app.run(debug=True,host='0.0.0.0',port=9890)
