#! /usr/bin/python

"""
Pilot application for TEITS demo

What it does :
- Connects to the drone
- Gets the video
- Stores each frame in a folder
- Stores frame indexes in a stream (video_stream) in a topic named with drone id
- reads movements instructions from a stream

What has to be defined :
- the drone ID
- FPS for the transmitted video
- the project folder on the cluster

TODO: Things to add
get_alt_limit
set_alt_limit(self, limit):
get_att_limit
set_att_limit(self, limit)


"""

import traceback
import time
from time import sleep
import os
import sys
try:
    import av
except:
    pass
import tellopy
import json
import threading
from random import randint
from confluent_kafka import Producer, Consumer, KafkaError
from mapr.ojai.storage.ConnectionFactory import ConnectionFactory
from math import atan2, sqrt, pi, floor
from shutil import copyfile
import base64
from io import BytesIO
import logging
import base64
import numpy as np

import settings

DRONE_ID = sys.argv[1]


logging.basicConfig(filename=settings.LOG_FOLDER + "pilot_{}.log".format(DRONE_ID),
                    level=logging.INFO,
                    format='%(asctime)s :: %(levelname)s :: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger()
logger.setLevel(settings.LOG_LEVEL)

KILL_ALL = False

# Remote mode sends data through a remote MaprDB buffer instead of writing directly to the FS
REMOTE_MODE = settings.REMOTE_MODE


logging.info("Remote mode : {}".format(REMOTE_MODE))


def get_cluster_name():
  with open('/opt/mapr/conf/mapr-clusters.conf', 'r') as f:
    first_line = f.readline()
    return first_line.split(' ')[0]

def get_cluster_ip():
  with open('/opt/mapr/conf/mapr-clusters.conf', 'r') as f:
    first_line = f.readline()
    return first_line.split(' ')[2].split(':')[0]

def check_stream(stream_path):
  if not os.path.islink(stream_path):
    logging.info("stream {} is missing. Exiting.".format(stream_path))
    sys.exit()

def create_and_get_table(connection, table_path):
  #if not os.path.islink(table_path):
  #maprcli table create -path <path> -tabletype json
    #print("creating table: "+'maprcli table create -path ' + table_path + ' -tabletype json')
    #os.system('maprcli table create -path ' + table_path + ' -tabletype json')
  if connection.is_store_exists(table_path):
    data_store = connection.get_store(table_path)
  else:
    data_store = connection.create_store(table_path)
  return data_store

STREAM_FPS = settings.STREAM_FPS
REPLAYER_FPS = settings.REPLAYER_FPS
PROJECT_FOLDER = settings.PROJECT_FOLDER




# Wait ratios
FORWARD_COEF = settings.FORWARD_COEF # Time taken to move 1m
ANGULAR_COEF = settings.ANGULAR_COEF # Time taken to rotate 360 deg

DRONE_MODE = settings.DRONE_MODE
NO_FLIGHT = settings.NO_FLIGHT 
DIRECTIONAL_MODE = settings.DIRECTIONAL_MODE
DEFAULT_DISTANCE = settings.DEFAULT_DISTANCE
ROTATION_SPEED = settings.ROTATION_SPEED

#STR_DEFAULT_DISTANCE = string_value(DEFAULT_DISTANCE)

 
CLUSTER_NAME = get_cluster_name()
CLUSTER_IP = get_cluster_ip()

ROOT_PATH = settings.ROOT_PATH
DATA_FOLDER = settings.DATA_FOLDER
IMAGE_FOLDER = DATA_FOLDER + "images/" + DRONE_ID + "/source/"
VIDEO_STREAM = settings.VIDEO_STREAM
POSITIONS_STREAM = settings.POSITIONS_STREAM
DRONEDATA_TABLE = settings.DRONEDATA_TABLE
ZONES_TABLE = settings.ZONES_TABLE
CONTROLS_TABLE = settings.CONTROLS_TABLE
RECORDING_FOLDER = settings.RECORDING_FOLDER

BUFFER_TABLE = DATA_FOLDER + "{}_buffer".format(DRONE_ID)
BASE_BUFFER_TABLE = settings.BASE_DATA_FOLDER + "{}_buffer".format(DRONE_ID)


current_angle = 0.0


time_tracker = {"min":1000,"max":0,"count":0,"avg":0}


SECURE_MODE = settings.SECURE_MODE
username = settings.USERNAME
password = settings.PASSWORD
PEM_FILE = settings.PEM_FILE


# Initialize databases
if SECURE_MODE:
  connection_str = "{}:5678?auth=basic;" \
                           "user={};" \
                           "password={};" \
                           "ssl=true;" \
                           "sslCA={};" \
                           "sslTargetNameOverride={}".format(CLUSTER_IP,username,password,PEM_FILE,CLUSTER_IP)
else:
  connection_str = "{}:5678?auth=basic;user={};password={};ssl=false".format(CLUSTER_IP,username,password)# Create database connection

connection = ConnectionFactory().get_connection(connection_str=connection_str)
zones_table = create_and_get_table(connection, settings.BASE_ZONES_TABLE)

# initialize drone data
dronedata_table = create_and_get_table(connection, settings.BASE_DRONEDATA_TABLE)
dronedata_table.insert_or_replace({"_id":DRONE_ID,
                                   "status":"ready",
                                   "last_command":"land",
                                   "flight_data":{"battery":50,"fly_speed":5.0},
                                   "log_data":"unset",
                                   "count":0,
                                   "connection_status":"disconnected",
                                   "position": {"zone":"home_base", "status":"landed","offset":0.0}})

# initialize drone controls
controls_table = create_and_get_table(connection, settings.BASE_CONTROLS_TABLE)
#controls_table = connection.get_or_create_store(CONTROLS_TABLE)
controls_table.insert_or_replace({"_id":DRONE_ID,
                                   "pressed_keys":[]})


buffer_table = create_and_get_table(connection, BASE_BUFFER_TABLE)

# test if folders exist and create them if needed
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# create sreams if needed
check_stream(VIDEO_STREAM)
check_stream(POSITIONS_STREAM)





#######################    INTERACTIVE DRONE CONTROL    ##################
# Function polls an instruction DB to get the current control keys and send the commands to the drone

controls = {
    'left': lambda drone, speed: drone.left(speed),
    'right': lambda drone, speed: drone.right(speed),
    'forward': lambda drone, speed: drone.forward(speed),
    'backward': lambda drone, speed: drone.backward(speed),
    'flip': lambda drone, speed: drone.flip_back(),
    'clockwise': lambda drone, speed: drone.clockwise(speed),
    'counter_clockwise': lambda drone, speed: drone.counter_clockwise(speed),
    'up': lambda drone, speed: drone.up(speed),
    'down': lambda drone, speed: drone.down(speed),
    'takeoff': lambda drone, speed: drone.takeoff(),
    'land': lambda drone, speed: drone.land(),
}


def interactive_control(drone):
    print("interactive control thread started")
    speed = 100
    try:
        prev_pk = []
        while True:
            time.sleep(0.05)
            
            if drone.state == drone.STATE_CONNECTED:
                dronedata_table.update(_id=DRONE_ID,mutation={"$put":{'connection_status':"connected"}})
            else:
                dronedata_table.update(_id=DRONE_ID,mutation={"$put":{'connection_status':"disconnected"}})

            pressed_keys = controls_table.find_by_id(DRONE_ID)["pressed_keys"]
            if set(pressed_keys) != set(prev_pk):
                keys_up = []
                for key in prev_pk:
                    if not key in pressed_keys:
                        keys_up.append(key)
                keys_down = []
                for key in pressed_keys:
                    if not key in prev_pk:
                        keys_down.append(key)
                prev_pk = pressed_keys
                print("Pressed keys : {}".format(pressed_keys))
                print("Down : {}".format(keys_down))
                print("Up : {}".format(keys_up))

                for key in keys_up:
                    controls[key](drone, 0)
                for key in keys_down:
                    controls[key](drone,speed)

    except Exception as ex:
        logging.exception("interactive control failed")






#######################    VIDEO PROCESSING    ##################

# Function for transfering the video frames to FS and Stream
def get_drone_video(drone):

    logging.info("Getting video from drone")

    global STREAM_FPS
    global DRONE_ID
    global VIDEO_STREAM
    global IMAGE_FOLDER
    global REMOTE_MODE

    logging.info("producing video stream into {}".format(VIDEO_STREAM))

    video_producer = Producer({'streams.producer.default.stream': VIDEO_STREAM})

    current_sec = 0
    last_frame_time = 0
    container = av.open(drone.get_video_stream())
    i = 0
    try:
        start_time = time.time()
        received_frames = 0
        sent_frames = 0
        # first_pass = True
        while True:
            try:
                i = 0
                try:
                    logging.info("start decode")
                    for frame in container.decode(video=0):
                        # skip first 400 frames
                        i = i + 1
                        if i < 300:
                            continue
                        received_frames += 1
                        current_time = time.time()
                        if current_time > (last_frame_time + float(1/STREAM_FPS)):
                            start_processing_time = time.time()
                            index = frame.index
                            new_image = IMAGE_FOLDER + "frame-{}.jpg".format(index)
                            try:
                                if REMOTE_MODE:
                                    memfile = BytesIO()
                                    frame.to_image().save(memfile,format="JPEG",width=480,height=270)
                                    image_bytes = base64.b64encode(memfile.getvalue())
                                    json_dict = {"_id":"{}".format(index),
                                                "image_name":new_image,
                                                "image_bytes":image_bytes}
                                    buffer_table.insert_or_replace(json_dict)
                                else:
                                    logging.info("saving {}".format(index))
                                    frame.to_image().save(new_image)
                                    video_producer.produce(DRONE_ID + "_source", json.dumps({"drone_id":DRONE_ID,
                                                                                             "index":index,
                                                                                             "image":new_image}))
                            except Exception as ex:
                                logging.exception("image save failed")

                            sent_frames += 1
                            last_frame_time = time.time()
                            duration = last_frame_time - start_processing_time
                            time_tracker["min"] = min(time_tracker["min"],duration)
                            time_tracker["max"] = max(time_tracker["max"],duration)
                            time_tracker["count"] += 1
                            time_tracker["avg"] = (time_tracker["avg"] * (time_tracker["count"] - 1) + duration) / time_tracker["count"]


                        # Print stats every second
                        elapsed_time = time.time() - start_time
                        if int(elapsed_time) != current_sec:
                            logging.info("Elapsed : {} s, received {} fps , sent {} fps".format(int(elapsed_time),received_frames,sent_frames))
                            logging.info("Time tracker : {} ".format(time_tracker))
                            received_frames = 0
                            sent_frames = 0
                            current_sec = int(elapsed_time)
                except:
                    time.sleep(2)
                    # container = av.open(drone.get_video_stream())
                    i=0
                    pass
            except:
                logging.exception("fails")

    # Catch exceptions
    except Exception:
        traceback.print_exc()



def play_video_from_file(): # file name has to be "zone_name.mp4"
    global DRONE_ID
    global VIDEO_STREAM
    global IMAGE_FOLDER
    global KILL_ALL
    global STREAM_FPS

    logging.info("producing into {}".format(VIDEO_STREAM))
    if not REMOTE_MODE :
        video_producer = Producer({'streams.producer.default.stream': VIDEO_STREAM})
    current_sec = 0
    last_frame_time = 0

    try:
        start_time = time.time()
        received_frames = 0
        sent_frames = 0
        while not KILL_ALL:
            try:
                stream_zone = dronedata_table.find_by_id(DRONE_ID)["position"]["zone"]
                zone_video = RECORDING_FOLDER + stream_zone + ".mp4"
                logging.info("playing {} ".format(zone_video))
                container = av.open(zone_video)
                
                for frame in container.decode(video=0):
                    if KILL_ALL:
                        break
                    received_frames += 1
                    current_time = time.time()
                    if current_time > (last_frame_time + float(1/STREAM_FPS)):
                        begin_process = time.time()
                        index = frame.index
                        new_image = IMAGE_FOLDER + "frame-{}.jpg".format(index)
                        try:
                            if REMOTE_MODE:
                                frame_format = frame.format.name
                                ndarray = frame.to_ndarray(width=640,height=360)
                                data_type = ndarray.dtype.name
                                shape = ndarray.shape
                                enc_bytes = ndarray.tobytes()
                                enc_str = base64.b64encode(enc_bytes)
                                buffer_table.insert_or_replace({"_id":"{}".format(index),
                                                                "image_name":new_image,
                                                                "image_bytes":enc_str,
                                                                "shape_0":shape[0],
                                                                "shape_1":shape[1],
                                                                "data_type":data_type,
                                                                "format":frame_format})

                            else:
                                video_producer.produce(DRONE_ID+"_source", json.dumps({"drone_id":DRONE_ID,
                                                                                    "index":index,
                                                                                    "image":new_image}))
                                frame.to_image().save(new_image)
                        except Exception as ex:
                            logging.exception("failed")
                        sent_frames += 1
                        last_frame_time = time.time()
                        end_process = time.time()
                        duration = end_process - begin_process
                        time_tracker["min"] = min(time_tracker["min"],duration)
                        time_tracker["max"] = max(time_tracker["max"],duration)
                        time_tracker["count"] += 1
                        time_tracker["avg"] = (time_tracker["avg"] * (time_tracker["count"] - 1) + duration) / time_tracker["count"]


                        current_zone = dronedata_table.find_by_id(DRONE_ID)["position"]["zone"]
                        if current_zone != stream_zone:
                            stream_zone = current_zone
                            zone_video = RECORDING_FOLDER + stream_zone + ".mp4"
                            container = av.open(zone_video)
                            logging.info("playing {} ".format(zone_video))
                            break

                    # Print stats every second
                    elapsed_time = time.time() - start_time
                    if int(elapsed_time) != current_sec:
                        logging.info("Elapsed : {} s, received {} fps , sent {} fps".format(int(elapsed_time),received_frames,sent_frames))
                        logging.info("Time tracker : {} ".format(time_tracker))
                        time_tracker["min"] = 100
                        time_tracker["max"] = 0
                        received_frames = 0
                        sent_frames = 0
                        current_sec = int(elapsed_time)

                    time.sleep(1/REPLAYER_FPS)

            except KeyboardInterrupt:
                break

            except Exception:
                traceback.print_exc()
                continue

    # Catch exceptions
    except Exception:
        traceback.print_exc()



#######################    MOVE PROCESSING    ##################

def move_to_zone(drone,start_zone,drop_zone):


    global current_angle

    try:

        logging.info("...   moving from {} to {}".format(start_zone,drop_zone))
        # get start_zone coordinates
        current_position_document = zones_table.find_by_id(start_zone)
        current_position = (float(current_position_document["x"]),float(current_position_document["y"]))
        # get drop_zone coordinates
        new_position_document = zones_table.find_by_id(drop_zone)
        new_position = (float(new_position_document["x"]),float(new_position_document["y"]))

        # calcul du deplacement
        y = new_position[1] - current_position[1] # Back and Front
        x = new_position[0] - current_position[0] # Left and Right

        # distance a parcourir
        distance = sqrt(x*x + y*y)
        offset = 0

        if DIRECTIONAL_MODE == "DIRECT" :
            command = "go {} {} 0 100".format(y*100,x*100)
            mutation = {"$put":{"last_command":command}}
            drone.custom_command(command)
            time.sleep(max(1,distance * FORWARD_COEF))

        if DIRECTIONAL_MODE == "LINEAR" :
            if y > 0:
                drone.forward_d(y)
            elif y < 0:
                drone.backward_d(-y)
            if y != 0:
                logging.info("Sleep {}".format(abs(FORWARD_COEF*y)))
                time.sleep(max(1,abs(FORWARD_COEF*y)))

            if x > 0:
                drone.right_d(x)
            elif x < 0:
                drone.left_d(-x)
            if x != 0:
                logging.info("Sleep {}".format(abs(FORWARD_COEF*x)))
                time.sleep(max(1,abs(FORWARD_COEF*x)))
        else:
            # calcul angle de rotation vs axe Y   
            target_angle = (atan2(x,y)*180/pi + 180) % 360 - 180

            logging.info("drone orientation : {}".format(current_angle))
            logging.info("target angle : {}".format(target_angle))

            angle =  (target_angle - current_angle + 180) % 360 - 180 
            logging.info("direction vs drone : {}".format(angle))

            if DIRECTIONAL_MODE == "OPTIMIZED":
                # calcul du cadran
                cadran = int(floor(angle/45))
                logging.info("cadran = {}".format(cadran))

                # calcul offset et deplacement
                if cadran in [-1,0]:
                    offset = angle
                    move = drone.forward_d
                elif cadran in [1,2]:
                    offset = angle - 90
                    move = drone.right_d
                elif cadran in [-4,3]:
                    offset = (angle + 90) % 180 - 90
                    move = drone.backward_d
                elif cadran in [-2,-3]:
                    offset = angle + 90
                    move = drone.left_d

                logging.info("offset : {}".format(offset))
                logging.info("move : {}".format(move))

            elif DIRECTIONAL_MODE == "FORWARD":
                move = drone.forward_d
                offset = angle 
                logging.info("forward mode, offset : {}".format(offset))

            

            logging.info("distance : {}".format(distance))

            if abs(offset) > 0:
                logging.info("###############      turning {} degrees".format(angle))
                drone.turn(offset)
                logging.info("sleep {}".format(max(1,float(abs(offset) * ANGULAR_COEF / 360))))
                time.sleep(max(1,float(abs(offset) * ANGULAR_COEF / 360)))

            # deplacement        
            if distance > 0 :
                move(distance)
                logging.info("sleep {}".format(max(1,distance * FORWARD_COEF)))
                time.sleep(max(1,distance * FORWARD_COEF))

            current_angle += offset
    except:
        traceback.print_exc()
        logging.exception("fails")

        drone.land()
        time.sleep(1)
        sys.exit()


def set_homebase():
    dronedata_table.update(_id=DRONE_ID,mutation={"$put": {"position": {"zone":"home_base", "status":"landed","offset":current_angle}}})
    logging.info("Drone position reset to homebase")



#######################    FLIGHT DATA  PROCESSING    ##################

def handler(event, sender, data, **args):
    drone = sender

    if event is drone.EVENT_FLIGHT_DATA:
        fly_speed = sqrt(data.north_speed*data.north_speed + data.east_speed*data.east_speed);
        flight_data_doc = {"battery":str(data.battery_percentage),
                           "fly_speed":str(data.fly_speed),
                           "wifi_strength":str(data.wifi_strength)}
        mutation = {"$put": {'flight_data': flight_data_doc}}
        try:
            dronedata_table.update(_id=DRONE_ID,mutation=mutation)
        except Exception as ex:
            logging.exception("fails")

            if "EXPIRED" in str(ex):
                logging.info("EXPIRED")


    if event is drone.EVENT_LOG:
        log_data_doc = {"mvo":{"vel_x":data.mvo.vel_x,
                               "vel_y":data.mvo.vel_y,
                               "vel_z":data.mvo.vel_z,
                               "pos_x":data.mvo.pos_x,
                               "pos_y":data.mvo.pos_y,
                               "pos_z":data.mvo.pos_z},
                        "imu":{"acc_x":data.imu.acc_x,
                               "acc_y":data.imu.acc_y,
                               "acc_z":data.imu.acc_z,
                               "gyro_x":data.imu.gyro_x,
                               "gyro_y":data.imu.gyro_y,
                               "gyro_z":data.imu.gyro_z}}
        mutation = {"$put": {'log_data': log_data_doc}}
        dronedata_table.update(_id=DRONE_ID,mutation=mutation)





#######################       MAIN FUNCTION       ##################

def main():

    logging.info("Pilot started for {}".format(DRONE_ID))

    global current_angle
    global KILL_ALL

    set_homebase() # reset drone position in the positions table

    drone_number = int(DRONE_ID.split('_')[1])
    
    if settings.DRONE_MODE  == "live":
        drone = tellopy.Tello()
    else:
        drone = tellopy.Tello(port=9000+drone_number)

    if DRONE_MODE == "live":
        drone.subscribe(drone.EVENT_FLIGHT_DATA, handler)
        drone.connect()
        drone.wait_for_connection(600)

    dronedata_table.update(_id=DRONE_ID,mutation={"$put":{'connection_status':"connected"}})

    # create video thread
    if DRONE_MODE == "video":
        videoThread = threading.Thread(target=play_video_from_file)
    elif DRONE_MODE == "live":
        #drone.start_video()
        videoThread = threading.Thread(target=get_drone_video,args=[drone])

    videoThread.start()


    livePilotThread = threading.Thread(target=interactive_control,args=[drone])
    livePilotThread.start()

    start_time = time.time()
    consumer_group = DRONE_ID + str(time.time())
    positions_consumer = Consumer({'group.id': consumer_group,'default.topic.config': {'auto.offset.reset':'latest'}})
    positions_consumer.subscribe([POSITIONS_STREAM + ":" + DRONE_ID])

    while True:
        try:
            logging.info("polling {}")
            msg = positions_consumer.poll(timeout=1)
            if msg is None:
                continue

            # Proceses moving instructions
            if not msg.error():

                json_msg = json.loads(msg.value().decode('utf-8'))
                logging.info("new message : {}".format(json_msg))

                if "action" in json_msg:
                    action = json_msg["action"]
                    if action == "takeoff":
                        logging.info("....................................................  Takeoff")
                        mutation = {"$put":{"status":"busy"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        mutation = {"$put":{"last_command":"takeoff"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        if DRONE_MODE == "live" and not NO_FLIGHT:
                            drone.takeoff()
                            time.sleep(8)
                            drone.up(1)
                        mutation = {"$put":{"position.status":"flying"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        mutation = {"$put":{"status":"waiting"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)

                    if action == "land":
                        logging.info("....................................................  Land")
                        mutation = {"$put":{"status":"busy"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        mutation = {"$put":{"last_command":"land"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        if DRONE_MODE == "live" and not NO_FLIGHT:
                            drone.land()
                        mutation = {"$put":{"position.status":"landed"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        mutation = {"$put":{"status":"waiting"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)  
                        
                    if action == "down":
                        print("....................................................  Moving Down")
                        logging.info("....................................................  Moving Down")
                        mutation = {"$put":{"status":"busy"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        mutation = {"$put":{"last_command":"down"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        if DRONE_MODE == "live" and not NO_FLIGHT:
                            drone.down_d(DEFAULT_DISTANCE)
                        mutation = {"$put":{"position.status":"lowered"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        mutation = {"$put":{"status":"waiting"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        
                    if action == "counterclockwise":
                        print("....................................................  Moving counter clockwise")
                        logging.info("....................................................  Moving counter clockwise")
                        mutation = {"$put":{"status":"busy"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        mutation = {"$put":{"last_command":"counterclockwise"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        if DRONE_MODE == "live" and not NO_FLIGHT:
                            drone.counter_clockwise(ROTATION_SPEED)
                        mutation = {"$put":{"position.status":"counterclockwise"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        mutation = {"$put":{"status":"waiting"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        
                    if action == "counterclockwise360":
                        print("....................................................  Moving counter clockwise 360")
                        logging.info("....................................................  Moving counter clockwise 360")
                        mutation = {"$put":{"status":"busy"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        mutation = {"$put":{"last_command":"counterclockwise360"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        if DRONE_MODE == "live" and not NO_FLIGHT:
                            drone.counter_clockwise(ROTATION_SPEED)
                            time.sleep(15)
                            drone.clockwise(0)                            
                        mutation = {"$put":{"position.status":"counterclockwise360"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        mutation = {"$put":{"status":"waiting"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)

                    if action == "clockwise":
                        print("....................................................  Moving clockwise")
                        logging.info("....................................................  Moving clockwise")
                        mutation = {"$put":{"status":"busy"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        mutation = {"$put":{"last_command":"clockwise"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        if DRONE_MODE == "live" and not NO_FLIGHT:
                            drone.clockwise(ROTATION_SPEED)
                        mutation = {"$put":{"position.status":"clockwise"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        mutation = {"$put":{"status":"waiting"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)                        

                    if action == "clockwise360":
                        print("....................................................  Moving clockwise")
                        logging.info("....................................................  Moving clockwise")
                        mutation = {"$put":{"status":"busy"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        mutation = {"$put":{"last_command":"clockwise"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        if DRONE_MODE == "live" and not NO_FLIGHT:
                            drone.clockwise(ROTATION_SPEED)
                            time.sleep(15)
                            drone.clockwise(0)
                        mutation = {"$put":{"position.status":"clockwise"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        mutation = {"$put":{"status":"waiting"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)                        
                        
                else:
                    logging.info(".....................................................  Moving ")
                    from_zone = dronedata_table.find_by_id(DRONE_ID)["position"]["zone"]
                    drop_zone = json_msg["drop_zone"]
                    if drop_zone != from_zone:
                        mutation = {"$put":{"status":"busy"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        if DRONE_MODE == "live" and not NO_FLIGHT:
                            move_to_zone(drone,from_zone,drop_zone)
                        trigger = 0
                        while not drone.ready: # waits 3 seconds for the drone to stabilize
                            time.sleep(0.1)
                            trigger += 1
                            if trigger > 30:
                                break
                        logging.info("{} ready".format(DRONE_ID))
                        mutation = {"$put":{"position.zone":drop_zone}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation)
                        mutation = {"$put":{"status":"waiting"}}
                        dronedata_table.update(_id=DRONE_ID,mutation=mutation) 
                            

                

            elif msg.error().code() != KafkaError._PARTITION_EOF:
                logging.info(msg.error())

        except KeyboardInterrupt:
            drone.land()
            break   

        except:
            logging.exception("land failed")
            drone.land()
            break
        time.sleep(1)

    logging.info("QUITTING")


    KILL_ALL = True
    drone.killall = True
    logging.info("Exiting threads ... ")
    time.sleep(5)
    logging.info("threads killed.")

    sys.exit()


if __name__ == '__main__':
    main()
