import pytesseract
import cv2
import numpy as np

from miscellaneous import is_bbox_in_roi, process_roi
from log_tools import *

# Modele YOLOv8
from roboflow import Roboflow
from ultralytics import YOLO
rf = Roboflow(api_key="FWlZpKPCE4GysrCWg6LC")

# Detekcja miejsc parkingowych
project = rf.workspace("muhammad-syihab-bdynf").project("parking-space-ipm1b")
version = project.version(4)
model = version.model

# Detekcja samochodów
car_project = rf.workspace("arac-zxyoi").project("car-detect-zefse")
car_version = car_project.version(2)
car_model = car_version.model

def detect_license_plate(frame, cars):
    """Wykrywanie tekstu z tablicy rejestracyjnej tylko wtedy, gdy bounding box samochodu nachodzi na ROI."""
    # Definiowanie dwóch obszarów zainteresowania (ROI)
    roi1 = (1600, 200, 1900, 550)  # Pierwszy obszar
    roi2 = (500, 330, 700, 650)  # Drugi obszar

    # Debug - Zaznacz obszary ROI na klatce
    # cv2.rectangle(frame, (roi1[0], roi1[1]), (roi1[2], roi1[3]), (0, 255, 255), 2)  # Żółty prostokąt dla ROI1
    # cv2.rectangle(frame, (roi2[0], roi2[1]), (roi2[2], roi2[3]), (255, 255, 0), 2)  # Cyjanowy prostokąt dla ROI2

    # Przetwarzanie tylko wtedy, gdy bounding box samochodu nachodzi na ROI
    detected_texts = []
    for car in cars:
        x1, y1, x2, y2 = car  # Współrzędne bounding boxa samochodu

        # Sprawdź, czy bounding box samochodu nachodzi na którykolwiek z ROI
        if is_bbox_in_roi((x1, y1, x2, y2), roi1):
            roi = frame[roi1[1]:roi1[3], roi1[0]:roi1[2]]  # Wycinamy ROI1
            processed_roi, text = process_roi(roi)  # Przetwarzamy ROI1
            if text:
                detected_texts.append(text)
                frame[roi1[1]:roi1[3], roi1[0]:roi1[2]] = cv2.resize(processed_roi, (roi1[2] - roi1[0], roi1[3] - roi1[1]))  # Przywróć przetworzony ROI

        if is_bbox_in_roi((x1, y1, x2, y2), roi2):
            roi = frame[roi2[1]:roi2[3], roi2[0]:roi2[2]]  # Wycinamy ROI2
            processed_roi, text = process_roi(roi)  # Przetwarzamy ROI2
            if text:
                detected_texts.append(text)
                frame[roi2[1]:roi2[3], roi2[0]:roi2[2]] = cv2.resize(processed_roi, (roi2[2] - roi2[0], roi2[3] - roi2[1]))  # Przywróć przetworzony ROI

    return frame, detected_texts
    
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

def detect_cars(frame):
    """Wykorzystanie modelu do wykrywania samochodów."""
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = car_model.predict(frame_rgb, confidence=15, overlap=35).json()  # Dostosuj parametry

    cars = []
    for prediction in results['predictions']:
        if prediction['class'] == 'car':  # Upewnij się, że klasa to 'car'
            x = int(prediction['x'] - prediction['width'] / 2)
            y = int(prediction['y'] - prediction['height'] / 2)
            w = int(prediction['width'])
            h = int(prediction['height'])
            cars.append((x, y, x + w, y + h))

    return cars