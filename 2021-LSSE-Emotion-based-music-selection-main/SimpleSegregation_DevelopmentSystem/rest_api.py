from flask import Flask, request
from flask_restful import Resource, Api

import sys

from DevelopmentSystem.development_testing import DevelopmentTesting
from DevelopmentSystem.utility import read_json
from SimpleSegregationSystem.segregation_testing import SegregateData
from jsonschema_validation import JsonSchemaValidation


app = Flask(__name__)
api = Api(app)

session = {}


# TODO Need to add Try and Catch
# TODO Need to finish for all the different application

class Restful_api(Resource):

    def get(self, system):
        if (system == "ingestion"):
            return session['new_record'], 200

        elif (system == "preparation"):
            return session['raw_session'], 200

        elif (system == "segregation"):
            try:
                return session['prepared_session'], 200
            except:
                return session, 500

        elif (system == "development"):
            try:
                return session['machine_learning_set'], 200
            except:
                return session, 500

        else:
            # TODO return an error
            return session, 404

    def post(self, system):
        print("SYSTEM: ", system)
        json_file = request.get_json()

        if (system == "ingestion"):
            session['new_record'] = {'new_record': json_file}

        elif (system == "preparation"):
            # session['raw_session'] = {'data': json_file}
            session['raw_session'] = {'raw_session': json_file}

        elif (system == "segregation"):
            session['prepared_session'] = {'prepared_session': json_file}
            #### ADDED ####
            validate = JsonSchemaValidation("DevelopmentSystem/", "development")
            app_json_object = read_json("DevelopmentSystem/conf_files"
                                        "/application_settings.json")
            if not validate.app_settings_validation(app_json_object):
                sys.exit()

            if (app_json_object["manual_testing"] and not app_json_object["manual_testing_started"]) \
                    or not app_json_object["manual_testing"]:
                SegregateData().run_segregation(json_file)
                print("Segregation done")

            # RUN DEVELOPMENT SYSTEM
            testing = DevelopmentTesting()
            if app_json_object["manual_testing"]:
                # MANUAL TESTING
                testing.manual_testing()
            else:
                # AUTOMATIC TESTING -> NO USER INVOLVED, JUST INITIAL FILE CONFIGURATION
                result = testing.automatic_testing()
                if result:
                    print("Network produced - sent to Deploy in Execution system")
                else:
                    print("Network development failed")

        elif (system == "development"):
            # {machine_learning_set: { 'training_set': data, 'validation_set': data,
            # 'testing_set': data}}
            session['machine_learning_set'] = {'machine_learning_set': json_file}

        else:
            # TODO Need to send error message
            return {"message": "Error"}, 201

        #return session, 201


api.add_resource(Restful_api, '/Restful_api/<system>')

app.run(debug=True, port=5000)

#if __name__ == '__main__':
#    app.run(debug=True, port=5001)
