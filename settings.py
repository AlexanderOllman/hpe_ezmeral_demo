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


#------CREDENTIALS-------

USERNAME = "hpe"

PASSWORD = "mapr"

PEM_FILE = "/opt/mapr/conf/ssl_truststore.pem"

SECURE_MODE = False

SSL_ENABLED = False

PROJECT_FOLDER = "/ezai/" # Project folder from the cluster root

ROOT_PATH = '/mapr/' + CLUSTER_NAME + '/projects' + PROJECT_FOLDER

DATA_FOLDER = ROOT_PATH + "data/" # Folder to store the data

LOG_FOLDER = ROOT_PATH + "logs/" #Folder for all logs

STATIC_FOLDER = ROOT_PATH + "static/" #Folder to store Flask static data

#--------STREAMS---------

VIDEO_STREAM = DATA_FOLDER + 'video_stream' # Stream for the face camera frame

ROBOT_STREAM = DATA_FOLDER + 'robot_stream' # Stream for the robot commands + telemetry

ROBOT_VIDEO_STREAM = DATA_FOLDER + 'robot_cam_stream' #Stream for the robot camera frame


#--------TABLES----------

STATS_TABLE = DATA_FOLDER + "stats_table" #Table for all stats appearing on Live Dashboard

ROBOT_TABLE = DATA_FOLDER "robot_table" #Table for robot telemetry data


#-------ADDRESSES--------


CAMERA_IP = '192.168.100.131'

CAMERA_FEED = 'rtsp://admin:Admin12345@'+CAMERA_IP+'/Src/MediaInput/stream_2'

#CAMERA_FEED = 0
#uncomment for webcam

ROBOT_IP = '' #Leave blank unless using Aruba/Enterprise WiFi.

PRINTER_BOOL = False #Boolean to state if you're using a printer.

PRINTER_NAME = "CANON_SELPHY_CP1300" #If true, state the name of the printer as it appears in lpstat -a
