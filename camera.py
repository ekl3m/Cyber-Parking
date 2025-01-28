import cv2
import os
import time
import threading
import numpy as np

from miscellaneous import manage_gates, delayed_manage_gates, GateAction
from database_tools import *
from detect_tools import *
from draw_tools import *
from log_tools import *

camera = None
camera_lock = threading.Lock()  # Blokada dla obsługi kamery

last_no_frame_log_time = 0  # Czas ostatniego logu "Kamera nie dostarcza klatek"
log_interval = 10  # Minimalny odstęp między logami (w sekundach)

# Sciezki plikow
DEFAULT_VIDEO_PATH = '/Users/sqstudio/Desktop/Studia/Przetwarzanie_Sygnałów_i_Obrazów/cyber-parking/static/sample2.mp4'
PLACEHOLDER_FRAME_PATH = '/Users/sqstudio/Desktop/Studia/Przetwarzanie_Sygnałów_i_Obrazów/cyber-parking/static/placeholder.jpg'

def set_camera(source):
    global camera
    with camera_lock:
        if camera:
            camera.release()
            camera = None

        if source == 'camera':
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                raise RuntimeError("Nie udało się otworzyć kamery.")
        elif source == 'video':
            if not os.path.exists(DEFAULT_VIDEO_PATH):
                raise RuntimeError("Nie znaleziono domyślnego pliku wideo!")
            camera = cv2.VideoCapture(DEFAULT_VIDEO_PATH)
            if not camera.isOpened():
                raise RuntimeError("Nie udało się otworzyć pliku wideo.")

def generate_frames():
    global camera, last_no_frame_log_time
    placeholder_frame = (cv2.imread(PLACEHOLDER_FRAME_PATH) if os.path.exists(PLACEHOLDER_FRAME_PATH) 
                         else 255 * np.ones((480, 640, 3), dtype=np.uint8))

    parking_areas = None
    cars = None
    frame_skip = 15  # Liczba klatek do pominięcia dla przyspieszenia
    frame_counter = 0  # Licznik klatek

    while True:
        try:
            with camera_lock:
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

                        if frame_counter % frame_skip != 0:
                            continue  # Pomijamy tę klatkę

                        parking_areas = detect_parking_areas(frame)
                        cars = detect_cars(frame)
                        frame, detected_texts = detect_license_plate(frame, cars)

                        for text in detected_texts:
                            last_event = get_last_event(text)
                            current_time = time.time()

                            if not last_event or (last_event["action"] == "EXIT" and current_time - last_event["timestamp"] > 30):
                                add_parking_event(text, "ENTRY")  # Zapis do bazy danych
                                log_event(f"Samochód o numerze rejestracyjnym {text} wjeżdża na parking.")
                                manage_gates(GateAction.ENTRY_OPEN)  # Otwórz bramkę wjazdową
                                delayed_manage_gates(GateAction.ENTRY_CLOSE, 30) # Zamknij bramkę wjazdową po 30 sekundach
                                

                        for text in detected_texts:
                            last_event = get_last_event(text)
                            current_time = time.time()

                            if last_event and last_event["action"] == "ENTRY" and current_time - last_event["timestamp"] > 30:
                                add_parking_event(text, "EXIT")  # Zapis do bazy danych
                                log_event(f"Samochód o numerze rejestracyjnym {text} opuszcza parking.")
                                manage_gates(GateAction.EXIT_OPEN)  # Otwórz bramkę wyjazdową
                                delayed_manage_gates(GateAction.EXIT_CLOSE, 30) # Zamknij bramkę wyjazdową po 30 sekundach

                        if parking_areas:
                            draw_parking_boxes(frame, parking_areas)
                        if cars:
                            draw_car_boxes(frame, cars)
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