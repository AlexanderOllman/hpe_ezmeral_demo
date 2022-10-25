from robot import Robot
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from confluent_kafka import Producer, Consumer
import webbrowser
import time
from os.path import exists
import json
import os
import cv2
import numpy as np

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

STATIC_FOLDER = ROOT_PATH + "/static"

app = Flask(__name__)

i = 0
b = []
j = 0
c = []


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




@app.route('/_stuff', methods = ['GET'])
def stuff():
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

@app.route('/_stuff2', methods = ['GET'])
def stuff2():
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
    #os.system("lpr -s -o fill -o media=Hagaki "+processed+".pdf")
    return result

@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(stream_video2(), mimetype='multipart/x-mixed-replace; boundary=frame')



if __name__ == '__main__':

    app.run(debug=True, host='0.0.0.0', port=9991)
