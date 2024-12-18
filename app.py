from flask import Flask, render_template, request, Response, stream_with_context, jsonify
import cv2
import os
import time
import numpy as np
import psutil
from signal import signal, SIGINT
import threading

app = Flask(__name__)
camera = None
camera_lock = threading.Lock()  # Blokada dla obsługi kamery

# Domyślny plik wideo
DEFAULT_VIDEO_PATH = os.path.join('static', 'sample.mp4')

# Lista logów przechowywana w pamięci
log_history = []

def log_event(message):
    """Dodaj wiadomość do listy logów."""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] {message}"
    log_history.append(log_message)
    print(log_message)  # Wyświetlanie logów w konsoli

def log_memory_usage():
    """Logowanie zużycia pamięci."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    log_event(f"Zużycie pamięci: RSS={mem_info.rss // 1024} KB, VMS={mem_info.vms // 1024} KB")

def cleanup(sig, frame):
    """Czyszczenie zasobów przy zamknięciu aplikacji."""
    global camera
    with camera_lock:
        if camera:
            camera.release()
            camera = None
    log_event("Aplikacja została zatrzymana.")
    exit(0)

signal(SIGINT, cleanup)

def generate_frames():
    """Generowanie klatek strumieniowych."""
    global camera
    placeholder_path = os.path.join('static', 'placeholder.jpg')
    if not os.path.exists(placeholder_path):
        log_event(f"Nie znaleziono pliku zastępczego: {placeholder_path}")
        placeholder_frame = 255 * np.ones((480, 640, 3), dtype=np.uint8)
    else:
        placeholder_frame = cv2.imread(placeholder_path)
        if placeholder_frame is None:
            log_event("Nie udało się załadować obrazu zastępczego.")
            placeholder_frame = 255 * np.ones((480, 640, 3), dtype=np.uint8)

    while True:
        try:
            with camera_lock:
                log_memory_usage()
                if camera and camera.isOpened():
                    ret, frame = camera.read()
                    if not ret:
                        log_event("Kamera nie dostarcza klatek. Wyświetlanie klatki zastępczej.")
                        frame = placeholder_frame
                    else:
                        log_event("Klatka kamery odczytana pomyślnie.")
                else:
                    log_event("Brak aktywnego źródła wideo. Wyświetlanie klatki zastępczej.")
                    frame = placeholder_frame

            # Kodowanie klatki do formatu JPEG
            success, buffer = cv2.imencode('.jpg', frame)
            if not success:
                raise ValueError("Nie udało się zakodować klatki do JPEG.")
            
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
            # Dodanie krótkiego opóźnienia
            time.sleep(0.03)  # Odpowiada około 30 FPS
        except Exception as e:
            log_event(f"Błąd w generatorze klatek: {str(e)}")
            time.sleep(1)  # Krótkie opóźnienie, aby zapobiec nadmiernemu obciążeniu CPU

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_source', methods=['POST'])
def set_source():
    """Ustawienie źródła wideo."""
    global camera
    source = request.form.get('source')

    with camera_lock:
        # Zamknij poprzednie źródło
        if camera:
            log_event("Zwalnianie poprzedniego źródła.")
            camera.release()
            camera = None

        # Ustaw nowe źródło
        if source == 'camera':
            camera = cv2.VideoCapture(0)  # Kamera na żywo
            if not camera.isOpened():
                log_event("Nie udało się otworzyć kamery.")
                return "Nie udało się otworzyć kamery!", 500
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            log_event("Źródło ustawione: Kamera na żywo.")
        elif source == 'video':
            video_path = DEFAULT_VIDEO_PATH  # Wczytaj domyślne wideo
            if not os.path.exists(video_path):
                log_event("Nie znaleziono domyślnego pliku wideo!")
                return "Nie znaleziono domyślnego pliku wideo!", 404
            camera = cv2.VideoCapture(video_path)
            if not camera.isOpened():
                log_event("Nie udało się otworzyć pliku wideo.")
                return "Nie udało się otworzyć pliku wideo!", 500
            log_event(f"Źródło ustawione: Wideo z pliku ({video_path}).")

    return "Źródło ustawione", 200

@app.route('/video_feed')
def video_feed():
    """Strumień wideo."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/logs')
def logs():
    """Strumień logów dla interfejsu webowego."""
    def stream_logs():
        index = 0
        while True:
            if index < len(log_history):
                yield f"data: {log_history[index]}\n\n"
                index += 1
    return Response(stream_with_context(stream_logs()), mimetype='text/event-stream')

@app.route('/get_all_logs', methods=['GET'])
def get_all_logs():
    """Endpoint do pobierania wszystkich logów na start."""
    return jsonify(log_history)

if __name__ == '__main__':
    log_event("Aplikacja została uruchomiona.")
    app.run(debug=False, port=8080)