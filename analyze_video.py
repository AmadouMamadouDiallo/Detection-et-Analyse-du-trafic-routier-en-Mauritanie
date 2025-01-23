from ultralytics import YOLO
import cv2
import numpy as np
from datetime import datetime

def analyze_video(video_path):
    # Load the YOLO model
    model = YOLO('yolov8n.pt')

    # Open the video file
    cap = cv2.VideoCapture(video_path)
    
    # Get video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    
    # Create output video writer
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f'analyzed_video_{timestamp}.mp4'
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
    
    # Initialize counters
    vehicle_count = 0
    frame_count = 0
    
    print("Starting video analysis...")
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break
            
        frame_count += 1
        
        # Run YOLOv8 inference on the frame
        results = model(frame)
        
        # Process the results
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # Get box coordinates
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                
                # Get class and confidence
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                
                # Get class name
                class_name = model.names[cls]
                
                # Filter for vehicles (car, truck, bus, motorcycle)
                vehicle_classes = ['car', 'truck', 'bus', 'motorcycle']
                if class_name in vehicle_classes and conf > 0.3:
                    # Draw bounding box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Add label
                    label = f'{class_name} {conf:.2f}'
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    vehicle_count += 1
        
        # Add frame information
        cv2.putText(frame, f'Vehicles detected: {vehicle_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Write the frame to output video
        out.write(frame)
        
        # Print progress every 100 frames
        if frame_count % 100 == 0:
            print(f"Processed {frame_count} frames...")
    
    # Release everything
    cap.release()
    out.release()
    
    print(f"\nAnalysis complete!")
    print(f"Total vehicles detected: {vehicle_count}")
    print(f"Output saved as: {output_path}")

if __name__ == "__main__":
    video_path = r"C:\Users\PC\Downloads\Test.mp4"
    analyze_video(video_path)
