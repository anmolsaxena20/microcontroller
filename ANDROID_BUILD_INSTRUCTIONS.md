# Testing and Building Your Face Tracker App

## 1. Test Locally on Windows First
Before building the APK, make sure the camera and interface work exactly as you want on your laptop!

### Install Requirements
Open your terminal and run:
`uv add kivy opencv-python`

If you want the app to be able to "Lock On" to a specific uploaded photo of a person (instead of just tracking the largest face), you must also install `face_recognition`:
`uv add face_recognition` \*(Note: this requires CMake and C++ build tools on Windows)*

### Run the App
`python main.py`

This will open a window with your webcam feed. The coordinates will be continuously written to `face_coordinates.txt` in this folder.

---

## 2. Build the APK using Google Colab
Since `Buildozer` doesn't run natively on Windows, the fastest way to get your `.apk` is using Google Colab. It takes about 10-15 minutes to run.

### Steps:
1. Go to [Google Colab](https://colab.research.google.com/) and create a **New Notebook**.
2. **Upload your files**: On the left sidebar, click the "Folder" icon and upload `main.py` and `buildozer.spec` from your `microcontroller` folder into the Colab environment.
3. In the first code block of the notebook, paste and run this to install Buildozer's dependencies:
   ```bash
   !pip install buildozer cython==0.29.33
   !sudo dpkg --add-architecture i386
   !sudo apt-get update
   !sudo apt-get install -y build-essential libltdl-dev libffi-dev libssl-dev python3-dev
   !sudo apt-get install -y python3-setuptools libncurses5:i386 libstdc++6:i386 zlib1g:i386
   !sudo apt-get install -y openjdk-17-jdk unzip ccache git
   ```
4. Create a second code block, paste and run this to build the APK:
   ```bash
 andro
   ```
5. **Download the APK**: Once it finishes (it will take a while the first time), go back to the File Explorer on the left. Open the `bin/` folder. You will see an `.apk` file there. Download it, send it to your phone via WhatsApp, and install!

> **Speed on Android**: You asked if Python/OpenCV is fast enough to pipe coordinates to a microcontroller. Yes! Tracking a single face using Haar Cascades usually runs at ~15-30 FPS on modern Android phones. We've optimized the camera resolution in `main.py` specifically so your microcontroller servos will feel smooth and responsive.
