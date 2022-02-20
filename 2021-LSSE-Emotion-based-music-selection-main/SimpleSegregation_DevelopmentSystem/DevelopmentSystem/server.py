import os
from flask import Flask, flash, request, redirect, Response, send_from_directory

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'sav'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# allow only '.sav' files to be uploaded
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/deploy/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'final_network.sav'))
            return Response("<h1>CLASSIFIER DEPLOYED</h1>", status=200, mimetype='text/html')
    if request.method == 'GET':
        return send_from_directory(app.config["UPLOAD_FOLDER"], 'final_network.sav')
    return


if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5001, debug=True)
