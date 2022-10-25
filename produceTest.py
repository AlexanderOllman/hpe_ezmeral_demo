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

ROBOT_STREAM = DATA_FOLDER + 'robot_stream' # Stream for the video frame>


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
    
    while True:
        controlRobot("f")
main()
