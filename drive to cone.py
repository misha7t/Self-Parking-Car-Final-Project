import cv2
import numpy as np
import serial
import time
import math
 
CAMERA_INDEX  = 0        
BAUD_RATE     = 115200
MICROBIT_PORT = "COM5"   
 
FORWARD_SPEED = 0.22     # m/s
TURN_SPEED_R  = 80       # deg/s
TURN_SPEED_L  = 68      # deg/s
STOP_DISTANCE = 0.005     # stopping distance from cone in meters
MIN_CONE_AREA = 50       # minimum area segmented to detect cone
 
# Homography matrix
H = np.array([
    [ 3.07253378e-05,  8.27601866e-04, -6.51989643e-01],
    [-8.62209974e-04,  8.05998627e-05,  2.57592498e-01],
    [ 6.35221706e-05, -3.88238975e-03,  1.00000000e+00]
], dtype=np.float64)
 
def segment_orange_cone(image_bgr, min_area=MIN_CONE_AREA):
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
 
    lower1 = np.array([0,  70, 170], dtype=np.uint8)
    upper1 = np.array([35, 255, 255], dtype=np.uint8)
    lower2 = np.array([35,  90, 190], dtype=np.uint8)
    upper2 = np.array([50, 255, 255], dtype=np.uint8)
 
    mask = cv2.bitwise_or(
        cv2.inRange(hsv, lower1, upper1),
        cv2.inRange(hsv, lower2, upper2)
    )
 
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
 
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
 
    best = max(contours, key=cv2.contourArea)
    if cv2.contourArea(best) < min_area:
        return None
 
    return cv2.boundingRect(best)
 
def uv_to_xy(u, v, H):
    pt = np.array([[u], [v], [1.0]])
    xy = H @ pt
    xy /= xy[2, 0]
    return float(xy[0, 0]), float(xy[1, 0])
 
def send_command(ser, cmd, duration=None):
    ser.write((cmd + "\n").encode())
    print(f"  → {cmd}" + (f" for {duration:.2f}s" if duration else ""))
    if duration:
        time.sleep(duration)
        ser.write(("S\n").encode())
        time.sleep(0.1)
 
def compute_commands(x_m, y_m):
    drive_distance  = max(0, math.sqrt(x_m**2 + y_m**2) - STOP_DISTANCE)
    turn_angle_rad  = math.atan2(y_m, x_m)
    turn_angle_deg  = math.degrees(turn_angle_rad)
    turn_time_l       = abs(turn_angle_deg) / TURN_SPEED_L
    turn_time_r       = abs(turn_angle_deg) / TURN_SPEED_R
    drive_time      = drive_distance / FORWARD_SPEED
 
    print(f"\nCone world position: x={x_m:.3f}m forward, y={y_m:.3f}m lateral")
    print(f"Turn left angle:     {turn_angle_deg:.1f}°  ({turn_time_l:.2f}s)")
    print(f"Turn right angle:     {turn_angle_deg:.1f}°  ({turn_time_r:.2f}s)")
    print(f"Drive distance: {drive_distance:.3f}m  ({drive_time:.2f}s)")
 
    return turn_angle_deg, turn_time_l, turn_time_r, drive_time
 
def main():
    print("Opening camera — press SPACE to capture, Q to quit...")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("ERROR: Could not open camera.")
        return
 
    photo = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        cv2.putText(frame, "Press SPACE to capture", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow("Camera — press SPACE to capture", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            photo = frame.copy()
            break
        elif key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            return
 
    cap.release()
    cv2.destroyAllWindows()
 
    if photo is None:
        print("No photo taken.")
        return
 
    # Detect cone
    print("\nDetecting cone...")
    bbox = segment_orange_cone(photo)
 
    if bbox is None:
        print("ERROR: No cone detected. Check lighting or cone colour.")
        cv2.imshow("No cone found — press any key to close", photo)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        return
 
    x, y, w, h = bbox
    u_cone = x + w / 2
    v_cone = y + h
 
    # Compute world coordinates
    x_m, y_m = uv_to_xy(u_cone, v_cone, H)
 
    # Compute command sequence
    turn_angle_deg, turn_time_l, turn_time_r, drive_time = compute_commands(x_m, y_m)
 
    # Show detection and confirm
    cv2.rectangle(photo, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.circle(photo, (int(u_cone), int(v_cone)), 6, (0, 0, 255), -1)
    cv2.putText(photo, f"x={x_m:.2f}m  y={y_m:.2f}m",
                (x, max(0, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.putText(photo, "SPACE = drive   Q = cancel",
                (20, photo.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.imshow("Cone detected — SPACE to drive, Q to cancel", photo)
    print("\nClick the image window then press SPACE to drive, Q to cancel.")
 
    confirmed = False
    while True:
        key = cv2.waitKey(0) & 0xFF
        if key == ord(' '):
            confirmed = True
            break
        elif key == ord('q'):
            break
 
    cv2.destroyAllWindows()
 
    if not confirmed:
        print("Cancelled.")
        return
 
    # Connect and send commands
    print(f"\nConnecting to micro:bit on {MICROBIT_PORT}...")
    ser = serial.Serial(MICROBIT_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    send_command(ser, "S")
 
    # Turn
    if abs(turn_angle_deg) > 2:
        if turn_angle_deg > 0:
            direction = "R"
            duration = turn_time_r
        else:
            direction = "L"
            duration = turn_time_l
        print(f"\nStep 1: Turning {'left' if direction == 'L' else 'right'}...")
        send_command(ser, direction, duration)
        time.sleep(0.3)
 
    # Drive forward
    if drive_time > 0:
        print(f"\nStep 2: Driving forward...")
        send_command(ser, "F", drive_time)
 
    # Stop
    send_command(ser, "S")
    print("\nDone — car should be at cone.")
    ser.close()
 
if __name__ == "__main__":
    main()