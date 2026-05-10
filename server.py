from flask import Flask, request
import os

app = Flask(__name__)
UPLOAD_FOLDER = './data'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file', 400
    file = request.files['file']
    # Важно: сохраняем в папку data, которую видят остальные скрипты
    file.save(os.path.join(UPLOAD_FOLDER, 'school_db.json'))
    return 'OK', 200

if __name__ == '__main__':
    # На реальном сервере укажи host='0.0.0.0'
    app.run(host=os.getenv("SITE_HOST"), port=os.getenv("SITE_PORT"))