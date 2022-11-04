from flask import Flask, render_template, Response
from threading import Thread
import multiprocessing as mp
import cv2
import numpy as np
from collections import namedtuple
import json
import os
from os.path import exists
import logging
import robomasterpy
import subprocess
import time
#from robot import Robot
from deface import deface
from deface.centerface import CenterFace

import settings

Rectangle = namedtuple('Rectangle', 'xmin ymin width height')

from confluent_kafka import Producer

app = Flask(__name__)

CLUSTER_NAME = settings.CLUSTER_NAME
CLUSTER_IP = settings.CLUSTER_IP

PROJECT_FOLDER = settings.PROJECT_FOLDER
ROOT_PATH = settings.ROOT_PATH
DATA_FOLDER = settings.DATA_FOLDER
VIDEO_STREAM = settings.VIDEO_STREAM
STATIC_FOLDER = settings.STATIC_FOLDER
ROBOT_STREAM = settings.ROBOT_STREAM
CAMERA_FEED = settings.CAMERA_FEED


#DRONEDATA_TABLE = settings.DRONEDATA_TABLE
#ZONES_TABLE = settings.ZONES_TABLE
#CONTROLS_TABLE = settings.CONTROLS_TABLE

#VIDEO_STREAM = settings.VIDEO_STREAM
#POSITIONS_STREAM = settings.POSITIONS_STREAM
#RECORDING_STREAM = settings.RECORDING_STREAM
#OFFSET_RESET_MODE = settings.OFFSET_RESET_MODE
#DISPLAY_STREAM_NAME = settings.DISPLAY_STREAM_NAME

#SECURE_MODE = settings.SECURE_MODE
#username = settings.USERNAME
#password = settings.PASSWORD
#PEM_FILE = settings.PEM_FILE
#DRONE_MODE = settings.DRONE_MODE

robotProcess = []



logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='producer.log',
                    filemode='w')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def overlap(box, face):
    a = [box.xmin, box.ymin]
    b = [box.xmin + box.width, box.ymin + box.height]
    c = [face.xmin, face.ymin]
    d = [face.xmin + face.width, face.ymin + face.height]
    x, y = 0,1

    width = min(b[x], d[x]) - max(a[x], c[x])
    height = min(b[y], d[y]) - max(a[y], c[y])

    if min(width, height) > 0:
        return width * height
    else:
        return 0

def detectFacesCNN(result_queue, queue_from_faces):
    #far more accurate in off-demo testing, way too slow here. Did not have time to diagnose.
    centerface = CenterFace(in_shape=None, backend='auto')
    while True:
        x0, y0, x3, y3 = 0,0,0,0
        frame = result_queue.get()
        if frame is not None:
            dets, _ = centerface(frame, threshold=0.2)
            for i, det in enumerate(dets):
                boxes, score = det[:4], det[4]
                x, y, x2, y2 = boxes.astype(int)
                if (x2-x1)*(y2-y1) > area:
                    area = (x2-x1)*(y2-y1)
                    x0, y0, x3, y3 = deface.scale_bb(x1, y1, x2, y2, 1.1)
            y0, y3 = max(0, y0), min(frame.shape[0] - 1, y3)
            x0, x3 = max(0, x0), min(frame.shape[1] - 1, x3)
            w, h = (x3 - x0), (y3 - y0)
            cv2.rectangle(frame, (x0, y0), (x3, y3), (130,169,1), 4)
            if len(dets) > 0:
                face = Rectangle(x0,y0,w,h)
            else:
                face = ()
            arr = [frame, face]
            queue_from_faces.put(arr)

def detectFaces(result_queue, queue_from_faces):
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

    while True:
        frame = result_queue.get()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces, rejectLevels, levelWeights = face_cascade.detectMultiScale3(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(200, 200),
            flags=cv2.CASCADE_SCALE_IMAGE,
            outputRejectLevels=True
        )
        if len(levelWeights) != 0: #grabs and draws the highest confidence face only
            max_index = np.argmax(levelWeights)
            x, y, w, h = faces[max_index]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (130, 169, 1), 4)
            face = Rectangle(x, y, w, h)
        else:
            face = ()
        arr = [frame, face]
        queue_from_faces.put(arr)

def detectOverlap(queue_from_faces):
    while True:
        arr = queue_from_faces.get()
        height, width, c = arr[0].shape
        face = arr[1]
        if len(face) != 0:
            left = Rectangle(0, 0, int(width / 4), height)
            right = Rectangle(width - int(width / 4), 0, width, height)
            forward = Rectangle(int(width / 4), 0, width - int(width / 2), int(height / 5))
            back = Rectangle(int(width / 4), height - int(height / 5), width - int(width / 2), int(height / 5))

            overlapCheck = [overlap(left, face), overlap(right, face), overlap(forward, face), overlap(back, face)]
            maxOverlap = np.argmax(overlapCheck)
            if (np.sum(overlapCheck) == 0):
                print("STOP")
                controlRobot('s')
            elif (maxOverlap == 0):
                print("LEFT")
                controlRobot('l')
            elif (maxOverlap == 1):
                print("RIGHT")
                controlRobot('r')

            elif (maxOverlap == 2):
                print("FORWARD")
                controlRobot('f')

            elif (maxOverlap == 3):
                print("BACK")
                controlRobot('b')

        else:
            controlRobot('s')

def receipt(err,msg):
    if err is not None:
        print('Error: {}'.format(err))
    else:
        message = 'Produced message on topic {} with value of {}\n'.format(msg.topic(), msg.value().decode('utf-8'))
        logger.info(message)
        print(message)


def controlRobot(command):
    robot_producer = Producer({'streams.producer.default.stream': ROBOT_STREAM})
    topic = 'command'
    data = {
                'offset': time.time(),
                'control': command,
           }
    m = json.dumps(data)
    robot_producer.poll(0.1)
    robot_producer.produce(topic, m.encode('utf-8'), callback=receipt)
    robot_producer.flush()


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



def detectSmiles(queue_from_faces):
    i = 0
    video_producer = Producer({'streams.producer.default.stream': VIDEO_STREAM})
    smile_cascade = cv2.CascadeClassifier('haarcascade_smile.xml')
    topic = 'user-stream'
    savePath = STATIC_FOLDER + "images/"
    while True:
        i = imageFlush()
        arr = queue_from_faces.get()
        frame = arr[0]
        face = arr[1]
        if len(face) != 0:
            (x, y, w, h) = face 
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            roi = gray[y:y + h, x:x + w]
            smile_rects, rejectLevels, levelWeights = smile_cascade.detectMultiScale3(roi, 2.5, 20, outputRejectLevels=True)

            if len(levelWeights) == 0:
                print("Not Smiling")
            else:
                if max(levelWeights) < 2:
                    print("Not smiling")
                else:
                    print("Smiling!")
                    fileName = savePath + "frame_" + str(i) + ".jpg"
                    cv2.imwrite(fileName, frame)
                    data = {
                            'offset': time.time(),
                            'user_id': i,
                            'frame': fileName,
                        }
                    m = json.dumps(data)
                    video_producer.poll(1)
                    video_producer.produce(topic, m.encode('utf-8'), callback=receipt)
                    video_producer.flush()

def drawRectangle(frame, rect, colour):
    shapes = np.zeros_like(frame, np.uint8)
    if colour == 'white':
        col = (255,255,255)
    elif colour == 'red':
        col = (0,0,255)
    elif colour == 'blue':
        col = (255,0,0)
    elif colour == 'green':
        col = (0,255,0)

    cv2.rectangle(shapes, (rect.xmin, rect.ymin), (rect.width+rect.xmin, rect.height+rect.ymin), col, cv2.FILLED)
    alpha = 0.5
    mask = shapes.astype(bool)
    frame[mask] = cv2.addWeighted(frame, alpha, shapes, 1 - alpha, 0)[mask]

def robotRectangles(result_queue, queue_from_rectangles):

    while True:
        arr = result_queue.get()
        frame = arr[0]
        height, width, c = frame.shape
        left = Rectangle(0,0,int(width/4),height)
        drawRectangle(frame, left, 'green')

        right = Rectangle(width-int(width/4), 0, width, height)
        drawRectangle(frame, right, 'red')
        forward = Rectangle(int(width/4), 0, width-int(width/2), int(height/5))
        drawRectangle(frame, forward, 'white')

        back = Rectangle(int(width/4), height-int(height/5), width-int(width/2), int(height/5))
        drawRectangle(frame, back, 'blue')

        queue_from_rectangles.put(frame)



def cam_loop(queue_from_cam):
    cap = cv2.VideoCapture(CAMERA_FEED)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    while True:
        hello, img = cap.read()
        frame = cv2.flip(img, 1)
	#flip back if necessary by commenting out
        queue_from_cam.put(frame)

def gen_frames():

    processes = []
    print('Initializing camera...')
    manager = mp.Manager()
    queue_from_cam = manager.Queue()
    queue_from_faces = manager.Queue()
    queue_from_rectangles = manager.Queue()

    cam_process = mp.Process(target=cam_loop, args=(queue_from_cam,))
    cam_process.start()
    processes.append(cam_process)

    face_process = mp.Process(target=detectFaces, args=(queue_from_cam,queue_from_faces,))
    face_process.start()
    processes.append(face_process)
    
    smile_process = mp.Process(target=detectSmiles, args=(queue_from_faces,))
    smile_process.start()
    processes.append(smile_process)

    square_process = mp.Process(target=robotRectangles, args=(queue_from_faces,queue_from_rectangles,))
    square_process.start()
    processes.append(square_process)

    robot_process = mp.Process(target=detectOverlap, args=(queue_from_faces,))
    robot_process.start()
    processes.append(robot_process)

    while True:

        if queue_from_rectangles.empty():
            continue
        frame = queue_from_rectangles.get()
        ret, buffer = cv2.imencode('.jpg', frame)

        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


    print("Destroying process...")
    global robotProcess
    robotProcess.terminate()
    for process in processes:
        process.terminate()
        process.join()
    



@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/startRobot')
def startRobot():
    print("Starting robot connection...")
    global robotProcess
    cmd = "python3 robot_control.py"
    robotProcess = subprocess.Popen("exec " + cmd, stdout=subprocess.PIPE, shell=True)
    return "nothing"

@app.route('/stopRobot')
def stopRobot():
    global robotProcess
    robotProcess.kill()
    return "nothing"

@app.route('/')
def index():
    #robo = Robot()
    """Video streaming home page."""
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9990)
