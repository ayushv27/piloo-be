from django.test import TestCase

# Create your tests here.
import cv2
import time
import os
from datetime import datetime
from ultralytics import YOLO
from your_django_project.tasks import save_detection_task  # 
#  Update to your Django task import
 
# Load YOLOv8 model
model = YOLO("yolov8n.pt")  # Or yolov8s.pt, yolov8m.pt, etc.
# Initialize video capture (0 = webcam, or replace with RTSP URL)
cap = cv2.VideoCapture("0")
# Frame save/output directories
output_dir = "detected_frames"
os.makedirs(output_dir, exist_ok=True)
# Frame rate for processing and output video
processing_interval = 1.0  # seconds
last_processed_time = 0
# Prepare video writer
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
video_out = cv2.VideoWriter('output.mp4', fourcc, 1.0, (frame_width, frame_height))  # 1 FPS output
print("[INFO] Starting detection...")
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("[INFO] End of stream or failed frame read.")
        break
    current_time = time.time()
    # Process only one frame per second
    if current_time - last_processed_time >= processing_interval:
        timestamp = datetime.now().isoformat()
        last_processed_time = current_time
        # Run YOLOv8 inference
        results = model(frame)
        annotated_frame = results[0].plot()
        boxes = results[0].boxes
        # Save annotated frame as JPEG
        filename_time = timestamp.replace(":", "_").replace(".", "_")
        image_filename = f"frame_{filename_time}.jpg"
        image_path = os.path.join(output_dir, image_filename)
        cv2.imwrite(image_path, annotated_frame)
        # Write frame into output video
        video_out.write(annotated_frame)
        # Send detection info to Celery asynchronously
        for box in boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].cpu().numpy().tolist()
            # Async task to store in DB via Django ORM
            save_detection_task.delay(
                timestamp=timestamp,
                label=label,
                confidence=conf,
                bbox=xyxy,
                image_path=image_path
            )
        # Optional: show frame in a window
        cv2.imshow("YOLO Annotated", annotated_frame)
    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
# Cleanup
cap.release()
video_out.release()
cv2.destroyAllWindows()
print("[INFO] Detection finished. Video saved to output.mp4")
