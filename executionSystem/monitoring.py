import numpy as np
from flask import Flask, Response, flash, request, redirect
import pandas as pd
import requests

MONITORING_REPETITION = 10
MONITORING_ERROR_THRESHOLD = 0.5
MONITORING_CLASSIFIER_URL = 'http://127.0.0.1:5006/classifier/label'
MONITORING_HUMAN_URL = 'http://127.0.0.1:5006/human/label'
END_MONITORING_TEST_URL = 'http://127.0.0.1:5009/testend'

class MonitoringSystem:
    def __init__(self, error_th, counter_val):
        self.maximum_error_threshold = error_th
        self.human_label = [0]*counter_val
        self.classifier_label = [0]*counter_val
        self.uuid_human = [0]*counter_val
        self.uuid_classifier = [0]*counter_val
        self.h_label_ctr = 0
        self.c_label_ctr = 0
        self.classifier_error = 0
        self.classifier_accuracy = 0
        self.monitoring_counter = counter_val
        self.monitoring_num = 1

    def new_monitoring(self):
        self.h_label_ctr = 0
        self.c_label_ctr = 0
        self.monitoring_num += 1

    def get_human_label(self, json_label):
        df = pd.read_json(json_label)
        encoded_df = df.replace("focused", 0)  # decode label
        encoded_df = encoded_df.replace("relaxed", 1)
        encoded_df = encoded_df.replace("excited", 2)
        encoded_df = encoded_df.replace("stressed", 3)
        data_lst = encoded_df.values.tolist()
        ret = data_lst[0]
        uuid = ret[0]
        label = ret[1]
        print("Human Data", uuid, label)
        if self.h_label_ctr < len(self.human_label):
            self.human_label[self.h_label_ctr] = label
            self.uuid_human[self.h_label_ctr] = uuid
            #print('copy human label')
            #print(self.human_label[self.h_label_ctr])
            self.h_label_ctr += 1
            if self.c_label_ctr == self.monitoring_counter:
                self.compare_labels()

    def get_classifier_label(self, json_label):
        data = json_label
        lst_uuid = data['uuid']
        np_label = np.array(data['label'])
        lst_label = np_label.tolist()
        label = lst_label[0]
        uuid = lst_uuid[0]
        print("Classifier Data", uuid, label)
        if self.c_label_ctr < len(self.classifier_label):
            self.classifier_label[self.c_label_ctr] = label
            self.uuid_classifier[self.c_label_ctr] = uuid
            #print('copy classifier label')
            #print(self.classifier_label[self.c_label_ctr])
            self.c_label_ctr += 1
            if self.c_label_ctr == self.monitoring_counter:
                self.compare_labels()

    def synchronize_labels(self):
        print("Monitoring Counter: ", self.h_label_ctr)
        if self.c_label_ctr == self.h_label_ctr:
            return 0   # human and classifier labels are synchronized
        else:
            return 1

    def produce_report(self):
        #print('classifier accuracy:')
        #print(self.classifier_accuracy)
        #print('classifier labels:')
        #print(self.classifier_label)
        #print('human labels:')
        #print(self.human_label)
        file = open("monitoring_report" + str(self.monitoring_num) + ".txt", "w")
        file.write("MONITORING REPORT\nNumber of Sessions Received: ")
        file.write(str(self.monitoring_counter) + "\n")
        file.write("Monitoring Error: " + str(round(100*self.classifier_error, 2)) + "%\n")
        file.write("Maximum Error Threshold: " + str(100*self.maximum_error_threshold) + "%\n")
        if self.classifier_error < self.maximum_error_threshold:
            file.write("Classifier Performance: APPROVED\n\n")
        else:
            file.write("Classifier Performance: REJECTED\n\n")
        file.write("Sessions\nReceived Labels:\n")
        file.write("Human    Classifier\n")
        for n in range(self.monitoring_counter):
            file.write(str(self.human_label[n]))
            file.write("        ")
            file.write(str(self.classifier_label[n]))
            file.write("\n")
        file.close()
        self.new_monitoring()
        requests.port(END_MONITORING_TEST_URL)

    def compare_labels(self):
        true_comp = 0
        valid_labels = 0
        if (self.synchronize_labels()) == 0:
            for n in range(self.monitoring_counter):
                if (self.uuid_human == self.uuid_classifier):
                    valid_labels += 1
                    if (self.classifier_label[n] == self.human_label[n]):
                        true_comp += 1
            self.classifier_accuracy = true_comp / valid_labels  # calculate percentage of correct predictions
            self.classifier_error = 1 - self.classifier_accuracy
            self.produce_report()


ms = MonitoringSystem(MONITORING_ERROR_THRESHOLD, MONITORING_REPETITION)

app = Flask(__name__)

@app.route("/human/label", methods=['GET', 'POST'])
def get_human_label():
    if request.method == 'POST':
        ms.get_human_label(request.json)
        return Response("<h1>RECEIVED HUMAN LABEL</h1>", status=200, mimetype='text/html')
    # check if the server is running
    return Response("<h1>MONITORING SYSTEM SERVER ALIVE</h1>",status=200, mimetype='text/html')


@app.route("/classifier/label", methods=['GET', 'POST'])
def get_classifier_label():
    if request.method == 'POST':
        ms.get_classifier_label(request.json)
        return Response("<h1>RECEIVED CLASSIFIER LABEL</h1>", status=200, mimetype='text/html')
    # check if the server is running
    return Response("<h1>MONITORING SYSTEM SERVER ALIVE</h1>",status=200, mimetype='text/html')


app.run(port=5006)

