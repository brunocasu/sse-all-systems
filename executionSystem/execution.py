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

MONITORING_REPETITION = 50
MONITORING_INTERVAL = 0

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

    def get_session(self, session_json):
        self.df = pd.read_json(session_json)
        self.uuid = self.df[0:1, 0:1]
        self.df.drop(columns=self.df.columns[0], axis=1, inplace=True)  # remove UUID from the session

        labels = self.df.iloc[:, 3]  # Take label
        data1 = self.df.iloc[:, 0:3]  # Take the inputs (calendar, music, emotion)
        dataframe_encoded = DataframeEncoding(columns=['1', '2', '3']).fit_transform(data1)  # Encode the input
        data2 = self.df.iloc[:, 4:8]  # Take the features
        # Merge everything, labels at the end.
        self.encoded_session = dataframe_encoded.join(data2)
        #data = data.join(labels)  # don't add labels to the session

    def send_label_monitoring(self, url):
        data = {'label': self.classification_result.tolist(), 'uuid': self.uuid}
        r = requests.post(url, json=data)  # send label to monitoring system
        #print(r.text)

    def classify_session(self, url):
        self.classification_result = self.classifier.predict(self.encoded_session)
        if self.monitoring_counter >= 0:  # monitoring period
            print('classifier label n:', self.monitoring_counter)
            print(self.classification_result)
            self.monitoring_counter -= 1
            #self.send_label_monitoring(url)
        # if no monitoring flag is zero, the system counts an amount of received sessions to then reset the monitoring
        elif self.no_monitoring_repetition == 0:
            self.monitoring_interval -= 1
            if self.monitoring_interval == 0:  # reset counters
                self.monitoring_counter = self.init_counter_value
                self.monitoring_interval = self.init_monitoring_interval


class DataframeEncoding:
    def __init__(self, columns=None):
        self.columns = columns  # array of column names to encode

    def fit(self, X, y=None):
        return self  # not relevant here

    def transform(self, X):
        """
        Transforms columns of X specified in self.columns using
        LabelEncoder(). If no columns specified, transforms all
        columns in X.
        """
        output = X.copy()
        if self.columns is not None:
            for col in self.columns:
                output[col] = LabelEncoder().fit_transform(output[col])
        else:
            for colname, col in output.iteritems():
                output[colname] = LabelEncoder().fit_transform(col)
        return output

    def fit_transform(self, X, y=None):
        return self.fit(X, y).transform(X)


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


app.run(port=5005)