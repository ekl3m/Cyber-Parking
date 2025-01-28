import cv2
import time
import threading
import numpy as np

from database_tools import add_parking_event
from pytesseract import image_to_string
from log_tools import log_event
from enum import Enum

def is_bbox_in_roi(bbox, roi):
    """Sprawdza, czy bounding box nachodzi na obszar ROI."""
    x1, y1, x2, y2 = bbox  # Współrzędne bounding boxa samochodu
    roi_x1, roi_y1, roi_x2, roi_y2 = roi  # Współrzędne ROI

    # Sprawdzenie, czy bounding box nachodzi na ROI
    return not (x2 < roi_x1 or x1 > roi_x2 or y2 < roi_y1 or y1 > roi_y2)

def process_roi(roi):
    """Przetwarza pojedynczy ROI w celu wykrycia tekstu na tablicy rejestracyjnej."""
    # Resize the image to make it easier to process
    resized_roi = cv2.resize(roi, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # Convert the image to gray scale
    gray = cv2.cvtColor(resized_roi, cv2.COLOR_BGR2GRAY)

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
        text = image_to_string(roi, config='--psm 8').strip()
        text = clean_text(text)

        # Sprawdź, czy tekst ma dokładnie 8 znaków
        if len(text) == 8 and text[0].isalpha():
            # Debug - text detected by tesseract
            # log_event(f"Detected License Plate Text: {text}")

            # Draw the contour and detected text on the original image
            cv2.drawContours(resized_roi, [license_plate], -1, (0, 255, 0), 3)
            cv2.putText(resized_roi, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

            return resized_roi, text
        else:
            # Debug - text ignored by tesseract
            # log_event(f"Ignored text (not 8 characters): {text}")
            return None, None
    else:
        return None, None

# Enum, który umozliwia kontrole nad bramkami
class GateAction(Enum):
    ENTRY_OPEN = "Bramka wjazdowa się otwiera."
    ENTRY_CLOSE = "Bramka wjazdowa się zamyka."
    EXIT_OPEN = "Bramka wyjazdowa się otwiera."
    EXIT_CLOSE = "Bramka wyjazdowa się zamyka."

# Funkcja, ktora zajmuje sie obsluga bramek
def manage_gates(action: GateAction, plate_number: str = None):
    """
    Zarządza stanem bramek i loguje odpowiedni komunikat.

    :param action: GateAction - określa akcję do wykonania
    :param plate_number: Numer rejestracyjny samochodu (opcjonalny)
    """
    if isinstance(action, GateAction):
        log_event(action.value)

        if action in {GateAction.ENTRY_OPEN, GateAction.EXIT_OPEN} and plate_number:
            add_parking_event(plate_number, "ENTRY" if action == GateAction.ENTRY_OPEN else "EXIT")
    else:
        raise ValueError("Niepoprawna akcja dla bramki")
    
def delayed_manage_gates(action: GateAction, delay: int):
    """
    Opóźnia zamknięcie bramki po określonym czasie.

    :param action: GateAction - określa akcję do wykonania
    :param delay: Czas opóźnienia w sekundach
    """
    def close_gate():
        time.sleep(delay)
        manage_gates(action)
    
    threading.Thread(target=close_gate, daemon=True).start()
    
# Funkcja do czyszczenia tekstu z nieprzewidywalnych znakow
def clean_text(text):
    cleaned_text = ""
    for char in text:
        if char.isalnum() or char.isspace():  # Sprawdź, czy znak jest literą, cyfrą lub spacją
            cleaned_text += char
    return cleaned_text
    