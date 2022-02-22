import json
import os
import sqlite3
import sys

import requests
import pandas as pd
from sklearn.model_selection import train_test_split

from SimpleSegregationSystem.dataframe_encoding import DataframeEncoding
from SimpleSegregationSystem.utility import write_db, read_db, delete_db
from jsonschema_validation import JsonSchemaValidation

# BASE_DIR = "SimpleSegregation_DevelopmentSystem/SimpleSegregationSystem" #### ADDED ####
BASE_DIR = "SimpleSegregationSystem"
CONF_PATH = BASE_DIR + "/conf_files/configuration.json"
EXPECTED_LEN = 9
"""
    THIS SYSTEM IMPLEMENTS ONLY:
        - DATA RETRIEVAL 
        - DATA STORING
        - IT ENCODES THE DATASET COLUMN VALUES
        - IT SPLITS INTO TRAINING, VALIDATION, TEST SETS
        - IT POSTS THE DATA FOR DEVELOPMENT SYSTEM
"""


class SegregateData:
    def run_segregation(self, json_file):

        validation = JsonSchemaValidation(BASE_DIR + "/", "segregation")
        if os.path.exists(CONF_PATH):
            with open(CONF_PATH, "r") as jsonFile:
                json_object = json.load(jsonFile)
                if not validation.segregation_conf_file_validation(json_object):
                    sys.exit()
                jsonFile.close()
        else:
            print("[SEGREGATION SYSTEM]: Error: file " + CONF_PATH + " does not exists.")
            sys.exit()

        # REQUEST AND GET THE DATA FROM PREPARATION SYSTEM
        #### ADDED #### Preparation POST the Data -  no need to GET
        #get_data = requests.get('http://127.0.0.1:5000/Restful_api/segregation')
        #if get_data.status_code == 500:
            #print("[SEGREGATION SYSTEM]: Machine Learning Set not available on the server.")
            #sys.exit()


        #json_data = get_data.json().get('prepared_session')
        #df = pd.DataFrame.from_dict(json_data)
        #### ADDED #### read pandas datafram from the json sent by preparation
        df = pd.read_json(json_file)

        if df.empty or len(df) < EXPECTED_LEN:
            print("[SEGREGATION SYSTEM]: Machine learning set received is empty or not complete.")
            sys.exit()

        # CONNECT TO DB
        try:
            con = sqlite3.connect(BASE_DIR + '/segregation_system.db')
        except sqlite3.DatabaseError as err:
            print("[SEGREGATION SYSTEM]: Cannot connect to the db\n")
            print(err)
            sys.exit()
        # Store the received data into the DB
        write_db(con, df)

        # Read data from the db
        df = read_db(con)

        df.drop(columns=df.columns[0], axis=1, inplace=True)  # I drop the UUID because useless

        # Take labels string
        labels = df.iloc[:, 2]

        # Take the inputs to be encoded (calendar, music, emotion)
        data_to_encode = df.iloc[:, 0:3]

        # Encode the dataframe
        dataframe_encoded = DataframeEncoding().encode(data_to_encode)

        # Take the encoded labels (emotions)
        labels = dataframe_encoded.iloc[:, -1]

        # Remove the encoded labels from the encoded dataframe (leave only calendar and music)
        dataframe_encoded = dataframe_encoded.iloc[:, :-1]

        # Take the eeg features
        data2 = df.iloc[:, 4:8]

        # Merge everything, labels at the end.
        data = dataframe_encoded.join(data2)
        data = data.join(labels)
        print("SEGREGATION DATA ENCODED", data.head(10)) #### ADDED ####

        # Split the data into training, test, and validation set
        test_size = json_object["test_split"]
        train_data, test_data, train_labels, test_labels = train_test_split(
            data.iloc[:, 0:len(data.columns) - 1],
            data.iloc[:, len(data.columns) - 1],
            test_size=test_size)

        val_size = json_object["val_split"]
        train_data, val_data, train_labels, val_labels = train_test_split(train_data, train_labels,
                                                                          test_size=val_size)
        # val_size x (1-test_size) = test_size

        train_data_json = train_data.to_dict()
        train_labels_json = train_labels.to_dict()
        val_data_json = val_data.to_dict()
        val_labels_json = val_labels.to_dict()
        test_data_json = test_data.to_dict()
        test_labels_json = test_labels.to_dict()

        json_file = {
            'training_set': train_data_json,
            'training_label': train_labels_json,
            'validation_set': val_data_json,
            'validation_label': val_labels_json,
            'testing_set': test_data_json,
            'testing_label': test_labels_json

        }

        r = requests.post('http://127.0.0.1:5000/Restful_api/development', json=json_file)
        if r.status_code == 200:
            print("[SEGREGATION SYSTEM]: Machine learning set successfully posted, ready for Development system.")

        # Delete the db content
        delete_db(con)
        con.close()
