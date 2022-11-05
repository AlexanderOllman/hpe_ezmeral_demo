from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from confluent_kafka import Producer, Consumer
import webbrowser
import time
from os.path import exists
import json
import os
import cv2
import numpy as np

from mapr.ojai.storage.ConnectionFactory import ConnectionFactory

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
PRINTER_NAME = settings.PRINTER_NAME

SECURE_MODE = settings.SECURE_MODE
username = settings.USERNAME
password = settings.PASSWORD
PEM_FILE = settings.PEM_FILE
STATS_TABLE = settings.STATS_TABLE
ROBOT_TABLE = settings.ROBOT_TABLE


app = Flask(__name__)


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
stats_table = connection.get_or_create_store(STATS_TABLE)
robot_table = connection.get_or_create_store(ROBOT_TABLE)

    

#scripts used to stream video from last saved files in "real time". Very slow, not recommended.
def stream_video():

    stream_topic = 'video_feed'
    consumer_group = str(time.time())
    c = Consumer({'group.id': consumer_group, 'default.topic.config':{'auto.offset.reset':'latest'}})
    c.subscribe([ROBOT_VIDEO_STREAM + ":" + stream_topic ])

    while True:
        msg = c.poll(0.1)
        print(msg)
        if msg is None:
            continue
        if not msg.error():
            json_msg = json.loads(msg.value())
            image = json_msg.get('frame')
            while not os.path.isfile(image):
                time.sleep(0.05)
            with open(image, "rb") as imageFile:
                f = imageFile.read()
                b = bytearray(f)
                yield (b'--frame\r\n' + b'Content-Type: image/jpg\r\n\r\n' + b + b'\r\n\r\n')

def stream_video2():
    robo = Robot()
    
    while True:
        ret, frame = robo.cap.read()
        ret, buffer = cv2.imencode('.jpg', frame)

        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

    

#detects latest file in dir based on suffix, not time created. change to os.lastdir(directory) for that if desired.
def imageFlush():
    i = 0
    path= "static/images/"
    while True:
        path2 = path+"frame_"+str(i)+".jpg"
        if exists(path2):
            i = i + 1
        else:
            break
    return i

i = 0
b = []


#pass data to web JS 

@app.route('/_smileImages', methods = ['GET'])
def smileImages():
    b = []
    i = imageFlush()
    path= "static/images/"
    path2 = path+"frame_"+str(i)+".jpg"
    if i > 10:
        for j in range(i-9, i):
            b.append(j)
    else:
        for j in range(0,9):
            b.append(j)

    print(b)
    return jsonify(b=b, path=path)

j = 0
c = []

@app.route('/_robotImages', methods = ['GET'])
def robotImages():
    global j
    path="static/robot_images/"
    path2 = path+"frame_"+str(j)+".jpg"

    if exists(path2):
        if len(b) < 10:
            c.append(j)
        else:
            c.pop()
            c.insert(0, j)

        if j == 12:
            j = 1
        else:
            j = j + 1

    return jsonify(c=c, path=path)

statArray = [0,0,0,0] #smiles, smiles per face detected, goals scored, some other
telemetry = [0,0,0] #x,y,z

@app.route('/_stats', methods = ['GET'])
def stats():

    stats = stats_table.find_by_id(_id=1)
    tele = robot_table.find_by_id(_id=1)
    
    #grab the variables from JSON (haven't tested yet so don't know if this is right)
    #telemetry = [tele[0], tele[1], tele[2]]
    #statArray = [stats[0], stats[1], stats[2], stats[3]]

    return jsonify(statArray=statArray, telemetry=telemetry)


@app.route('/')
def index():

    return render_template('index3.html')

@app.route('/print', methods=['POST'])
def test():
    global i
    output = request.get_json()
    result = ROOT_PATH+json.loads(output)
    background = cv2.imread(result)
    overlay = cv2.imread(ROOT_PATH + "static/img/overlay.png")

    added_image = cv2.addWeighted(background,1.0,overlay,1.0,0)
    processed = ROOT_PATH + 'static/images/processed/face_'+str(i) 
    cv2.imwrite(processed+".jpg", added_image, [cv2.IMWRITE_JPEG_QUALITY, 100])

    print("Printing " + processed+".jpg")
    os.system("convert " + processed + ".jpg "+processed+".pdf")
    time.sleep(3)
    os.system("lp -d "+PRINTER_NAME+" -o fill "+processed+".pdf")
    return result

@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(stream_video2(), mimetype='multipart/x-mixed-replace; boundary=frame')



if __name__ == '__main__':

    app.run(debug=True, host='0.0.0.0', port=9991)
