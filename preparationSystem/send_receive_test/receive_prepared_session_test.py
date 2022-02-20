import requests
import json
import pandas as pd

def save_file_in_json(name, file):
    with open(name, 'w') as f:
        json.dump(file, f)

if __name__ == '__main__':
    #send request to receive the prepared session from the preparation application
    prepared_session = requests.get('http://127.0.0.1:5000/Restful_api/segregation')
    pd_file = pd.DataFrame(prepared_session.json().get('prepared_session'))
    print(pd_file.to_string())