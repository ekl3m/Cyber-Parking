import cv2

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