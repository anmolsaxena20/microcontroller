import cv2
import threading
from flask import Flask, Response, render_template_string
import webbrowser
import time

app = Flask(__name__)

# Load the pre-trained Haar Cascade classifier for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def generate_frames():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, 'Face', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            
            # Yield frame over HTTP in multipart format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    cap.release()

@app.route('/')
def index():
    return render_template_string('''
    <html>
        <head>
            <title>Real-time Face Detection</title>
            <style>
                body { text-align: center; font-family: Arial, sans-serif; background-color: #121212; color: white; margin-top: 50px; }
                #video-container { 
                    display: inline-block;
                    border: 4px solid #4CAF50;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 15px rgba(0, 255, 0, 0.2);
                }
                img { display: block; }
            </style>
        </head>
        <body>
            <h1>Real-time Face Detection</h1>
            <div id="video-container">
                <img src="{{ url_for('video_feed') }}" width="640" height="480">
            </div>
            <p style="color: #bbb; margin-top: 20px;">Press Ctrl+C in the terminal to close the server</p>
        </body>
    </html>
    ''')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

def open_browser():
    # Give the Flask server a second to start
    time.sleep(1.5)
    webbrowser.open_new_tab('http://127.0.0.1:5000/')

if __name__ == '__main__':
    # Start the browser thread
    threading.Thread(target=open_browser, daemon=True).start()
    # Run the Flask server
    app.run(host='0.0.0.0', port=5000, debug=False)
