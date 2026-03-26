import torch
import torch.nn.functional as F
import time
from collections import deque

from .model import TransformerAnomaly
from .featureExtractor import extract_features_from_frames

class ExternalAnomalyEngine:
    def __init__(self, model_path="external_detection/Models/modelmid.pt", threshold=0.75):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.model = TransformerAnomaly().to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
        
        self.threshold = threshold
        self.window_size = 16
        
        # REMOVED: self.frame_buffer = deque(maxlen=self.window_size)
        
        self.last_inference_time = time.time()
        self.inference_cooldown = 1.0 

    # CHANGED: Now accepts a full list of 16 frames instead of 1 frame
    def process_sequence(self, frames_list):
        current_time = time.time()
        
        # Check if cooldown has passed and we have exactly 16 frames
        if frames_list and len(frames_list) == self.window_size and (current_time - self.last_inference_time) > self.inference_cooldown:
            self.last_inference_time = current_time
            
            features = extract_features_from_frames(frames_list)
            x = features.unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                logits = self.model(x)
                probs = F.softmax(logits, dim=1)
                
                # Correctly pulling the anomaly score (index 1)
                anomaly_score = probs[0,1].item()
                
            is_anomaly = anomaly_score > self.threshold
            
            return {
                "status": "ANOMALY" if is_anomaly else "NORMAL",
                "score": float(anomaly_score),
                "is_anomaly": bool(is_anomaly)
            }

        return None