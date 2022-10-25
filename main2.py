from flask import Flask, render_template, Response
from threading import Thread
from imutils.video import FPS
import multiprocessing as mp
import cv2
import numpy as np
from collections import namedtuple
import json
import logging
import robomasterpy
import time
from robot import Robot
Rectangle = namedtuple('Rectangle', 'xmin ymin width height')

from confluent_kafka import Producer

app = Flask(__name__)



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

VIDEO_STREAM = DATA_FOLDER + 'video_stream' # Stream for the video frame>

STATIC_FOLDER = ROOT_PATH + "static/"

ROBOT_STREAM = DATA_FOLDER + 'robot_stream'


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



def detectSmiles(queue_from_faces):
    i = 0
    video_producer = Producer({'streams.producer.default.stream': VIDEO_STREAM})
    smile_cascade = cv2.CascadeClassifier('haarcascade_smile.xml')
    topic = 'user-stream'
    savePath = STATIC_FOLDER + "images/"
    while True:
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
                    
                    if i == 20:
                        i = 0
                    else:
                        i = i + 1


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




def run_parallel(*functions):
    processes = []
    for function in functions:
        proc = mp.Process(target=function)
        proc.start()
        processes.append(proc)
    for proc in processes:
        proc.join()

def cam_loop(queue_from_cam):
    cap = cv2.VideoCapture('rtsp://admin:Admin12345@192.168.100.209/Src/MediaInput/stream_2')
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    while True:
        hello, img = cap.read()
        frame = cv2.flip(img, 1)
        queue_from_cam.put(frame)

def gen_frames():

    processes = []
    print('initializing cam')
    manager = mp.Manager()
    queue_from_cam = manager.Queue()
    queue_from_faces = manager.Queue()
    queue_from_rectangles = manager.Queue()

    cam_process = mp.Process(target=cam_loop, args=(queue_from_cam,))
    cam_process.start()
    processes.append(cam_process)

    square_process = mp.Process(target=detectFaces, args=(queue_from_cam,queue_from_faces,))
    square_process.start()
    processes.append(square_process)
    
    smile_process = mp.Process(target=detectSmiles, args=(queue_from_faces,))
    smile_process.start()
    processes.append(smile_process)

    square2_process = mp.Process(target=robotRectangles, args=(queue_from_faces,queue_from_rectangles,))
    square2_process.start()
    processes.append(square2_process)

    robot_process = mp.Process(target=detectOverlap, args=(queue_from_faces,))
    robot_process.start()
    processes.append(robot_process)

    while True:
        # frame2 = vs.read()
        # queue_from_cam.put(frame2)
        if queue_from_rectangles.empty():
            continue
        frame = queue_from_rectangles.get()
        ret, buffer = cv2.imencode('.jpg', frame)

        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result


    print("Destroying process...")
    for process in processes:
        process.terminate()
        process.join()



@app.route('/video_feed')
def video_feed():
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/')
def index():
    #robo = Robot()
    """Video streaming home page."""
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9990)
