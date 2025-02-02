import cv2

from database_tools import save_parking_change

def draw_debug_area(frame, y_min=900, y_max=1200, color=(0, 0, 255), alpha=0.5):
    """
    Rysuje półprzezroczysty prostokąt na obszarze ignorowanym przez detekcję.
    
    :param frame: Obraz wejściowy (numpy array)
    :param y_min: Dolna granica obszaru
    :param y_max: Górna granica obszaru
    :param color: Kolor prostokąta w formacie BGR
    :param alpha: Przezroczystość (0 - całkowicie przezroczyste, 1 - całkowicie nieprzezroczyste)
    """
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, y_min), (frame.shape[1], y_max), color, -1)  # Wypełniony prostokąt
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)  # Nałożenie półprzezroczystego efektu
    
    # Dodanie tekstu informacyjnego
    cv2.putText(frame, "Ignored Area", (10, y_min + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    return frame

def draw_parking_boxes(frame, parking_areas, plate_number=None):
    height, width, _ = frame.shape
    black_band_top = (height // 3) - 20
    black_band_bottom = 2 * height // 3

    enumerate_id = 1  # Numerowanie miejsc nad czarnym pasem


    for (x1, y1, x2, y2, status) in sorted(parking_areas):
        # Sprawdź, czy współrzędne prostokąta znajdują się poza "czarnym pasem"
        if y1 >= black_band_top and y2 <= black_band_bottom:
            continue
        if y1 >= 900 and y2 <= 1200:
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
        # Jeśli box znajduje się nad czarnym pasem, dodaj numerację
        if y1 < black_band_top:
            cv2.putText(frame, str(enumerate_id), (x1 + (x2 - x1) // 2, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            enumerate_id += 1
        # Jeśli box znajduje się pod czarnym pasem, dodaj numerację powyżej
        if y2 > black_band_bottom:
            cv2.putText(frame, str(enumerate_id), (x1 + (x2 - x1) // 2, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            enumerate_id += 1

        save_parking_change(enumerate_id, status, plate_number)

def draw_car_boxes(frame, cars):
    for (x1, y1, x2, y2) in cars:
        color = (255, 0, 0)  # Niebieski dla samochodów
        label = 'Car'
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

# Debug - funkcja do wskazywania ROI
def draw_roi_areas(frame):
    """Funkcja do rysowania obszarów ROI na klatce w celach debugowania."""
    # Definiowanie dwóch obszarów zainteresowania (ROI)
    roi1 = (1600, 200, 1900, 550)  # (x1, y1, x2, y2) - pierwszy obszar
    roi2 = (500, 350, 700, 650)  # (x1, y1, x2, y2) - drugi obszar

    # Rysowanie prostokątów wokół ROI
    cv2.rectangle(frame, (roi1[0], roi1[1]), (roi1[2], roi1[3]), (0, 255, 255), 2)  # Żółty prostokąt dla ROI1
    cv2.rectangle(frame, (roi2[0], roi2[1]), (roi2[2], roi2[3]), (255, 255, 0), 2)  # Cyjanowy prostokąt dla ROI2

    return frame