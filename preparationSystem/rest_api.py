from flask import Flask, request
from flask_restful import Resource, Api
import preparation_system as ps

app = Flask(__name__)
api = Api(app)

session = {}

#TODO Need to add Try and Catch
#TODO Need to finish for all the different application

class Restful_api(Resource):


    def get(self, system):
        if (system == "ingestion"):
            return session['new_record'], 200

        elif (system == "preparation"):
            return session['raw_session'], 200

        elif (system == "segregation"):
            return session['prepared_session_segregation']

        elif (system == "development"):
            return session['machine_learning_set']

        elif (system == "execution"):
            return session['prepared_session_execution']

        elif (system == "monitoring"):
            return session['labels']

        else:
            #TODO return an error
            return session, 200


    def post(self, system):
        print("SYSTEM: ", system)
        try:
            json_file = request.get_json()

            if (system == "ingestion"):
                session['new_record'] = {'new_record': json_file}

            elif (system == "preparation"):
                #session['raw_session'] = {'data': json_file}
                #print("RAW SESSION:" ,request.json)
                session['raw_session'] = {'raw_session': json_file}
                cl.execute_preparation_system(request.json)  ## added

            elif (system == "segregation"):
                session['prepared_session_segregation'] = {'prepared_session': json_file}

            elif (system == "development"):
                #i suggest to send a json like this: { 'training_set': data, 'validation_set': data,
                # 'testing_set': data}
                session['machine_learning_set'] = {'machine_learning_set': json_file}

            elif (system == "execution"):
                session['prepared_session_execution'] = {'prepared_session': json_file}

            elif (system == "monitoring"):
                session['labels'] = {'labels': json_file}

            else:
                #TODO Need to send error message
                return {"message" : "Error"}, 201
        except:
            print("Error")
        return session, 201


cl = ps.Preparation_system() ## added
api.add_resource(Restful_api, '/Restful_api/<system>')

if __name__ == '__main__':
    app.run(debug=True, port=5002)