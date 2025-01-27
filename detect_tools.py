import pytesseract
import cv2
import numpy as np

from pytesseract import Output
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

def detect_license_plate(frame):
    """Wykrywanie tekstu z tablicy rejestracyjnej na klatce wideo."""
    # Resize the image to make it easier to process
    resized_frame = cv2.resize(frame, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # Convert the image to gray scale
    gray = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)

    # Apply bilateral filter to reduce noise while keeping edges sharp
    gray = cv2.bilateralFilter(gray, 11, 17, 17)

    # Perform edge detection
    edged = cv2.Canny(gray, 30, 200)

    # Find contours
    contours, _ = cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    license_plate = None

    for cnt in contours:
        # Approximate the contour
        epsilon = 0.018 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        # If the contour has 4 sides, assume it might be the license plate
        if len(approx) == 4:
            license_plate = approx
            break

    if license_plate is not None:
        # Create a mask for the license plate and extract it
        mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.drawContours(mask, [license_plate], 0, 255, -1)
        
        # Extract the region of interest (ROI)
        x, y, w, h = cv2.boundingRect(license_plate)
        roi = gray[y:y+h, x:x+w]

        # Deskew the ROI if necessary
        if h > w:
            roi = cv2.rotate(roi, cv2.ROTATE_90_CLOCKWISE)

        # Apply thresholding to make text more distinct
        roi = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        # Perform OCR on the ROI
        text = pytesseract.image_to_string(roi, config='--psm 8')
        log_event(f"Detected License Plate Text: {text.strip()}")

        # Draw the contour and detected text on the original image
        cv2.drawContours(resized_frame, [license_plate], -1, (0, 255, 0), 3)
        cv2.putText(resized_frame, text.strip(), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        return resized_frame, text.strip()
    else:
        log_event("No license plate detected.")
        return frame, None
    
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