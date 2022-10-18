from confluent_kafka import Producer
import json
import time
import logging
import random 
import cv2

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

VIDEO_STREAM = DATA_FOLDER + 'video_stream' # Stream for the video frame>

p = Producer({'streams.producer.default.stream': VIDEO_STREAM})

print('Kafka Producer has been initiated...')

def receipt(err,msg):
    if err is not None:
        print('Error: {}'.format(err))
    else:
        message = 'Produced message on topic {} with value of {}\n'.format(msg.topic(), msg.value().decode('utf-8'))
        logger.info(message)
        print(message)






def main():
    i = 0
    capture = cv2.VideoCapture('rtsp://admin:Admin12345@192.168.100.131/Src/MediaInput/stream_2')
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    while True:
        ret, frame = capture.read()
        savePath = DATA_FOLDER + "images/drone_2/"
        fileName = savePath + "frame"+ str(i)+".jpg"
        cv2.imwrite(fileName, frame)
        data={
                'offset':time.time(),
                'user_id': i,
                'frame': fileName,
           }
        m=json.dumps(data)
        p.poll(1)
        p.produce('user-tracker', m.encode('utf-8'),callback=receipt)
        p.flush()
        i = i + 1
        if i == 999:
            i = 0

    capture.release()
main()
