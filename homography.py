import cv2
import numpy as np
import glob

image_files = sorted(glob.glob("*.jpg"))

ground_points_inches = [
    [81,-21], [90,21], [50,18],
    [60,-17], [44,0], [20,-17], [25,13]
]

METERS_PER_INCH = 0.0254
ground_points_meters = np.array(
    ground_points_inches, dtype=np.float32
) * METERS_PER_INCH

def segment_orange_cone(image_bgr, min_area=50):
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    lower_orange1 = np.array([0, 70, 170], dtype=np.uint8)
    upper_orange1 = np.array([35, 255, 255], dtype=np.uint8)

    lower_orange2 = np.array([35, 90, 190], dtype=np.uint8)
    upper_orange2 = np.array([50, 255, 255], dtype=np.uint8)

    mask1 = cv2.inRange(hsv, lower_orange1, upper_orange1)
    mask2 = cv2.inRange(hsv, lower_orange2, upper_orange2)
    mask = cv2.bitwise_or(mask1, mask2)

    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None

    best = max(contours, key=cv2.contourArea)
    if cv2.contourArea(best) < min_area:
        return None

    x, y, w, h = cv2.boundingRect(best)
    return (x, y, w, h)

pixel_points = []

for path in image_files:
    img = cv2.imread(path)

    bbox = segment_orange_cone(img)

    if bbox is None:
        print(f"X No cone detected in {path}")
        continue

    x, y, w, h = bbox

    u = x + w / 2
    v = y + h

    pixel_points.append([u, v])

    cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
    cv2.circle(img, (int(u), int(v)), 5, (0,0,255), -1)

    cv2.imshow("debug", img)
    cv2.waitKey(200)

cv2.destroyAllWindows()

pixel_points = np.array(pixel_points, dtype=np.float32)

print("\nPixel points:")
print(pixel_points)

print("\nGround points:")
print(ground_points_meters)


H, status = cv2.findHomography(pixel_points, ground_points_meters)

# Test homography matrix on the same images

def uv_to_world(u, v, H):
    pt = np.array([[u], [v], [1.0]], dtype=np.float64)
    xy = H @ pt
    xy /= xy[2, 0]
    return float(xy[0, 0]), float(xy[1, 0])

print("\n--- HOMOGRAPHY TEST ---")

for i, path in enumerate(image_files):
    img = cv2.imread(path)

    bbox = segment_orange_cone(img)
    if bbox is None:
        print(f"{path}: no detection (skipping)")
        continue

    x, y, w, h = bbox
    u = x + w / 2
    v = y + h

    x_w, y_w = uv_to_world(u, v, H)

    gt_x, gt_y = ground_points_meters[i]

    error = np.sqrt((x_w - gt_x)**2 + (y_w - gt_y)**2)

    print(f"\nImage: {path}")
    print(f"Predicted: ({x_w:.3f}, {y_w:.3f})")
    print(f"Ground:    ({gt_x:.3f}, {gt_y:.3f})")
    print(f"Error:     {error:.3f} m")

    # visualization
    vis = img.copy()
    cv2.rectangle(vis, (x,y), (x+w,y+h), (0,255,0), 2)
    cv2.circle(vis, (int(u), int(v)), 6, (0,0,255), -1)

    cv2.putText(vis, f"X:{x_w:.2f} Y:{y_w:.2f}",
                (x, y-10), cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (255,0,0), 2)

    cv2.imshow("homography test", vis)
    cv2.waitKey(500)

cv2.destroyAllWindows()

# Live homography test

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Cannot open camera")
    exit()

print("\n--- LIVE HOMOGRAPHY TEST ---")
print("Press 'q' to quit")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    bbox = segment_orange_cone(frame)

    if bbox is not None:
        x, y, w, h = bbox

        u = x + w / 2
        v = y + h

        x_w, y_w = uv_to_world(u, v, H)

        print(f"X: {x_w:.3f} m | Y: {y_w:.3f} m")

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
        cv2.circle(frame, (int(u), int(v)), 6, (0,0,255), -1)

        cv2.putText(frame,
                    f"X:{x_w:.2f} Y:{y_w:.2f}",
                    (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255,0,0),
                    2)

    cv2.imshow("Live Homography Test", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print("\nHomography matrix:")
print(H)

# Save

np.save("homography.npy", H)
print("\nSaved homography.npy")