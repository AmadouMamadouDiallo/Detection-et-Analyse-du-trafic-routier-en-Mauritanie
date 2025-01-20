import cv2
import numpy as np
from .yolo_model import TrafficDetector
from typing import List, Dict, Optional
import os
import time

class VideoProcessor:
    def __init__(self):
        self.detector = TrafficDetector()
        self.trajectories = {}  # Pour stocker les trajectoires des objets
        self.next_id = 0  # Pour attribuer des IDs uniques aux objets

    def get_object_id(self, detection, prev_detections):
        """Attribue un ID à un objet en fonction de sa position"""
        x1, y1, x2, y2 = detection['bbox']
        center = ((x1 + x2) / 2, (y1 + y2) / 2)
        
        # Chercher l'objet le plus proche dans les détections précédentes
        min_dist = float('inf')
        best_id = None
        
        for obj_id, prev_pos in prev_detections.items():
            px, py = prev_pos['center']
            dist = ((center[0] - px) ** 2 + (center[1] - py) ** 2) ** 0.5
            if dist < min_dist and dist < 50:  # Seuil de distance
                min_dist = dist
                best_id = obj_id
        
        if best_id is None:
            best_id = self.next_id
            self.next_id += 1
        
        return best_id

    def process_video_feed(self, video_path: str) -> Dict:
        try:
            # Créer le dossier de sortie pour la vidéo traitée
            output_dir = os.path.join(os.path.dirname(video_path), 'processed')
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, 'processed_' + os.path.basename(video_path))
            
            # Ouvrir la vidéo
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception(f"Impossible d'ouvrir la vidéo: {video_path}")

            # Obtenir les propriétés de la vidéo
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            # Créer le writer pour la vidéo de sortie
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

            results = []
            frame_count = 0
            prev_detections = {}
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                
                # Détecter les véhicules dans la frame
                detections, annotated_frame = self.detector.detect_vehicles(frame)
                current_detections = {}
                
                # Traiter chaque détection
                for detection in detections:
                    obj_id = self.get_object_id(detection, prev_detections)
                    current_detections[obj_id] = {
                        'center': ((detection['bbox'][0] + detection['bbox'][2]) / 2,
                                 (detection['bbox'][1] + detection['bbox'][3]) / 2),
                        'class': detection['class']
                    }
                    
                    # Mettre à jour la trajectoire
                    if obj_id not in self.trajectories:
                        self.trajectories[obj_id] = []
                    self.trajectories[obj_id].append(current_detections[obj_id]['center'])
                    
                    # Dessiner la trajectoire
                    if len(self.trajectories[obj_id]) > 1:
                        points = np.array(self.trajectories[obj_id], np.int32)
                        points = points.reshape((-1, 1, 2))
                        cv2.polylines(annotated_frame, [points], False, (0, 255, 255), 2)
                
                # Calculer le niveau de congestion
                congestion_level = self.detector.calculate_congestion(detections)
                
                # Ajouter le compteur sur l'image
                cv2.putText(annotated_frame, f"Vehicules: {len(detections)}", (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(annotated_frame, f"Congestion: {congestion_level:.2%}", (10, 70),
                          cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Sauvegarder la frame annotée
                out.write(annotated_frame)
                
                # Sauvegarder les résultats
                result = {
                    'frame_number': frame_count,
                    'detections': detections,
                    'congestion_level': congestion_level,
                    'trajectories': {str(k): v for k, v in self.trajectories.items()}
                }
                results.append(result)
                
                prev_detections = current_detections

            cap.release()
            out.release()
            
            return {
                'results': results,
                'output_video': output_path,
                'trajectories': self.trajectories
            }

        except Exception as e:
            print(f"Erreur lors du traitement de la vidéo: {e}")
            return None

def process_video_feed(video_source):
    processor = VideoProcessor()
    return processor.process_video_feed(video_source)
