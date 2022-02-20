import json
import math
import os
import sys
import warnings

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import requests

from numpy import ravel

from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GridSearchCV
from sklearn.neural_network import MLPClassifier

from jsonschema_validation import JsonSchemaValidation
from DevelopmentSystem.utility import read_json, write_json, plot_bar_chart, \
    multi_bar_chart, table

MODEL_CONFIGURATION_PATH = "conf_files/initial_network_params.json"
FIRST_MODEL = "networks/first_model.sav"
BEST_NETWORK = "networks/best_network"  # best_network0.sav etc...
NETWORKS_DIR = "networks/"
warnings.filterwarnings("ignore", category=ConvergenceWarning, module="sklearn")
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")


class DevelopEmotionClassifier:
    validate = None
    training_set = None
    training_set_labels = None
    validation_set = None
    validation_set_labels = None
    test_set = None
    test_set_labels = None
    params = None
    classifier = None
    gs = None
    base_dir = None
    test_report_path = None
    best_networks_path = None
    best_networks_table = None
    deployed_path = None
    model_configuration_path = None
    first_model = None
    best_network = None

    def __init__(self, base_dir, best_networks_params_path, best_networks_table, test_report_path, deployed_network):
        self.base_dir = base_dir + "/"
        self.test_report_path = test_report_path
        self.best_networks_path = best_networks_params_path
        self.best_networks_table = best_networks_table
        self.deployed_path = self.base_dir + NETWORKS_DIR + deployed_network
        self.model_configuration_path = self.base_dir + MODEL_CONFIGURATION_PATH
        self.first_model = self.base_dir + FIRST_MODEL
        self.best_network = self.base_dir + BEST_NETWORK
        self.validate = JsonSchemaValidation(self.base_dir, "development")

    def set_data(self, training_set, training_set_labels, validation_set, validation_set_labels, test_set,
                 test_set_labels):
        self.training_set = training_set
        self.training_set_labels = training_set_labels
        self.validation_set = validation_set
        self.validation_set_labels = validation_set_labels
        self.test_set = test_set
        self.test_set_labels = test_set_labels

    # IN CASE OF RETRAINING I MUST SET THE NEW NUMBER OF GENERATIONS
    def set_epochs(self, epochs):
        if os.path.exists(self.model_configuration_path):
            json_object = read_json(self.model_configuration_path)
            json_object["max_iter"] = [epochs]
            write_json(self.model_configuration_path, json_object)
            self.params = read_json(self.model_configuration_path)
        else:
            print("[DEVELOPMENT SYSTEM]: No hyperparameter setting. Only number of epochs added\n")
            json_object = {"max_iter": [epochs]}
            write_json(self.model_configuration_path, json_object)
            self.params = read_json(self.model_configuration_path)

    def training_classifier(self):

        # CHECK IF THE CONFIGURATION FILE IS COMPLIANT
        params = read_json(self.model_configuration_path)
        if not self.validate.conf_params_validation(params):
            sys.exit()

        # READ AND SET THE NETWORK PARAMETERS FROM THE CONF FILE. I SET THE AVG OF THE VALUES
        json_parameters = {}
        for i in params:
            if type(params[i]) is list and len(params[i]) > 0:
                if type(params[i][0]) is int or type(params[i][0]) is float:
                    params_i = []
                    for j in range(0, len(params[i])):
                        params_i.append(params[i][j])
                    media = math.floor(sum(params_i) / len(params_i))
                    json_parameters[i] = media

        # CREATE AND TRAIN THE CLASSIFIER
        self.classifier = MLPClassifier()
        self.classifier.set_params(**json_parameters)

        self.classifier.fit(self.training_set, ravel(self.training_set_labels))
        # compute training error
        tr_labels = self.classifier.predict(self.training_set)
        tr_error = accuracy_score(ravel(self.training_set_labels), tr_labels)
        print("[DEVELOPMENT SYSTEM]: Training Error: " + str(1 - tr_error))

        # store classifier for reuse
        joblib.dump(self.classifier, self.first_model)

        # DRAW GRADIENT DESCEND CURVE
        plt.plot(self.classifier.loss_curve_)
        plt.title('Loss Curve')
        plt.xlabel('Number of generations')
        plt.ylabel('Loss')
        #plt.savefig(self.base_dir + "graph/gradient_descend.png") #### ADDED ####
        plt.savefig("gradient_descend.png")
        plt.close()

    def grid_search(self):

        # READ THE HYPER PARAMETERS FROM THE CONF FILE, CHECK THE COMPLIANCE
        params = read_json(self.model_configuration_path)
        if not self.validate.conf_params_validation(params):
            sys.exit()

        # LOAD THE CLASSIFIER PREVIOUSLY TRAINED
        self.classifier = joblib.load(self.first_model)
        # EXECUTE GRID SEARCH TO FIND THE BEST PARAMS
        gs = GridSearchCV(self.classifier, params, cv=4)
        gs.fit(self.validation_set, ravel(self.validation_set_labels))
        # Extract the dataframe from the results and keep the parameters of the best networks
        var = pd.DataFrame(gs.cv_results_)
        best_networks = var['params']
        df = pd.DataFrame(best_networks)

        val_error = []
        tr_error = []
        classifier = []
        # FOR EACH PARAMETER SET, BUILD THE NETWORK AND COMPUTE THE TRAINING AND VALIDATION ERROR
        for i in range(0, len(best_networks)):
            classifier.append(MLPClassifier(**best_networks[i]).fit(self.training_set, ravel(self.training_set_labels)))
            val_labels = classifier[i].predict(self.validation_set)
            val_error.append(float(1 - accuracy_score(ravel(self.validation_set_labels), val_labels)))
            tr_labels = classifier[i].predict(self.training_set)
            tr_error.append(float(1 - accuracy_score(ravel(self.training_set_labels), tr_labels)))

        # ADD VALIDATION AND TRAINING ERROR TO THE DATAFRAME
        df.insert(0, "validation_error", val_error)
        df.insert(1, 'training_error', tr_error)

        # ORDER THE DATAFRAME BASED ON VALIDATION ERROR IN DESCENDING ORDER
        df["validation_error"] = pd.to_numeric(df["validation_error"])
        df.sort_values(by="validation_error", ascending=False, inplace=True)

        # Take only the first 5 networks, with the lowest validation error
        networks = df.head(5)

        # PLOT THE ERRORS IN A BAR CHART
        training_err = networks["training_error"].to_list()
        validation_err = networks["validation_error"].to_list()
        multi_bar_chart(training_err, validation_err, self.base_dir)

        # STORE THE 5 BEST NETWORKS
        j = 0
        for i in networks.index:
            joblib.dump(classifier[i], self.best_network + str(j) + ".sav")
            j += 1

        # Reset the indexes to simplify network selection and testing phase
        networks.reset_index(drop=True, inplace=True)

        #SAVE THE NETWORK PARAMETERS IN TABULAR FORMAT TO BE MORE READABLE
        table(networks["params"], self.best_networks_table)

        # Store the 5 best networks params and errors into a json file
        if not self.validate.validation_report_validation(networks.to_dict()):
            exit(0)
        with open(self.best_networks_path, 'w') as file:
            json.dump(networks.to_dict(), file)
            file.close()

        # REMOVE THE FIRST MODEL USED TO DECIDE THE EPOCHS
        if os.path.exists(self.first_model):
            os.remove(self.first_model)

    # DELETE THE NETWORKS AND THE PARAMETERS FOR RETRAINING PHASE
    def delete_for_retraining(self):
        networks = read_json(self.best_networks_path)

        # DELETE THE NETWORKS
        for i in range(0, len(networks['params'])):
            if os.path.exists(self.best_network + str(i) + ".sav"):
                os.remove(self.best_network + str(i) + ".sav")

        # DELETE THE BEST PARAMS
        if os.path.exists(self.best_networks_path):
            os.remove(self.best_networks_path)

    # CHECK IF IN THE BEST NETWORKS THERE'S ONE WITH INDEX 'ACCEPT'
    def check_presence(self, accept):
        networks = read_json(self.best_networks_path)
        if not self.validate.validation_report_validation(networks):
            sys.exit()
        return str(accept) in networks['params']

    # I TAKE THE VALIDATION ERROR OF THE NETWORKS AND GIVE BACK TO THE MAIN FUNCTION TO BE COMPARED WITH THE THRESHOLD.
    # THOSE NETWORKS HAVING VAL ERROR ABOVE THE THR CANNOT BE CHOSEN.
    # IT'S JUST FOR AUTOMATIC TESTING
    def get_validation_error(self, accept):
        networks = read_json(self.best_networks_path)
        if not self.validate.validation_report_validation(networks):
            sys.exit()
        return networks['validation_error'][str(accept)]

    # SELECT THE BEST NETWORK. I KEEP ONLY THAT NETWORK AND I REMOVE ALL THE OTHERS
    def select_network(self, accept):

        # READ THE FILE WITH THE PARAMS OF THE BEST NETWORKS
        networks = read_json(self.best_networks_path)
        index = self.check_presence(accept)

        # DELETE ALL THE NETWORKS APART FROM THE CHOSEN ONE
        if index:
            for i in range(0, len(networks['params'])):
                if i is not int(accept):
                    if os.path.exists(self.best_network + str(i) + ".sav"):
                        os.remove(self.best_network + str(i) + ".sav")

            # rename the file to easily find it later
            if os.path.exists(self.best_network + str(accept) + ".sav"):
                os.rename(self.best_network + str(accept) + ".sav", self.best_network + ".sav")
            else:
                print("[DEVELOPMENT SYSTEM]: Error, file " + self.best_network + str(accept) + ".sav does not exists")
                exit(0)

            # store the best params and related errors in a json file
            best_param = networks['params'][str(accept)]
            print("[DEVELOPMENT SYSTEM]: Best parameters: " + str(best_param))

            val_error = networks["validation_error"][str(accept)]
            print("[DEVELOPMENT SYSTEM]: Validation error: " + str(val_error))

            tr_error = networks["training_error"][str(accept)]
            print("[DEVELOPMENT SYSTEM]: Training error: " + str(tr_error))

            json_object = {'params': best_param, 'validation_error': float(val_error),
                           'training_error': float(tr_error)}

            if not self.validate.test_report_validation(json_object):
                sys.exit()
            # WRITE THE TEST_REPORT (PARAMS + TRAINING/VALIDATION ERROR)
            write_json(self.test_report_path, json_object)

            # REMOVE THE FILE WITH PARAMS OF THE 5 BEST NETS
            if os.path.exists(self.best_networks_path):
                os.remove(self.best_networks_path)
            if os.path.exists(self.best_networks_table):
                os.remove(self.best_networks_table)
        else:
            print("[DEVELOPMENT SYSTEM]: No network with this index\n")
            sys.exit()

    # TEST THE CHOSEN NETWORK USING THE TESTING DATASET
    def testing_classifier(self):

        # load the network
        classifier = joblib.load(self.best_network + ".sav")
        labels = classifier.predict(self.test_set)
        test_error = 1 - accuracy_score(ravel(self.test_set_labels), labels)
        print("[DEVELOPMENT SYSTEM]: Testing Error: " + str(test_error))

        # ADD THE TESTING ERROR TO THE TEST_REPORT FILE
        if os.path.exists(self.test_report_path):

            json_object = read_json(self.test_report_path)
            json_object["testing_error"] = float(test_error)
            if not self.validate.test_report_validation(json_object):
                exit(0)
            write_json(self.test_report_path, json_object)
            plot_bar_chart(json_object.get("training_error"), json_object.get("validation_error"),
                           json_object.get("testing_error"), self.base_dir)
        else:
            print("[DEVELOPMENT SYSTEM]: Error: during testing phase, file " + self.test_report_path + " not found.")
        return test_error

    # DEPLOY THE NETWORK
    def deploy_classifier(self):
        # I CHECK THE EXISTENCE OF THE NET AND RENAME IT
        if os.path.exists(self.best_network + ".sav"):
            os.rename(self.best_network + ".sav", self.deployed_path)
        else:
            print("[DEVELOPMENT SYSTEM]: Error during deployment\n")
            # exit(0)

        app_json_object = read_json(self.base_dir + "/conf_files/application_settings.json")
        if not self.validate.app_settings_validation(app_json_object):
            sys.exit()
        # POST THE CLASSIFIER THROUGH THE HTTP
        API_URL = str(app_json_object["network_server_addr"]) + "/deploy/"
        #### ADDED ####
        EXECUTION_DEPLOY_URL = 'http://127.0.0.1:5005/execution/deploy'
        files = {'file': open(self.deployed_path, 'rb')}
        try:
            rr = requests.post(EXECUTION_DEPLOY_URL, files=files)
            if rr.status_code == 200:
                print("[DEVELOPMENT SYSTEM]: Network successfully deployed.")

        except requests.exceptions.RequestException as e:
            print(e)

    def delete_report_files(self):

        #DELETE ALL THE TEXT FILE REPORTS
        if os.path.exists(self.test_report_path):
            os.remove(self.test_report_path)

        #DELETE ALL THE GRAPHS
        if os.path.exists(self.base_dir + "graph/gradient_descend.png"):
            os.remove(self.base_dir + "graph/gradient_descend.png")
        if os.path.exists(self.base_dir + "graph/final_report.png"):
            os.remove(self.base_dir + "graph/final_report.png")
        if os.path.exists(self.base_dir + "graph/validation_report.png"):
            os.remove(self.base_dir + "graph/validation_report.png")
