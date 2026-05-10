from flask import Flask, request
import os

app = Flask(__name__)
UPLOAD_FOLDER = './data'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    file.save(os.path.join(UPLOAD_FOLDER, 'school_db.json'))
    return 'File uploaded successfully', 200

if __name__ == '__main__':
    # На реальном сервере укажи host='0.0.0.0'
    app.run(host='0.0.0.0', port=5000)