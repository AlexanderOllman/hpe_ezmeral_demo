from confluent_kafka import Consumer
import time
import json
import cv2
import os
################

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

MIRROR_VOLUME_NAME = "testMirror"


stream_topic = 'user-tracker'
consumer_group = str(time.time())
c = Consumer({'group.id': consumer_group, 'default.topic.config':{'auto.offset.reset':'latest'}})
c.subscribe([VIDEO_STREAM + ":" + stream_topic ])


print('Kafka Consumer has been initiated...')

#c.subscribe(['user-tracker'])
################
def faceRecognise(frame):

   
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    
    faces = face_cascade.detectMultiScale(frame, scaleFactor=1.1,minNeighbors=5,minSize=(100, 100),flags=cv2.CASCADE_SCALE_IMAGE )

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (130, 169, 1), 4)
                                                # Grab ROI with Numpy slicing and blur
        #face = Rectangle(x, y, w, h)
        #print(data["frame"])

    return frame


def processing_function(message, count):
        image = cv2.imread(message.get('frame'),0)
        print("image read successful")        
        #image = imutils.resize(image, width=min(400, image.shape[1]))
        processed_image = faceRecognise(image)
                                                                        # (processed_image,count) = face_detection(image)


        image_folder = DATA_FOLDER + "/images/drone_2/processed/"
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)
        processed_image_path = image_folder + "frame-{}.jpg".format(count)
        cv2.imwrite(processed_image_path, processed_image)
        message["image"] = processed_image_path

        #return message 


def main():
    
    offsetOld = 0.0
    
    while True:
        msg=c.poll(1.0) #timeout
        if msg is None:
            continue
        if msg.error():
            print('Error: {}'.format(msg.error()))
            continue
        else:
            data = json.loads(msg.value())
            fileName = data.get('frame')
            offset = data.get('offset')
            count = data.get('user_id')
            print(fileName)
            
            while not os.path.isfile(fileName):
                time.sleep(0.5)
                print('file not found at: ' + fileName)
            
            #os.system("maprcli volume mirror start -name testMirror")
            #frame = cv2.imread(fileName)
    
           
    c.close()
        
if __name__ == '__main__':
    main()
