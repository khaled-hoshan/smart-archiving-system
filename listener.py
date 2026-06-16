import serial
import cv2
import requests
import time

# --- CONFIG ---
SERIAL_PORT = "/dev/rfcomm0"
LAPTOP_IP = "192.168.1.XX"  # <--- MUST MATCH YOUR LAPTOP IP
URL = f"http://{LAPTOP_IP}:5000/upload"

try:
    ser = serial.Serial(SERIAL_PORT, 9600, timeout=1)
    print("✅ Bluetooth Port Opened Successfully.")
except:
    print(
        "❌ ERROR: Could not open /dev/rfcomm0. Try running: sudo rfcomm bind rfcomm0 [MAC]"
    )
    exit()

camera = cv2.VideoCapture(0)

print("👂 Listening... Press 'A' on the Arduino now.")

while True:
    if ser.in_waiting:
        # We read the raw data to see EXACTLY what is arriving
        raw_data = ser.readline().decode().strip()
        print(f"📩 I just received: '{raw_data}'")

        if raw_data == "CAPTURE":
            print("📸 Command Match! Taking photo...")
            ret, frame = camera.read()
            if ret:
                cv2.imwrite("temp.jpg", frame)
                try:
                    print(f"📡 Attempting to send to laptop at {URL}...")
                    with open("temp.jpg", "rb") as f:
                        r = requests.post(URL, files={"file": f}, timeout=5)
                    print(f"✅ Laptop responded: {r.status_code}")
                except Exception as e:
                    print(f"❌ Network Error: Could not reach Laptop. {e}")
