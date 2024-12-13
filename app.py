from flask import Flask, render_template, request, Response
import cv2
import os

app = Flask(__name__)
camera = None

# Domyślny plik wideo
DEFAULT_VIDEO_PATH = os.path.join('static', 'sample.mp4')

def generate_frames():
    global camera
    while True:
        if camera:
            ret, frame = camera.read()
            if not ret:
                break
            # Kodowanie klatki do formatu JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            
            # Strumieniowanie JPEG do klienta
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_source', methods=['POST'])
def set_source():
    global camera
    source = request.form.get('source')

    if source == 'camera':
        camera = cv2.VideoCapture(0)  # Kamera na żywo
    elif source == 'video':
        video_path = DEFAULT_VIDEO_PATH  # Wczytaj domyślne wideo
        if not os.path.exists(video_path):
            return "Nie znaleziono domyślnego pliku wideo!", 404
        camera = cv2.VideoCapture(video_path)

    return "Źródło ustawione", 200

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, port=8080)