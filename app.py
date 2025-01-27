from flask import Flask, render_template, request, Response, stream_with_context, jsonify
import cv2
import os
import time
import numpy as np
import psutil
from signal import signal, SIGINT
from enum import Enum
import threading

app = Flask(__name__)
camera = None
camera_lock = threading.Lock()  # Blokada dla obsługi kamery

# Sciezki plikow
DEFAULT_VIDEO_PATH = '/Users/sqstudio/Desktop/Studia/Przetwarzanie_Sygnałów_i_Obrazów/cyber-parking/static/sample1.mp4'
PLACEHOLDER_FRAME_PATH = '/Users/sqstudio/Desktop/Studia/Przetwarzanie_Sygnałów_i_Obrazów/cyber-parking/static/placeholder.jpg'

# Model YOLOv8
from roboflow import Roboflow
from ultralytics import YOLO
rf = Roboflow(api_key="FWlZpKPCE4GysrCWg6LC")
project = rf.workspace("muhammad-syihab-bdynf").project("parking-space-ipm1b")
version = project.version(4)
model = version.model

# Lista logów przechowywana w pamięci
log_history = []

# Dodawanie wiadomości do listy logów
def log_event(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_message = f"[{timestamp}] {message}"
    log_history.append(log_message)
    print(log_message)

# Debug - funkcja do logowania zuzycia pamieci
def log_memory_usage():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    log_event(f"Zużycie pamięci: RSS={mem_info.rss // 1024} KB, VMS={mem_info.vms // 1024} KB")

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

# Enum, który umozliwia kontrole nad bramkami
class GateAction(Enum):
    ENTRY_OPEN = "Bramka wjazdowa się otwiera."
    ENTRY_CLOSE = "Bramka wjazdowa się zamyka."
    EXIT_OPEN = "Bramka wyjazdowa się otwiera."
    EXIT_CLOSE = "Bramka wyjazdowa się zamyka."

# Funkcja, ktora zajmuje sie obsluga bramek
def manage_gates(action: GateAction):
    if isinstance(action, GateAction):
        log_event(action.value)
    else:
        raise ValueError("Niepoprawna akcja dla bramki")

# Detekcja parkingów
def detect_parking_areas(frame):
    """Wykorzystanie modelu YOLOv8 do detekcji miejsc parkingowych."""

    # Konwersja obrazu do RGB (YOLO wymaga przestrzeni RGB)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Predykcja z modelu YOLO
    results = model.predict(frame_rgb, confidence=12, overlap=35).json()

    # Debugowanie wyników detekcji
    # print("Wyniki detekcji:", results)

    parking_areas = []
    for prediction in results['predictions']:
        # print("Klasa:", prediction['class'])  # Logowanie klasy detekcji
        # print("Predykcja:", prediction)  # Logowanie szczegółów predykcji

        # Sprawdzenie, czy klasyfikacja to miejsce parkingowe
        if prediction['class'] == 'empty' or prediction['class'] == 'occupied':
            x = int(prediction['x'] - prediction['width'] / 2)
            y = int(prediction['y'] - prediction['height'] / 2)
            w = int(prediction['width'])
            h = int(prediction['height'])
            parking_areas.append((x, y, x + w, y + h, prediction['class']))

    return parking_areas

def draw_parking_boxes(frame, parking_areas):
    height, width, _ = frame.shape
    black_band_top = (height // 3) - 20
    black_band_bottom = 2 * height // 3

    for (x1, y1, x2, y2, status) in parking_areas:
        # Sprawdź, czy współrzędne prostokąta znajdują się poza "czarnym pasem"
        if y1 >= black_band_top and y2 <= black_band_bottom:
            continue

        if status == 'empty':
            color = (0, 255, 0)  # Zielony dla miejsc "empty"
            label = 'Empty'
        elif status == 'occupied':
            color = (0, 0, 255)  # Czerwony dla miejsc "occupied"
            label = 'Occupied'

        # Debug - logowanie współrzędnych
        # print(f"Rysowanie prostokąta: ({x1}, {y1}), ({x2}, {y2})")
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

def generate_frames():
    global camera
    placeholder_frame = (cv2.imread(PLACEHOLDER_FRAME_PATH) if os.path.exists(PLACEHOLDER_FRAME_PATH) 
                         else 255 * np.ones((480, 640, 3), dtype=np.uint8))

    parking_areas = None
    frame_skip = 15  # Liczba klatek do pominięcia dla przyspieszenia
    frame_counter = 0  # Licznik klatek

    last_no_frame_log_time = 0  # Czas ostatniego logu "Kamera nie dostarcza klatek"
    log_interval = 10  # Minimalny odstęp między logami (w sekundach)

    while True:
        try:
            with camera_lock:
                # log_memory_usage()
                if camera and camera.isOpened():
                    ret, frame = camera.read()
                    if not ret:
                        current_time = time.time()
                        if current_time - last_no_frame_log_time > log_interval:
                            log_event("Kamera nie dostarcza klatek. Wyświetlanie klatki zastępczej.")
                            last_no_frame_log_time = current_time
                        frame = placeholder_frame
                    else:
                        frame_counter += 1

                        # Pomiń co frame_skip klatkę
                        if frame_counter % frame_skip != 0:
                            continue  # Pomijamy tę klatkę

                        # Debug - logowanie odczytania klatki
                        # log_event("Klatka kamery odczytana pomyślnie. Numer klatki: {}".format(frame_counter))

                        parking_areas = detect_parking_areas(frame)
                        
                        # Debug - wypisywanie ilosci wykrytych miejsc parkingowych
                        # log_event(f"Wykryto {len(parking_areas)} miejsc parkingowych.")

                        if parking_areas:
                            draw_parking_boxes(frame, parking_areas)
                else:
                    current_time = time.time()
                    if current_time - last_no_frame_log_time > log_interval:
                        log_event("Brak aktywnego źródła wideo. Wyświetlanie klatki zastępczej.")
                        last_no_frame_log_time = current_time
                    frame = placeholder_frame

            success, buffer = cv2.imencode('.jpg', frame)
            if not success:
                raise ValueError("Nie udało się zakodować klatki do JPEG.")

            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        except Exception as e:
            log_event(f"Błąd w generatorze klatek: {str(e)}")
            time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_source', methods=['POST'])
def set_source():
    global camera
    source = request.form.get('source')

    with camera_lock:
        if camera:
            log_event("Zwalnianie poprzedniego źródła.")
            camera.release()
            camera = None

        if source == 'camera':
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                log_event("Nie udało się otworzyć kamery.")
                return "Nie udało się otworzyć kamery!", 500
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            log_event("Źródło ustawione: Kamera na żywo.")
        elif source == 'video':
            if not os.path.exists(DEFAULT_VIDEO_PATH):
                log_event("Nie znaleziono domyślnego pliku wideo!")
                return "Nie znaleziono domyślnego pliku wideo!", 404
            camera = cv2.VideoCapture(DEFAULT_VIDEO_PATH)
            if not camera.isOpened():
                log_event("Nie udało się otworzyć pliku wideo.")
                return "Nie udało się otworzyć pliku wideo!", 500
            log_event(f"Źródło ustawione: Wideo z pliku ({DEFAULT_VIDEO_PATH}).")

    return "Źródło ustawione", 200

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