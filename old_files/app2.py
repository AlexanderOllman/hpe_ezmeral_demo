

from confluent_kafka import Producer
import json
import logging
import random

from flask import Flask, render_template, Response
from threading import Thread
from imutils.video import FPS
import multiprocessing

import cv2
import numpy as np
from collections import namedtuple
import robomasterpy
import time
from robot import Robot
Rectangle = namedtuple('Rectangle', 'xmin ymin width height')

#from camera import IPCamera
app = Flask(__name__)


# use 0 for web camera
#  for cctv camera use rtsp://username:password@ip_address:554/user=username_password='password'_channel=channel_number_stream=0.sdp' instead of camera
# for local webcam use cv2.VideoCapture(0)

class WebcamVideoStream:
    def __init__(self, src=0):
        # initialize the video camera stream and read the first frame
        # from the stream
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.width = self.stream.get(3)
        self.height = self.stream.get(4)
        (self.grabbed, self.frame) = self.stream.read()
        # initialize the variable used to indicate if the thread should
        # be stopped
        self.stopped = False

    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self


    def update(self):
        # keep looping infinitely until the thread is stopped
        while True:
            # if the thread indicator variable is set, stop the thread
            if self.stopped:
                return
            # otherwise, read the next frame from the stream
            (self.grabbed, self.frame) = self.stream.read()


    def read(self):
        # return the frame most recently read
        return self.frame


    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True



logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='producer.log',
                    filemode='w')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

vs = WebcamVideoStream(src='rtsp://admin:Admin12345@192.168.100.131/Src/MediaInput/stream_2').start()
frame = vs.read()
faceRecognition = faceProcessing(frame).start() 
smileRecognition = smileProcessing().start()


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

video_producer = Producer({'streams.producer.default.stream': VIDEO_STREAM})
robot_producer = Producer({'streams.producer.default.stream': ROBOT_STREAM})

print('Kafka Producer has been initiated...')

def receipt(err,msg):
    if err is not None:
        print('Error: {}'.format(err))
    else:
        message = 'Produced message on topic {} with value of {}\n'.format(msg.topic(), msg.value().decode('utf-8'))
        logger.info(message)
        print(message)



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

def produceMessage(stream, topic, message):
    m = json.dumps(message)
    stream.poll(1)
    stream.produce(topic, m.encode('utf-8'), callback=receipt)
    stream.flush()


def multi_process():
    print("Video processing using {} processes...".format(num_processes))
    start_time = time.time()

    # Paralle the execution of a function across multiple input values
    p = mp.Pool(num_processes)
    p.map(process_video_multiprocessing, range(num_processes))

    combine_output_files(num_processes)

    end_time = time.time()

    total_processing_time = end_time - start_time
    print("Time taken: {}".format(total_processing_time))
    print("FPS : {}".format(frame_count/total_processing_time))


class imageObject:

    def __init__():
        self.frame = None
        self.rectangles = False
        self.face = False
        self.smile = False




def getFrame():
    frame = vs.read()
    return frame

def drawRectangle():
    #check with object state if already done



def gen_frames():  

    global frame

    ret, buffer = cv2.imencode('.jpg', frame)

    frame = buffer.tobytes()
    yield (b'--frame\r\n'
           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
        

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
