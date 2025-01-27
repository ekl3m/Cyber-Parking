import cv2
import os

from flask import Flask, render_template, request, Response, stream_with_context, jsonify
from signal import signal, SIGINT
from detect_tools import *
from log_tools import *
from camera import *

app = Flask(__name__)

# Czyszczenie zasobów przy zamknięciu aplikacji
def cleanup(sig, frame):
    global camera
    with camera_lock:
        if camera:
            camera.release()
            camera = None
    log_event("Aplikacja została zatrzymana.")
    exit(0)

signal(SIGINT, cleanup)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_source', methods=['POST'])
def set_source():
    source = request.form.get('source')
    try:
        set_camera(source)  # Ustaw źródło kamery
        return "Źródło ustawione", 200
    except RuntimeError as e:
        return str(e), 500

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/logs')
def logs():
    def stream_logs():
        index = 0
        while True:
            if index < len(log_history):
                yield f"data: {log_history[index]}\n\n"
                index += 1
    return Response(stream_with_context(stream_logs()), mimetype='text/event-stream')

@app.route('/get_all_logs', methods=['GET'])
def get_all_logs():
    return jsonify(log_history)

if __name__ == '__main__':
    log_event("Aplikacja została uruchomiona.")
    app.run(debug=False, port=8080)