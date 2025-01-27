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