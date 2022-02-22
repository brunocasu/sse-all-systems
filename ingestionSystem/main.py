from ingestion import IngestionSystem
from flask import Flask, Response, flash, request, redirect
import requests
import os
PREPARATION_URL = 'http://127.0.0.1:5002/Restful_api/preparation'
MONITORING_URL = 'http://127.0.0.1:5006/human/label'

NUMBER_OF_SESSIONS_PROCESSED = 200

app = Flask(__name__) # always use this

UPLOAD_FOLDER = '.'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

calendar_filename = 'dataset_calendar.csv'
headset_filename = 'dataset_headset.csv'
labels_filename = 'dataset_labels.csv'
setting_filename = 'dataset_setting.csv'

@app.route("/ingestion/dataset", methods=['GET', 'POST'])
def get_dataset():
    if request.method == 'POST':
        if 'labels' not in request.files:
            flash('No file part')
            return redirect(request.url)
        calendar_file = request.files['calendar']
        headset_file = request.files['headset']
        labels_file = request.files['labels']
        setting_file = request.files['setting']

        calendar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], calendar_filename))
        headset_file.save(os.path.join(app.config['UPLOAD_FOLDER'], headset_filename))
        labels_file.save(os.path.join(app.config['UPLOAD_FOLDER'], labels_filename))
        setting_file.save(os.path.join(app.config['UPLOAD_FOLDER'], setting_filename))

        add_file = [calendar_filename,headset_filename,labels_filename,setting_filename]

        IngestionSystem(add_file, NUMBER_OF_SESSIONS_PROCESSED, PREPARATION_URL, None, 1)

        return Response("<h1>DATASET SENT TO PREPARATION</h1>", status=200, mimetype='text/html')
    else:
        # This is a test endpoint used to check if the server is running
        return Response("<h1>I’m alive!</h1>",status=200, mimetype='text/html')

@app.route("/ingestion/session", methods=['GET', 'POST'])
def get_session():
    if request.method == 'POST':
        if 'labels' not in request.files:
            flash('No file part')
            return redirect(request.url)
        calendar_file = request.files['calendar']
        headset_file = request.files['headset']
        labels_file = request.files['labels']
        setting_file = request.files['setting']

        calendar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'session_calendar.csv'))
        headset_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'session_headset.csv'))
        labels_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'session_labels.csv'))
        setting_file.save(os.path.join(app.config['UPLOAD_FOLDER'],'session_setting.csv'))

        add_file = ['session_calendar.csv','session_headset.csv','session_labels.csv','session_setting.csv']

        IngestionSystem(add_file, 1, PREPARATION_URL, MONITORING_URL, 0)
        return Response("<h1>SESSION SENT</h1>", status=200, mimetype='text/html')
    else:
        # This is a test endpoint used to check if the server is running
        return Response("<h1>I’m alive!</h1>",status=200, mimetype='text/html')


app.run(port=5004)
