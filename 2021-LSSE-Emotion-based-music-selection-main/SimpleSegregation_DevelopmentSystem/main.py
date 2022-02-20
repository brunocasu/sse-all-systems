import sys

from flask import Flask, request
from flask_restful import Resource, Api

import requests
from pandas import read_csv
import pandas as pd
from SimpleSegregation_DevelopmentSystem.DevelopmentSystem.development_testing import DevelopmentTesting
from SimpleSegregation_DevelopmentSystem.DevelopmentSystem.utility import read_json
from SimpleSegregation_DevelopmentSystem.SimpleSegregationSystem.segregation_testing import SegregateData
from SimpleSegregation_DevelopmentSystem.jsonschema_validation import JsonSchemaValidation

if __name__ == '__main__':

    # READ THE APPLICATION CONF FILE OF DEVELOPMENT SYSTEM TO UNDERSTAND IF MANUAL OR AUTOMATIC TESTING.
    # THE MODALITY (MANUAL/AUTOM) MUST BE SET IN SimpleSegregation_DevelopmentSystem/DevelopmentSystem/conf_files"
    #                                 "/application_settings.json
    # CASE MANUAL:
    # IF DEVEL. IS NOT AT THE BEGINNING (PART OF COMPUTATION ALREADY DONE):
    # SKIP ALL THE PREVIOUS SYSTEMS EXECUTIONS (INGESTION, PREP, SEGR.) BECAUSE DATA ALREADY IN THE DB

    validate = JsonSchemaValidation("SimpleSegregation_DevelopmentSystem/DevelopmentSystem/", "development")
    app_json_object = read_json("SimpleSegregation_DevelopmentSystem/DevelopmentSystem/conf_files"
                                "/application_settings.json")
    if not validate.app_settings_validation(app_json_object):
        sys.exit()

    if (app_json_object["manual_testing"] and not app_json_object["manual_testing_started"]) \
            or not app_json_object["manual_testing"]:

        # TODO REMOVE AFTER OTHER SYSTEM ADDED
        # I POST DATA AS PREPARATION SHOULD DO
        df_prepared_session_ = read_csv('SimpleSegregation_DevelopmentSystem/SimpleSegregationSystem/prepared_session.csv')
        prepared_session_ = pd.DataFrame(df_prepared_session_).to_dict()
        r = requests.post('http://127.0.0.1:5000/Restful_api/segregation', json=prepared_session_)
        # TODO UP TO HERE
        # RUN SEGREGATION SYSTEM
        SegregateData().run_segregation()
        print("Segregation done")


    #RUN DEVELOPMENT SYSTEM
    testing = DevelopmentTesting()

    if app_json_object["manual_testing"]:
        # MANUAL TESTING
        testing.manual_testing()

    else:
        # AUTOMATIC TESTING -> NO USER INVOLVED, JUST INITIAL FILE CONFIGURATION
        result = testing.automatic_testing()
        if result:
            print("Network produced")
        else:
            print("Network development failed")