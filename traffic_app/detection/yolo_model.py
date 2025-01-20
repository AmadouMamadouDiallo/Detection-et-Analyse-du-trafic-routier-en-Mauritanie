from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Dict, Tuple
import torch

class TrafficDetector:
    def __init__(self):
        # Charger le modèle YOLOv8
        try:
            self.model = YOLO('yolov8n.pt')
        except Exception as e:
            print(f"Erreur lors du chargement du modèle: {e}")
            raise
            
        # Classes pertinentes pour la détection du trafic
        self.target_classes = {
            2: 'car',      # voiture
            3: 'motorcycle',  # moto
            5: 'bus',      # bus
            7: 'truck'     # camion
        }
    
    def detect_vehicles(self, frame: np.ndarray) -> Tuple[List[Dict], np.ndarray]:
        if frame is None:
            return [], np.array([])
            
        # Faire une copie du frame pour le dessin
        display_frame = frame.copy()
        
        try:
            # Prédiction avec YOLOv8
            results = self.model(frame, verbose=False)
            detections = []
            
            # Traiter chaque détection
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    cls = int(box.cls[0])
                    # Vérifier si la classe est un véhicule que nous voulons détecter
                    if cls in self.target_classes:
                        conf = float(box.conf[0])
                        xyxy = box.xyxy[0].cpu().numpy()
                        
                        detection = {
                            'class': self.target_classes[cls],
                            'confidence': conf,
                            'bbox': xyxy.tolist()
                        }
                        detections.append(detection)
                        
                        # Dessiner la boîte sur l'image
                        x1, y1, x2, y2 = map(int, xyxy)
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        label = f"{self.target_classes[cls]} {conf:.2f}"
                        cv2.putText(display_frame, label, (x1, y1 - 10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            return detections, display_frame
            
        except Exception as e:
            print(f"Erreur lors de la détection: {e}")
            return [], frame

    def calculate_congestion(self, detections: List[Dict]) -> float:
        if not detections:
            return 0.0
            
        # Calculer le niveau de congestion basé sur le nombre de véhicules
        # et leur proximité
        vehicle_count = len(detections)
        
        # Seuil de base pour la congestion
        base_threshold = 5  # Considéré comme trafic normal
        max_threshold = 15  # Considéré comme congestion maximale
        
        # Calculer le niveau de congestion normalisé
        congestion_level = min(1.0, vehicle_count / max_threshold)
        
        return congestion_level
