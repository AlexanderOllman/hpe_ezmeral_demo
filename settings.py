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

ROBOT_VIDEO_STREAM = DATA_FOLDER + 'robot_cam_stream'

CAMERA_IP = '192.168.100.131'

CAMERA_FEED = 'rtsp://admin:Admin12345@'+CAMERA_IP+'/Src/MediaInput/stream_2'

#CAMERA_FEED = 0
#uncomment for webcam

ROBOT_IP = '192.168.100.138'

PRINTER_NAME = "CANON_SELPHY_CP1300"
