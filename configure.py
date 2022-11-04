import fileinput
import os
import settings
import time
import subprocess
from mapr.ojai.storage.ConnectionFactory import ConnectionFactory

print("Starting pre-flight checks ... ")

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
# at this time there is a bug and only MapR user can mount volumes
if not os.path.exists(settings.PROJECTS):
  print("ERROR: " + settings.PROJECTS + " not found. Create " + settings.PROJECTS + " volume in Data Fabric")
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

def create_and_get_table(connection, table_path):
  if connection.is_store_exists(table_path):
    data_store = connection.get_store(table_path)
  else:
    data_store = connection.create_store(table_path)
  return data_store

os.system("rm -rf " + settings.POSITIONS_STREAM)
print("removing any existing data at stream location " + settings.POSITIONS_STREAM)
create_stream(settings.BASE_POSITIONS_STREAM)
print("Positions stream created " + settings.POSITIONS_STREAM )
os.system("rm -rf " + settings.PROCESSORS_STREAM)
create_stream(settings.BASE_PROCESSORS_STREAM)
print("Processors stream created" + settings.PROCESSORS_STREAM)
os.system("rm -rf " + settings.VIDEO_STREAM)
create_stream(settings.BASE_VIDEO_STREAM)
print("Video stream created " + settings.VIDEO_STREAM)
os.system("rm -rf " + settings.RECORDING_STREAM)
create_stream(settings.BASE_RECORDING_STREAM)
print("Recording stream created " + settings.RECORDING_STREAM)


print("initializing Ezmeral Data Fabric Tables for drones")
os.system("rm -rf " + settings.DRONEDATA_TABLE)
DRONEDATA_TABLE = settings.DRONEDATA_TABLE
BASE_DRONEDATA_TABLE = settings.BASE_DRONEDATA_TABLE
ZONES_TABLE = settings.ZONES_TABLE
BASE_ZONES_TABLE = settings.BASE_ZONES_TABLE
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
print("removing old dronedata table: " + settings.DRONEDATA_TABLE)
os.system("rm -rf " + settings.DRONEDATA_TABLE)

#create tables with data fabric ojai rpc call
dronedata_table = create_and_get_table(connection, settings.BASE_DRONEDATA_TABLE)
print("DRONEDATA_TABLE table created " + settings.DRONEDATA_TABLE )
controls_table = create_and_get_table(connection, settings.BASE_CONTROLS_TABLE)
print("CONTROLS_TABLE table created " + settings.CONTROLS_TABLE )
controls_table = create_and_get_table(connection, settings.BASE_PROCESSORS_TABLE)
print("PROCESSORS_TABLE table created " + settings.PROCESSORS_TABLE )

print("creating data entries for DRONE_ID's drone_1, drone_2, and drone_3")
for DRONE_ID in ["drone_1","drone_2","drone_3"]:
    document ={"_id": DRONE_ID,
                    "flight_data":{
                                    "battery":50,
                                    "fly_speed":5.0
                                   },
                    "log_data":"unset",
                    "count":0,
                    "connection_status":"disconnected",
                    "position": {
                                   "zone":"home_base", 
                                   "status":"landed",
                                   "offset":0.0
                                }
                   }

    new_document = connection.new_document(dictionary=document)
    dronedata_table.insert_or_replace(new_document)
    print(new_document.as_json_str())
    
print("removing old zones table: " + settings.ZONES_TABLE)
os.system("rm -rf " + settings.ZONES_TABLE)

zones_table = create_and_get_table(connection, BASE_ZONES_TABLE)
print("creating ezmeral table for drone zone assignmnets at " + settings.ZONES_TABLE)
try:
  # Create home_base if doesn't exist
  document = {"_id":"home_base",
              "height":"10",
              "left":"45",
              "top":"45",
              "width":"10",
              "x":"0",
              "y":"0"
             }
  new_document = connection.new_document(dictionary=document)
  zones_table.insert_or_replace(new_document)
  print(new_document.as_json_str())
except:
  pass

print("updating init file")
os.system("sed -i 's/my\.cluster\.com/{}/g' init.sh".format(CLUSTER_NAME))
os.system("sed -i 's/my\.cluster\.com/{}/g' clean.sh".format(CLUSTER_NAME))

print("update application folder: cp -rfu ./* " + settings.ROOT_PATH )
os.system("cp -rfu ./* " + settings.ROOT_PATH)


print("Configuration complete, initialize environment variables with source init.sh then run the aplication using start.py")
