from flask import Flask, render_template, request, jsonify, send_file, Response
from spleeter.separator import Separator
from threading import Thread
from queue import Queue
import os
import shutil
import uuid
import json
import time

app = Flask(__name__,
static_url_path='', 
static_folder='public',
template_folder='views'
    )
app.config['UPLOAD_FOLDER'] = 'public/uploads/'
app.config['ZIP_FOLDER'] = 'public/zip/'

# Queue for log messages
log_queue = Queue()
clients = {}

def send_log(message, client_id):
    if client_id in clients:
        clients[client_id].put(json.dumps( message ))

def process_audio(folder_path, audio_path, client_id):
    try:
        uid = str(uuid.uuid4())
        
        send_log({"event": "process", "message": "start to separate audio."}, client_id)
        separator = Separator('spleeter:2stems')
        separator.separate_to_file(audio_path, folder_path)
        
        # Kirim log bahwa proses dimulai
        send_log({"event": "process", "message": "compressing files to zip."}, client_id)

        # Zip the output folder
        zip_path = os.path.join(app.config['ZIP_FOLDER'], uid)
        shutil.make_archive(zip_path, 'zip', folder_path)
        
        # Remove contents of the output folder
        shutil.rmtree(folder_path)

        # Kirim log bahwa proses selesai
        send_log({"event": "success", "message": "Processing completed.", "link": f"/zip/{uid}.zip"}, client_id)
    except Exception as e:
        # Kirim log jika terjadi kesalahan
        print( e );
        send_log({"event": "error", "message": "Error during separation."}, client_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global clients
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file:
        # Generate a random filename with UUID
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], str(uuid.uuid4()))
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        audio_path = os.path.join(folder_path, file.filename)
        file.save(audio_path)

        # Create a unique client ID
        client_id = str(uuid.uuid4())

        # Add the client queue to the clients dictionary
        clients[client_id] = Queue()

        # Start a thread for audio processing
        thread = Thread(target=process_audio, args=(folder_path, audio_path, client_id))
        thread.start()

        return jsonify({'success': True, 'message':'Uploaded, wait to spleeter start.', 'client_id': client_id})

@app.route('/log/<client_id>')
def log(client_id):
    def generate():
        while True:
            message = clients[client_id].get()
            yield f'data: {message}\n\n'
            time.sleep(0.1)

    return Response(generate(), content_type='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
