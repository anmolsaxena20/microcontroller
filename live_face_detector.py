import cv2
import time
import os
import serial  # Ensure 'pyserial' is installed: uv add pyserial

# --- Configuration ---
SERIAL_PORT = 'COM9'  # Updated to your PORT9
BAUD_RATE = 9600
LOG_FILE = "face_coordinates.txt"


# --- SENSOR-ACTUATOR OFFSET COMPENSATION ---
# Adjust these values (in pixels) to align your laser with your face
OFFSET_X = 0  # Increase to move laser Right, Decrease for Left
OFFSET_Y = 0  # Increase to move laser Down, Decrease for Up
# --------------------------------------------

# --- Arduino Serial Initialization ---
print(f"[STEP 1] Connecting to Arduino on {SERIAL_PORT}...")
try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    time.sleep(2) # CRITICAL: Wait for Arduino to reset before sending data
    HAS_SERIAL = True
    print(f"SUCCESS: Arduino connected on {SERIAL_PORT}")
except Exception as e:
    HAS_SERIAL = False
    arduino = None
    print(f"WARNING: Arduino NOT connected ({e}). Logging to file only.")

# --- Improved Import Logic (MediaPipe/Haar Fallback) ---
HAS_MEDIAPIPE = False
try:
    from mediapipe.python.solutions import face_detection as mp_face_detection
    face_detection = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5)
    HAS_MEDIAPIPE = True
except:
    # Use Haar Cascade as reliable fallback
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')
    if face_cascade.empty():
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def main():
    print("\n[STEP 2] Initializing Camera Hardware...")
    print("        (Wait 3-5 seconds for first frame on Windows)")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("[ERROR] Camera not accessible. Is another app using it?")
        return

    time.sleep(1.0) # Warm up
    print("\n" + "="*40)
    print("   LASER TRACKER ACTIVE (COM9)")
    print("="*40)
    print("-> Press 'q' to stop.")

    # Prep Log file
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("Time, Center_X, Center_Y\n")

    try:
        while True:
            ret, frame = cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1) # Mirroring matches physical head move
            h, w, _ = frame.shape
            center_x, center_y = None, None

            # --- Detection Routine ---
            if HAS_MEDIAPIPE:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_detection.process(rgb)
                if results.detections:
                    best = max(results.detections, key=lambda d: d.score[0])
                    bbox = best.location_data.relative_bounding_box
                    center_x = int((bbox.xmin + bbox.width / 2) * w)
                    center_y = int((bbox.ymin + bbox.height / 2) * h)
                    # Draw visual box
                    cv2.rectangle(frame, (int(bbox.xmin*w), int(bbox.ymin*h)), 
                                  (int((bbox.xmin+bbox.width)*w), int((bbox.ymin+bbox.height)*h)), (0, 255, 0), 2)
            else:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # scaleFactor, minNeighbors, minSize
                faces = face_cascade.detectMultiScale(gray, 1.1, 7, minSize=(60,60))
                if len(faces) > 0:
                    (x, y, fw, fh) = max(faces, key=lambda f: f[2]*f[3])
                    center_x, center_y = x + fw // 2, y + fh // 2
                    cv2.rectangle(frame, (x, y), (x + fw, y + fh), (255, 120, 0), 2)

            # --- Live Data Pipe (Direct to Serial + Log) ---
            if center_x is not None:
                # APPLY OFFSET COMPENSATION
                piped_x = center_x + OFFSET_X
                piped_y = center_y + OFFSET_Y
                
                # Constrain to screen bounds so servos don't crash
                piped_x = w - max(0, min(w, piped_x))
                piped_y = max(0, min(h, piped_y))   
                # 1. Pipe to Serial (Format: "X,Y\n" e.g "320,240\n")
                if HAS_SERIAL:
                    arduino.write(f"{piped_x},{piped_y}\n".encode())
                
                # 2. Log to Text
                with open(LOG_FILE, "a") as f:
                    f.write(f"{time.time():.3f}, {center_x}, {center_y}\n")

                # UI Overlay
                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                cv2.putText(frame, f"PIPED: {piped_x},{piped_y} (COM9)", (15, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "STATUS: TARGET LOST...", (15, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            cv2.imshow("Laser Face Tracker - Ready", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

    except KeyboardInterrupt:
        print("\nShutdown by user.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        if HAS_SERIAL: arduino.close()
        print("System Deactivated.")

if __name__ == "__main__":
    main()
