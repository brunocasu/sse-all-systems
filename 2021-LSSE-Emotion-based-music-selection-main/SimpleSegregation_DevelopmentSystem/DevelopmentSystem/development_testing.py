import sqlite3
import sys
from random import randint
import random
import pandas as pd
import requests

from DevelopmentSystem.emotionclassifier \
    import DevelopEmotionClassifier
from jsonschema_validation \
    import JsonSchemaValidation
from DevelopmentSystem.utility \
    import read_db, read_json, write_db, write_json, delete_db, empty_df

BASE_DIR = "DevelopmentSystem"
DEPLOYED_NETWORK = "final_network.sav"
#BEST_NETWORKS_PATH = BASE_DIR + "/json_report_files/validation_report.json"
#BEST_NETWORKS_TABLE = BASE_DIR + "/json_report_files/best_networks_params.txt"
#TEST_REPORT_PATH = BASE_DIR + "/json_report_files/test_report.json"
BEST_NETWORKS_PATH = BASE_DIR + "/validation_report.json"
BEST_NETWORKS_TABLE = BASE_DIR + "/best_networks_params.txt"
TEST_REPORT_PATH = BASE_DIR + "/test_report.json"


class DevelopmentTesting:

    def manual_testing(self):

        # CONNECT TO DB
        try:
            con = sqlite3.connect(BASE_DIR + '/develop_system.db')
        except sqlite3.DatabaseError as err:
            print("[DEVELOPMENT SYSTEM]: Cannot connect to the db\n")
            print(err)
            sys.exit()

        classifier = DevelopEmotionClassifier(BASE_DIR, BEST_NETWORKS_PATH,
                                              BEST_NETWORKS_TABLE, TEST_REPORT_PATH,
                                              DEPLOYED_NETWORK)

        json_object = read_json(BASE_DIR + "/conf_files/execution_flow.json")

        validate = JsonSchemaValidation(BASE_DIR + "/", "development")
        if not validate.flow_validation(json_object):
            sys.exit()

        app_json_object = read_json(BASE_DIR + "/conf_files/application_settings.json")
        if not validate.app_settings_validation(app_json_object):
            sys.exit()

        if json_object["start"]:
            # GET DATA FROM RESTFUL AND STORE THEM INTO THE DB

            get_data = requests.get(str(app_json_object["rest_addr"]) + '/Restful_api/development')
            if get_data.status_code == 500:
                print("[DEVELOPMENT SYSTEM]: Machine Learning Set not available on the server.")
                sys.exit()

            json_data = get_data.json().get('machine_learning_set')

            training_data = pd.DataFrame.from_dict(json_data.get('training_set'))
            training_labels = pd.Series(json_data.get('training_label'))

            validation_data = pd.DataFrame.from_dict(json_data.get('validation_set'))
            validation_labels = pd.Series(json_data.get('validation_label'))

            testing_data = pd.DataFrame.from_dict(json_data.get('testing_set'))
            testing_labels = pd.Series(json_data.get('testing_label'))

            # SET CLASSIFIER DATASETS
            classifier.set_data(training_data, training_labels,
                                validation_data, validation_labels, testing_data,
                                testing_labels)

            # WRITE DATA IN THE DB
            write_db(con, training_data, training_labels,
                     validation_data, validation_labels, testing_data,
                     testing_labels)

            # SET STARTING PHASE TO FALSE
            json_object["start"] = False
            write_json(BASE_DIR + "/conf_files/execution_flow.json", json_object)

            # THE APPLICATION STARTED. INFORM THE MAIN PROCESS
            app_json_object["manual_testing_started"] = True
            write_json(BASE_DIR + "/conf_files/application_settings.json", app_json_object)

            # TRAIN THE CLASSIFIER
            classifier.training_classifier()
            print("[DEVELOPMENT SYSTEM]: Classifier training. Check the curve trend\n"
                  "If you're not satisfied please change max_iter in conf_file "
                  "and restart training")

        elif json_object["training"]:
            # Reset the execution_flow
            json_object["training"] = False
            write_json(BASE_DIR + "/conf_files/execution_flow.json", json_object)
            if json_object["retraining"]:
                classifier.delete_for_retraining()
                # Reset the execution_flow
                json_object["retraining"] = False
                write_json(BASE_DIR + "/conf_files/execution_flow.json", json_object)

            # READ DATA FROM THE DB AND SET INTO THE CLASSIFIER
            training_data, training_labels, validation_data, \
                validation_labels, testing_data, testing_labels = read_db(
                    con)

            if empty_df(training_data, training_labels, validation_data,
                        validation_labels, testing_data, testing_labels):
                print("[DEVELOPMENT SYSTEM]: Data Sets in the database are not complete")
                sys.exit()

            classifier.set_data(training_data, training_labels,
                                validation_data, validation_labels, testing_data,
                                testing_labels)

            # TRAIN THE CLASSIFIER
            classifier.training_classifier()
            print("[DEVELOPMENT SYSTEM]: Classifier training. Check the curve trend\n"
                  "If you're not satisfied please change max_iter in initial_network_params.json "
                  "and restart training")

        elif json_object["success_training"]:
            # Reset the execution_flow
            json_object["success_training"] = False
            write_json(BASE_DIR + "/conf_files/execution_flow.json", json_object)
            # READ DATA FROM THE DB AND SET INTO THE CLASSIFIER

            training_data, training_labels, validation_data, validation_labels, testing_data, testing_labels = read_db(
                con)

            if empty_df(training_data, training_labels, validation_data,
                        validation_labels, testing_data, testing_labels):
                print("[DEVELOPMENT SYSTEM]: Data Sets in the database are not complete")
                sys.exit()

            classifier.set_data(training_data, training_labels, validation_data, validation_labels, testing_data,
                                testing_labels)

            print("[DEVELOPMENT SYSTEM]: Start Grid Search and Validation phase\n")
            # RUN GRID SEARCH ALGORITHM AND VALIDATE THE NETWORKS
            classifier.grid_search()

            # CHECK IF THE FILE WITH THE BEST NETWORKS HAS BEEN PRODUCED: IF NOT IS USELESS TO CONTINUE
            if not read_json(BEST_NETWORKS_PATH):
                print("[DEVELOPMENT SYSTEM]: No network produced by GridSearch. Restart training phase\n")
            else:
                print("[DEVELOPMENT SYSTEM]: Grid search algorithm executed. "
                      "Check the bar plot for the errors in graph/validation_report.png.\n"
                      "Networks parameters and available in " + BEST_NETWORKS_TABLE + ".\n"
                                                                                      "Choose the best network "
                                                                                      "by typing the index in "
                                                                                      "the file or restart "
                                                                                      "training\n")
        elif json_object["testing"]:
            # Reset the execution_flow
            json_object["testing"] = False
            write_json(BASE_DIR + "/conf_files/execution_flow.json", json_object)
            # CHECK WHETHER THE BEST NETWORK HAS BEEN CHOSEN
            if json_object["chosen_network_index"] is not None:

                # READ DATA FROM THE DB AND SET INTO THE CLASSIFIER
                training_data, training_labels, validation_data, validation_labels, testing_data, testing_labels = \
                    read_db(con)

                if empty_df(training_data, training_labels, validation_data, validation_labels, testing_data,
                            testing_labels):
                    print("[DEVELOPMENT SYSTEM]: Data Sets in the database are not complete")
                    # Reset the execution_flow
                    json_object["chosen_network_index"] = None
                    write_json(BASE_DIR + "/conf_files/execution_flow.json", json_object)
                    sys.exit()

                classifier.set_data(training_data, training_labels, validation_data, validation_labels, testing_data,
                                    testing_labels)

                # SET THE SELECTED NETWORK
                classifier.select_network(json_object["chosen_network_index"])

                # Reset the execution_flow
                json_object["chosen_network_index"] = None
                write_json(BASE_DIR + "/conf_files/execution_flow.json", json_object)
            else:
                print("[DEVELOPMENT SYSTEM]: Please insert the network you choose and restart\n")

            print("[DEVELOPMENT SYSTEM]: Start network testing\n")
            classifier.testing_classifier()

            # DELETE DB CONTENT.
            delete_db(con)

            print(
                "[DEVELOPMENT SYSTEM]: Check the textual test report in " + TEST_REPORT_PATH + "or the plot in "
                                                                                               "graph/test_report"
                                                                                               ".json.\n "
                                                                                               "State whether you "
                                                                                               "accept or not the "
                                                                                               "network.")

        elif json_object["accept_final_report_step"]:
            # Reset the execution_flow
            json_object["accept_final_report_step"] = False
            write_json(BASE_DIR + "/conf_files/execution_flow.json", json_object)
            # FINAL STEP: CHECK IF THE NETWORK HAS BEEN ACCEPTED OF NOT
            if json_object["accept_network"]:
                # NETWORK ACCEPTED. CLASSIFIER CAN BE DEPLOYED
                classifier.deploy_classifier()
                print(
                    "[DEVELOPMENT SYSTEM]: Classifier ready to be deployed.\nFinal network stored in " +
                    DEPLOYED_NETWORK)

                # Reset the execution_flow
                json_object["accept_network"] = False
                write_json(BASE_DIR + "/conf_files/execution_flow.json", json_object)

            else:
                print("[DEVELOPMENT SYSTEM]: Network non accepted. Reconfiguration required.\n")
            # classifier.delete_report_files()

        elif json_object["retraining"] and not json_object["training"]:
            print("[DEVELOPMENT SYSTEM]: To retrain the network, set also 'training':true")
        else:
            print("[DEVELOPMENT SYSTEM]: No action to be executed, please select the point from where to start\n")
        con.close()

    def automatic_testing(self):

        # CONNECT TO DB
        try:
            con = sqlite3.connect(BASE_DIR + '/develop_system.db')
        except sqlite3.DatabaseError as err:
            print("[DEVELOPMENT SYSTEM]: Cannot connect to the db\n")
            print(err)
            sys.exit()

        classifier = DevelopEmotionClassifier(BASE_DIR, BEST_NETWORKS_PATH, BEST_NETWORKS_TABLE, TEST_REPORT_PATH,
                                              DEPLOYED_NETWORK)

        validate = JsonSchemaValidation(BASE_DIR + "/", "development")
        app_json_object = read_json(BASE_DIR + "/conf_files/application_settings.json")
        if not validate.app_settings_validation(app_json_object):
            sys.exit()

        # GET DATA FROM SEGREGATION SYSTEM THROUGH RESTFUL, SET CLASSIFIER DATA AND FILL THE DB
        get_data = requests.get(str(app_json_object["rest_addr"]) + '/Restful_api/development')
        if get_data.status_code == 500:
            print("[DEVELOPMENT SYSTEM]: Machine Learning Set not available on the server.")
            sys.exit()
        json_data = get_data.json().get('machine_learning_set')

        training_data = pd.DataFrame.from_dict(json_data.get('training_set'))
        training_labels = pd.Series(json_data.get('training_label'))

        validation_data = pd.DataFrame.from_dict(json_data.get('validation_set'))
        validation_labels = pd.Series(json_data.get('validation_label'))

        testing_data = pd.DataFrame.from_dict(json_data.get('testing_set'))
        testing_labels = pd.Series(json_data.get('testing_label'))

        # SET CLASSIFIER DATASETS
        classifier.set_data(training_data, training_labels, validation_data, validation_labels, testing_data,
                            testing_labels)

        # WRITE DATA IN THE DB
        write_db(con, training_data, training_labels, validation_data, validation_labels, testing_data,
                 testing_labels)

        # READ DATA FROM THE INPUT AND STORE THEM INTO THE DB

        restart_from_training = True
        training = True
        while restart_from_training:

            # THE CLASSIFIER IS TRAINED UNTIL THE CURVE IS NOT FLAT ENOUGH
            while training:
                classifier.training_classifier()
                pass_training = random.uniform(0, 1)
                #if pass_training < app_json_object["curve_flat"]:
                if pass_training < 0.5:
                    old_epochs = int(classifier.get_epochs())
                    new_epochs = randint(old_epochs, 1000)
                    print("[DEVELOPMENT SYSTEM]: Training not passed. New number of epochs generated: " + str(
                        new_epochs) + ". Training is restarting")
                    # Set generations
                    classifier.set_epochs(new_epochs)
                else:
                    training = False

            print("[DEVELOPMENT SYSTEM]: Classifier has been trained. The loss curve is flat enough")

            # RUN THE GRID SEARCH AND VALIDATE THE RESULTING NETWORKS
            print("[DEVELOPMENT SYSTEM]: Start Grid Search and Validation phase")
            classifier.grid_search()
            # CHECK IF NETWORKS HAVE BEEN PRODUCED
            if not read_json(BEST_NETWORKS_PATH):
                print("[DEVELOPMENT SYSTEM]: No network produced by GridSearch. Restart training phase")
                training = True
            else:
                # I CHECK IF ALL THE FIVE BEST NETWORKS ARE PRESENT, OTHERWISE I DO NOT CONSIDER THAT INDEX
                # BETWEEN THE PRESENT I TAKE ONLY THOSE HAVING VALIDATION ERROR LESS THAN THRESHOLD
                present = []
                for i in range(0, 5):
                    if classifier.check_presence(i):
                        # get the validation error
                        val_error = classifier.get_validation_error(i)
                        #if float(val_error) < app_json_object["validation_threshold"]:
                        if float(val_error) < 0.9: #### ADDED ####
                            present.append(i)
                if len(present) == 0:
                    print("[DEVELOPMENT SYSTEM]: No network is enough accurate. Validation not passed. Restart "
                          "training phase")
                    classifier.delete_for_retraining()
                    training = True
                else:
                    print("[DEVELOPMENT SYSTEM]: Grid search algorithm executed.")
                    # I CAN EXIT FROM THE LOOP
                    restart_from_training = False

        # PRODUCE THE INDEX OF THE CHOSEN NETWORK
        chosen = random.choice(present)
        print("[DEVELOPMENT SYSTEM]: Classifier has been chosen, index: " + str(chosen))
        classifier.select_network(chosen)

        # DELETE DB CONTENT.
        delete_db(con)

        # THE THE CHOSEN NETWORK
        print("[DEVELOPMENT SYSTEM]: Start network testing")
        test_error = classifier.testing_classifier()

        if test_error > app_json_object["test_threshold"]:
            print("[DEVELOPMENT SYSTEM]: Classifier didn't pass testing phase. Reconfiguration needed")
            classifier.delete_report_files()
            return False
        else:
            # CLASSIFIER PASSED THE TESTING PHASE, SO CAN BE DEPLOYED THROUGH A POST
            print("[DEVELOPMENT SYSTEM]: Classifier passed the testing phase")
            classifier.deploy_classifier()

            return True
