from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import accuracy_score
from pandas import read_csv
from numpy import ravel
import json
import joblib
import requests


### FOR TESTING ONLY ###

## INGESTION/PREPARATION
data1 = read_csv('test_data/hotspotUrbanMobility-1.csv')
data2 = read_csv('test_data/hotspotUrbanMobility-2.csv')
data = data1.append(data2, ignore_index=True)
data = data.drop('h24', axis=1)
data = data.loc[data['Anomalous'] < 1]
data.to_csv('test_data/preprocessedDataset.csv', index=False)
data = read_csv('test_data/preprocessedDataset.csv')

## SEGREGATION
training_data, testing_data, training_labels, testing_labels = train_test_split(data.iloc[:, 4:len(data.columns)], data.iloc[:, 1])  # return DataFrame obj (pandas)

## DEVELOPMENT
mlp = MLPClassifier(random_state=1234)
parameters = {'max_iter': (10, 20, 30)}
gs = GridSearchCV(mlp, parameters)
gs.fit(training_data, ravel(training_labels))

# test performance
labels = gs.predict(testing_data)
score = accuracy_score(ravel(testing_labels), labels)
print('deploy score:')
print(score)

# save parameters
config_path = 'test_config/modelConfiguration.json'
with open(config_path, 'w') as f:
    json.dump(gs.best_params_, f)
joblib.dump(gs, 'test_config/fitted_model.sav')

EXE_URL = 'http://127.0.0.1:5000/execution/classifier'

# check if the server is running
r = requests.get(EXE_URL)
print(r.content)

# send execution system the complete classifier file - to be deployed
files = {'file': open('test_config/fitted_model.sav', 'rb')}

rr = requests.post(EXE_URL, files=files)  # send trained network
print(rr.text)

