import joblib
import requests
import pandas as pd
import os
from flask import Flask, Response, flash, request, redirect
from sklearn.preprocessing import LabelEncoder

EXECUTION_DEPLOY_URL = 'http://127.0.0.1:5005/execution/deploy'
EXECUTION_URL = 'http://127.0.0.1:5005/execution/session'
MONITORING_URL = 'http://127.0.0.1:5006/classifier/label'
DEVELOPMENT_CLASSIFIER_NET_URL = 'http://127.0.0.1:5001/deploy'
END_OF_DEVEL_TEST_URL = 'http://127.0.0.1:5009/testend'

MONITORING_REPETITION = 10
MONITORING_INTERVAL = 0

class DataframeEncoding:
    def encode(self, dataframe):
        encoder = {
            "1": {"sport": 0, "meditation": 1},
            "2": {"pop-music": 0, "ambient-music": 1},
            "3": {"focused": 0, "relaxed": 1, "excited": 2, "stressed": 3}
        }
        dataframe = dataframe.replace(encoder)
        return dataframe


class ExecutionSystem:
    def __init__(self, counter_val, monitoring_int, initial_mode):
        self.classifier = None
        self.classification_result = None
        self.uuid = None
        self.df = None
        self.session_data = None
        self.init_counter_value = counter_val
        self.monitoring_counter = None
        self.init_monitoring_interval = monitoring_int
        self.monitoring_interval = None
        self.operation_mode = initial_mode  # development mode = 0 // execution mode = 1
        self.no_monitoring_repetition = 0
        self.encoded_session = None
        self.classifier_n = 1

    def set_execution_mode(self):
        self.operation_mode = 1

    def set_development_mode(self):
        self.operation_mode = 0

    def get_mode(self):
        return self.operation_mode

    def deploy_classifier(self, response):
        if 'file' not in response.files:
            flash('No file part')
            print("Fail o get File")
            return 0
        file = response.files['file']
        classifier_name = "deployedClassifier" + str(self.classifier_n) + ".sav"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], classifier_name))
        self.classifier_n += 1
        self.classifier = joblib.load(classifier_name)
        #self.set_execution_mode()
        self.monitoring_counter = self.init_counter_value
        self.monitoring_interval = self.init_monitoring_interval
        if self.init_monitoring_interval == 0:  # monitoring is only executed once
            self.no_monitoring_repetition = 1
        return 1

    def load_classifier(self, filename):  # FOR TESTING ONLY
        self.classifier = joblib.load(filename)
        self.monitoring_counter = self.init_counter_value
        self.monitoring_interval = self.init_monitoring_interval
        if self.init_monitoring_interval == 0:  # monitoring is only executed once
            self.no_monitoring_repetition = 1

    def get_session(self, session_json):
        self.df = pd.read_json(session_json)
        print("\n\nSession from preparation")
        print(self.df)
        self.uuid = self.df.iloc[0:1, 0:1]
        self.df.drop(columns=self.df.columns[0], axis=1, inplace=True)  # I drop the UUID because useless

        # Take the inputs to be encoded (calendar, music, emotion)
        data_to_encode = self.df.iloc[:, 0:3]

        encoded_df = data_to_encode.replace("sport", 0)
        encoded_df = encoded_df.replace("meditation", 1)
        encoded_df = encoded_df.replace("pop-music", 0)
        encoded_df = encoded_df.replace("ambient-music", 1)
        encoded_df = encoded_df.replace("focused", 0)
        encoded_df = encoded_df.replace("relaxed", 1)
        encoded_df = encoded_df.replace("excited", 2)
        encoded_df = encoded_df.replace("stressed", 3)
        # Remove the encoded labels from the encoded dataframe (leave only calendar and music)
        dataframe_encoded = encoded_df.iloc[:, :-1]

        # Add the EEG features
        data2 = self.df.iloc[:, 4:8]

        # Merge everything, labels at the end.
        self.encoded_session = dataframe_encoded.join(data2)
        print("Encoded session")
        print(self.encoded_session)
        #data = data.join(labels) ### do not add label

    def send_label_monitoring(self, url):
        uuid_value = self.uuid.loc[0:1,0:1].values[0]  # ndarray
        data = {'label': self.classification_result.tolist(), 'uuid': uuid_value.tolist()}
        r = requests.post(url, json=data)  # send label to monitoring system
        #print(r.text)

    def classify_session(self, url):
        self.classification_result = self.classifier.predict(self.encoded_session)
        if self.monitoring_counter >= 0:  # monitoring period
            print('Remaining Sessions for Monitoring:', self.monitoring_counter)
            print(self.classification_result)
            self.monitoring_counter -= 1
            self.send_label_monitoring(url)
        # if no monitoring flag is zero, the system counts an amount of received sessions to then reset the monitoring
        elif self.no_monitoring_repetition == 0:
            self.monitoring_interval -= 1
            if self.monitoring_interval == 0:  # reset counters
                self.monitoring_counter = self.init_counter_value
                self.monitoring_interval = self.init_monitoring_interval



es = ExecutionSystem(MONITORING_REPETITION, MONITORING_INTERVAL, 0)

app = Flask(__name__)
UPLOAD_FOLDER = '.'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/execution/deploy", methods=['GET', 'POST'])
def deploy_classifier():
    if request.method == 'POST':
        r = es.deploy_classifier(request)
        if r != 0:
            print("CLASSIFIER DEPLOYED")
            requests.post(END_OF_DEVEL_TEST_URL)
            return Response("<h1>CLASSIFIER DEPLOYED</h1>", status=200, mimetype='text/html')
    else:
        return Response("<h1>EXECUTION SYSTEM ALIVE</h1>", status=200, mimetype='text/html')

@app.route("/execution/session", methods=['GET', 'POST'])
def exe_classifier():
    if request.method == 'POST':
        es.get_session(request.json)
        es.classify_session(MONITORING_URL)
        return Response("<h1>CLASSIFICATION COMPLETED</h1>", status=200, mimetype='text/html')
    else:
        return Response("<h1>EXECUTION SYSTEM ALIVE</h1>",status=200, mimetype='text/html')

es.load_classifier('deployedClassifier.sav') ## ONLY FOR MONITORING TEST
app.run(port=5005)