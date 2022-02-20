import requests
import json

if __name__ == '__main__':
    #We will simulate the send of the data from the ingestion application
    config_path = "raw_session_from_ingestion.json"
    with open(config_path, "r") as f:
       data = json.load(f)

    #We will send the json through the restful_API
    r = requests.post('http://127.0.0.1:5000/Restful_api/preparation', json=data)
