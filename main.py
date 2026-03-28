import cv2
import os
import time
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup

# If you install face_recognition later, it can do deep-learning face matching.
# For now, we fall back to a simple template matching / Cascade approach if not installed.
try:
    import face_recognition
    HAS_FR = True
except ImportError:
    HAS_FR = False

class FaceTrackerApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        
        # UI Elements
        self.top_bar = BoxLayout(size_hint=(1, 0.1))
        
        self.status_label = Label(text="Initializing...", color=(0, 1, 0, 1))
        self.top_bar.add_widget(self.status_label)
        
        if HAS_FR:
            self.upload_btn = Button(text="Upload Target Face")
            self.upload_btn.bind(on_press=self.open_filechooser)
            self.top_bar.add_widget(self.upload_btn)
        else:
            self.status_label.text = "Install 'face_recognition' for specific photo tracking. Currently tracking largest face."
        
        self.layout.add_widget(self.top_bar)
        
        # Camera Display
        self.img_display = Image()
        self.layout.add_widget(self.img_display)
        
        # Face Detection Setup
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.capture = cv2.VideoCapture(0)
        
        # Set a lower resolution for faster processing if writing to a microcontroller
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Coordinate Logging Setup
        # On Android, we would write to the external storage directory.
        # Locally, we write to the same folder.
        self.log_file_path = "face_coordinates.txt"
        with open(self.log_file_path, "w") as f:
            f.write("Time, Center_X, Center_Y\n")
            
        self.target_encoding = None
        
        # Schedule the update function at ~30 FPS
        Clock.schedule_interval(self.update, 1.0 / 30.0)
        
        return self.layout

    def open_filechooser(self, instance):
        # Create a FileChooser inside a Popup
        self.filechooser = FileChooserIconView(filters=['*.png', '*.jpg', '*.jpeg'])
        
        layout = BoxLayout(orientation='vertical')
        layout.add_widget(self.filechooser)
        
        btn_layout = BoxLayout(size_hint=(1, 0.1))
        select_btn = Button(text="Select")
        select_btn.bind(on_press=self.load_target_face)
        cancel_btn = Button(text="Cancel")
        
        btn_layout.add_widget(select_btn)
        btn_layout.add_widget(cancel_btn)
        layout.add_widget(btn_layout)
        
        self.popup = Popup(title="Choose a photo of the target person", content=layout, size_hint=(0.9, 0.9))
        cancel_btn.bind(on_press=self.popup.dismiss)
        self.popup.open()

    def load_target_face(self, instance):
        selection = self.filechooser.selection
        if selection and HAS_FR:
            image_path = selection[0]
            try:
                # Load image and compute face encoding
                ref_image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(ref_image)
                if len(encodings) > 0:
                    self.target_encoding = encodings[0]
                    self.status_label.text = f"Target Face Loaded! Tracking only this face."
                else:
                    self.status_label.text = "No face found in uploaded image."
            except Exception as e:
                self.status_label.text = f"Error loading image: {str(e)}"
        self.popup.dismiss()

    def update(self, dt):
        ret, frame = self.capture.read()
        if not ret:
            return

        # Flip the frame for a mirror effect (more natural)
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        center_x, center_y = None, None

        if HAS_FR and self.target_encoding is not None:
            # --- Specific Person Tracking (face_recognition / dlib) ---
            # Shrink for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Find all faces and encodings in the current frame
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces([self.target_encoding], face_encoding, tolerance=0.6)
                if matches[0]:
                    # Scale back up
                    top *= 4; right *= 4; bottom *= 4; left *= 4
                    
                    center_x = left + (right - left) // 2
                    center_y = top + (bottom - top) // 2
                    
                    # Draw Bounding Box
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                    cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                    break # Track the first match we find
        else:
            # --- Fallback: Largest Face Tracking (OpenCV Haar Cascades) ---
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(50, 50))
            
            # Find largest face (assumed to be the main target)
            largest_face = None
            max_area = 0
            for (x, y, fw, fh) in faces:
                if fw * fh > max_area:
                    max_area = fw * fh
                    largest_face = (x, y, fw, fh)
            
            if largest_face:
                x, y, fw, fh = largest_face
                center_x = x + fw // 2
                center_y = y + fh // 2
                
                # Draw Bounding Box and Center point
                cv2.rectangle(frame, (x, y), (x + fw, y + fh), (0, 255, 0), 2)
                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)

        # Log coordinates if a face is tracked
        if center_x is not None and center_y is not None:
            with open(self.log_file_path, "a") as f:
                f.write(f"{time.time():.3f}, {center_x}, {center_y}\n")
            
            if not self.target_encoding:  # Only update label if not locked on specific face
                 self.status_label.text = f"Tracking: X={center_x}, Y={center_y}"

        # Convert the frame to a Kivy Texture
        # OpenCV uses BGR, but Kivy expects RGB or BGR(A) depending on configuration.
        # It's safest to convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create a texture containing the 2D image data
        texture = Texture.create(size=(w, h), colorfmt='rgb')
        # Flip vertically because Kivy's coordinate system starts from bottom-left
        texture.blit_buffer(rgb_frame.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
        texture.flip_vertical()
        
        # Update the image widget
        self.img_display.texture = texture

    def on_stop(self):
        # Release the camera when the app stops
        self.capture.release()

if __name__ == '__main__':
    FaceTrackerApp().run()
