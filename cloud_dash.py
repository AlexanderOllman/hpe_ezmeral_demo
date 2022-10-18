
from flask import Flask, jsonify, render_template, request
import webbrowser
import time
from os.path import exists



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

STATIC_FOLDER = ROOT_PATH + "/static"

app = Flask(__name__)

i = 0
b = []



def stream_video():
    global VIDEO_STREAM
    global OFFSET_RESET_MODE
    global DISPLAY_STREAM_NAME

    logging.info('Start of loop for {}:{}'.format(VIDEO_STREAM,drone_id))
    consumer_group = str(time.time())
    consumer = Consumer({'group.id': consumer_group, 'default.topic.config': {'auto.offset.reset': OFFSET_RESET_MODE}})
    consumer.subscribe([VIDEO_STREAM + ":" + drone_id + "_" + DISPLAY_STREAM_NAME ])
    current_stream = DISPLAY_STREAM_NAME

    while True:
        msg = consumer.poll(0.5)
        if msg is None:
            continue
        if not msg.error():
            json_msg = json.loads(msg.value().decode('utf-8'))
            image = json_msg['image']
            try:
              while not os.path.isfile(image):
                    time.sleep(0.05)
              with open(image, "rb") as imageFile:
                f = imageFile.read()
                b = bytearray(f)
              yield (b'--frame\r\n' + b'Content-Type: image/jpg\r\n\r\n' + b + b'\r\n\r\n')
            except Exception as ex:
              logging.info("can't open file {}".format(image))
              logging.exception("fails")


        elif msg.error().code() != KafkaError._PARTITION_EOF:
            logging.info('  Bad message')
            logging.info(msg.error())
            break
    logging.info("Stopping video loop for {}".format(drone_id))


@app.route('/_stuff', methods = ['GET'])
def stuff():
    global i
    path= "static/images/"
    path2 = path+"frame_"+str(i)+".jpg"

    if exists(path2):
        if len(b) < 12:
            b.append(i)
        else:
            b.pop()
            b.insert(0, i)

        if i == 20:
            i = 1
        else:
            i = i + 1

    return jsonify(b=b, path=path)


@app.route('/')
def index():

    return render_template('index2.html')

def contact():
    if "forward" in request.form:
        print("forward!")
    elif "left" in request.form:
        print("left!")


if __name__ == '__main__':

    app.run(debug=True, host='0.0.0.0', port=9991)
