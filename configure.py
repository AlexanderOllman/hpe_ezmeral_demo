import fileinput
import os
import settings
import time
import subprocess
from mapr.ojai.storage.ConnectionFactory import ConnectionFactory

print("Starting checks... ")

#/opt/mapr/bin/maprcli volume create -name p1 -path /p1
def volume_create(volume_name, volume_path, mount=True):
    print("creating Volume: "+'maprcli volume create -name ' + volume_name + ' -path ' + volume_path)
    os.system('maprcli volume create -name ' + volume_name + ' -path ' + volume_path)
    if mount:
        time.sleep(2)
        volume_mount(volume_name, volume_path)
  
def volume_mount(volume_name, volume_path):
    print("mounting Volume: "+'maprcli volume mount -name ' + volume_name + ' -path ' + volume_path)
    os.system('maprcli volume mount -name ' + volume_name + ' -path ' + volume_path)

# Create folders and Volumes
# at this time there is a bug and only MapR user can mount volumes. This should have been done as per the guide.

if not os.path.exists(settings.PROJECTS):
    print("ERROR: " + settings.PROJECTS + " not found. Create " + settings.PROJECTS + " volume in Data Fabric. Run the command as provided in the documentation.")
    exit(1)
  #volume_create('projects_volume',settings.BASE_PROJECTS)

if not os.path.exists(settings.ROOT_PATH):
    os.makedirs(settings.ROOT_PATH)
    print("Root Project directory created " + settings.ROOT_PATH)

print("cleaning data folder")
os.system("rm -rf " + settings.DATA_FOLDER)

if not os.path.exists(settings.DATA_FOLDER):
    os.makedirs(settings.DATA_FOLDER)
print("Data directory created " + settings.DATA_FOLDER)

if not os.path.exists(settings.RECORDING_FOLDER):
    os.makedirs(settings.RECORDING_FOLDER)
print("Recording directory created " + settings.RECORDING_FOLDER)

print("cleaning log folder")
os.system("rm -rf " + settings.LOG_FOLDER)
if not os.path.exists(settings.LOG_FOLDER):
    os.makedirs(settings.LOG_FOLDER)
print("Log directory created " + settings.LOG_FOLDER)

# Create streams
print("Creating Ezmeral Data streams ...")

def create_stream(stream_path):
    if not os.path.islink(stream_path):
        print("creating stream: "+'maprcli stream create -path ' + stream_path + ' -produceperm p -consumeperm p -topicperm p -copyperm p -adminperm p')
        os.system('maprcli stream create -path ' + stream_path + ' -produceperm p -consumeperm p -topicperm p -copyperm p -adminperm p')
        
def create_topic(stream_path, topic_name):
    if not os.path.islink(stream_path):
        print("Stream does not exist!")
    else:
        os.system('maprcli stream topic create -path ' + stream_path + '-topic '+topic_name)

def create_and_get_table(connection, table_path):
    if connection.is_store_exists(table_path):
        data_store = connection.get_store(table_path)
    else:
        data_store = connection.create_store(table_path)
    return data_store

os.system("rm -rf " + settings.ROBOT_VIDEO_STREAM)
create_stream(settings.ROBOT_VIDEO_STREAM)
create_topic(settings.ROBOT_VIDEO_STREAM, 'video_feed')
print("Robot Video Stream created " + settings.ROBOT_VIDEO_STREAM)

os.system("rm -rf " + settings.ROBOT_STREAM)
create_stream(settings.ROBOT_STREAM)
create_topic(settings.ROBOT_STREAM, 'command')
print("Robot Control Stream created" + settings.ROBOT_STREAM)

os.system("rm -rf " + settings.VIDEO_STREAM)
create_stream(settings.VIDEO_STREAM)
create_topic(settings.ROBOT_VIDEO_STREAM, 'user_stream')
print("Video Stream created " + settings.VIDEO_STREAM)


print("Initializing Ezmeral Data Fabric Tables...")
os.system("rm -rf " + settings.ROBOT_TABLE)
ROBOT_TABLE = settings.ROBOT_TABLE
STATS_TABLE = settings.STATS_TABLE
CLUSTER_IP = settings.CLUSTER_IP
CLUSTER_NAME = settings.CLUSTER_NAME
SECURE_MODE = settings.SECURE_MODE
SSL_ENABLED = settings.SSL_ENABLED
username = settings.USERNAME
password = settings.PASSWORD
PEM_FILE = settings.PEM_FILE



# Initialize databases

if SSL_ENABLED:
    print("using ssl connection")
    connection_str = "{}:5678?auth=basic;" \
                           "ssl=true;" \
                           "sslCA={};" \
                           "sslTargetNameOverride={};" \
                           "user={};" \
                           "password={}".format(CLUSTER_IP,PEM_FILE,CLUSTER_IP,username,password)
else:
    connection_str = "{}:5678?auth=basic;user={};password={};ssl=false".format(CLUSTER_IP,username,password)

connection = ConnectionFactory.get_connection(connection_str=connection_str)

#delete table tables with posix
print("removing old Stats Table: " + settings.STATS_TABLE)
os.system("rm -rf " + settings.STATS_TABLE)

#create tables with data fabric ojai rpc call
stats_table = create_and_get_table(connection, settings.STATS_TABLE)
print("Stats Table created " + settings.STATS_TABLE)

print("Creating data entries for Stats table")
document = {"_id":1,
              "faces":0,
              "smiles":0,
              "goals":0,
              "participants": 0
             }

new_document = connection.new_document(dictionary=document)
stats_table.insert_or_replace(new_document)
print(new_document.as_json_str())
    
controls_table = create_and_get_table(connection, settings.ROBOT_TABLE)
print("CONTROLS_TABLE table created " + settings.ROBOT_TABLE )

try:
  # Create home_base if doesn't exist
    document = {"_id":1,
              "x":0,
              "y":0,
              "z":0
             }
    new_document = connection.new_document(dictionary=document)
    controls_table.insert_or_replace(new_document)
    print(new_document.as_json_str())
except:
    pass

print("Updating init file...")
os.system("sed -i 's/my\.cluster\.com/{}/g' init.sh".format(CLUSTER_NAME))
os.system("sed -i 's/my\.cluster\.com/{}/g' clean.sh".format(CLUSTER_NAME))

print("Updating application folder: cp -rfu ./* " + settings.ROOT_PATH )
os.system("cp -rfu ./* " + settings.ROOT_PATH)


print("Configuration complete. Initialize environment variables with source init.sh as hpe user, then run the aplication using python3 main.py or cloud_dash.py")
