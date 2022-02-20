import numpy as np
from flask import Flask, Response, flash, request, redirect

MONITORING_ERROR_THRESHOLD = 0.1
MONITORING_CLASSIFIER_URL = 'http://127.0.0.1:5006/classifier/label'
MONITORING_HUMAN_URL = 'http://127.0.0.1:5006/human/label'

class MonitoringSystem:
    def __init__(self, error_th, counter_val):
        self.maximum_error_threshold = error_th
        self.human_label = [0]*counter_val
        self.classifier_label = [0]*counter_val
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
        data = json_label
        uuid = data['uuid']
        print("HUMAN LABEL UUID RECEIVED\n", uuid)
        label = np.array(data['label'])
        print(label)
        if self.h_label_ctr < len(self.human_label):
            self.human_label[self.h_label_ctr] = label.tolist()
            #print('copy human label')
            #print(self.human_label[self.h_label_ctr])
            self.h_label_ctr += 1
            if self.c_label_ctr == self.monitoring_counter:
                self.compare_labels()

    def get_classifier_label(self, json_label):
        data = json_label
        uuid = data['uuid']
        print("CLASSIFIER LABEL RECEIVED\n", uuid)
        print(type(uuid))
        label = np.array(data['label'])
        print(label)
        if self.c_label_ctr < len(self.classifier_label):
            self.classifier_label[self.c_label_ctr] = label.tolist()
            #print('copy classifier label')
            #print(self.classifier_label[self.c_label_ctr])
            self.c_label_ctr += 1
            if self.c_label_ctr == self.monitoring_counter:
                self.compare_labels()

    def synchronize_labels(self):
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

    def compare_labels(self):
        true_comp = 0
        if (self.synchronize_labels()) == 0:
            for n in range(self.monitoring_counter):
                if self.classifier_label[n] == self.human_label[n]:
                    true_comp += 1
            self.classifier_accuracy = true_comp / self.c_label_ctr  # calculate percentage of correct predictions
            self.classifier_error = 1 - self.classifier_accuracy
            self.produce_report()


ms = MonitoringSystem(0.1, 50)

app = Flask(__name__)

@app.route("/human/label", methods=['GET', 'POST'])
def get_human_label():
    if request.method == 'POST':
        print(request.json)
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

