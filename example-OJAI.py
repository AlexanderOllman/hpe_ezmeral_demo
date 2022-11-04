#!/usr/bin/python

"""
-----------------------------------------------------------------------------------------------
  This script will read and write to DF DB
  First we establish a connection to secure or non secrue cluster
  Then we create and delete a random JSON DB table
  Then we create a DB JSON table with an inital JSON document if it does not already exits
  Then we Read and write a whole JSON document
  Then we read and write a specific field in a JSON document
  Then we add and delete a random field in an existing document
  Then

  https://docs.datafabric.hpe.com/apidocs/61/ojai/python/functions.html
-----------------------------------------------------------------------------------------------
"""

"""
-----------------------------------------------------------------------------------------------
The CLI demo will have examples of CLI commands in an SH script
Create and delete a random DB JSON table
Test a table with basic comands
Add or update ACES and permissions
Add or update data masking
Add one way table replication
Add master + master replication
pause replication
ersume replication
throtle replication

Need to do the same with REST calls
-----------------------------------------------------------------------------------------------
"""

# VARIABLES
SECURE_MODE = False
MY_CLUSTER_API_ADDRESS = '127.0.0.1' # cluster name if you have resolution or cluster IP for the API server
MY_CLUSTER_GATEWAY_ADDRESS = '127.0.0.1' # the location of the Data Access Gateway
MY_CLUSTER_NAME = 'MY_CLUSTER_NAME' # the name of the cluster in the global namespace
GLOBAL_PATH = '/mapr/' + MY_CLUSTER_NAME # the path to the root folder of the cluster via global namespace
LOCAL_PATH = '/apps/my_project_folder' # the path to the project folder via assumed local cluster
MY_PROJECT_DBS = '/apps/my_project_folder/my_project_dbs' # the place where my tables will live. I like to have a volume for the project folder and a volume for each type of data used
USERNAME='ezmeral'
PASSWORD='admin123'
PEM_FILE = "/opt/mapr/conf/ssl_truststore.pem"

RANDOM_TABLE_NAME = MY_PROJECT_DBS + '/RANDOM_TABLE_NAME'
MY_TABLE_NAME = MY_PROJECT_DBS + '/MY_TABLE_NAME'

DRONE_ID = 'my_drone_id'

# Import required libs
from mapr.ojai.storage.ConnectionFactory import ConnectionFactory

# Initialize databases conection
# create connection string
if SECURE_MODE:
  connection_str = "{}:5678?auth=basic;" \
                           "user={};" \
                           "password={};" \
                           "ssl=true;" \
                           "sslCA={};" \
                           "sslTargetNameOverride={}".format(MY_CLUSTER_API_ADDRESS,USERNAME,PASSWORD,PEM_FILE,MY_CLUSTER_API_ADDRESS)
else:
  connection_str = "{}:5678?auth=basic;user={};password={};ssl=false".format(MY_CLUSTER_API_ADDRESS,USERNAME,PASSWORD)

# establish connection
df_db_connection = ConnectionFactory().get_connection(connection_str=connection_str)


# create a new document store for a my_random_table
random_table = df_db_connection.get_or_create_store(RANDOM_TABLE_NAME)

# delete my random table
df_db_connection.delete_store(RANDOM_TABLE_NAME)


# create table MY_TABLE_NAME
my_table = df_db_connection.get_or_create_store(MY_TABLE_NAME)


# example JSON docuemnt
document = {"_id": DRONE_ID,
            "drone_data":{
                "battery":0,
                "movement_speed":5.0,
                "drone_type":"TEST",
                "dreone_resources":{
                    "camera":"false",
                    "gps":"false",
                    "wifi":"false",
                    "bluetooth":"false",
                    "celular":"false",
                },
                "manufacture":"TEST",
                "software_version":"TEST"
            },
            "log_data":"unset",
            "count":0,
            "connection_status":"disconnected",
            "position": {
                "zone":"home_base", 
                "status":"available",
                "offset":0.0
            }
        }

print('adding a document to table')
new_document = df_db_connection.new_document(dictionary=document)
my_table.insert_or_replace(new_document)
print(new_document.as_json_str())


# fetch the OJAI Document by its '_id' field
print("get the document by _id")
doc = my_table.find_by_id(_id=DRONE_ID)
print(doc)

print('delete a document from a table')
# delete by document
print("delete by document")
my_table.delete(new_document)
doc = my_table.find_by_id(_id=DRONE_ID)
print(doc)

# delete by _ID
print("delete by _ID")
my_table.insert_or_replace(new_document)
my_table.delete(_id=DRONE_ID)
doc = my_table.find_by_id(_id=DRONE_ID)
print(doc)

my_table.insert_or_replace(new_document)
# inert a field in document or update its value using mutation
#{"$set":{"fieldpath":value}}
#{"$set":[{"fieldpath1":value1},{"fieldpath2":value2},...]}
doc = my_table.find_by_id(_id=DRONE_ID)
print(doc)

mutation = {"$set": [{"drone_data.battery": 100}, {"drone_data.battery_temp":122}]}
my_table.update(_id=DRONE_ID, mutation=mutation)
doc = my_table.find_by_id(_id=DRONE_ID)
print(doc)

# delete a field
mutation = {"$delete":["drone_data.battery_temp"]}
my_table.update(_id=DRONE_ID, mutation=mutation)
doc = my_table.find_by_id(_id=DRONE_ID)
print(doc)
