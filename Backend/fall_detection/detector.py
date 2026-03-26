import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

import time
import cv2
import torch
import numpy as np
import tensorflow as tf
from collections import deque
from ultralytics import YOLO

class FallDetector:
    def __init__(
        self,
        pose_model_path="fall_detection/models/yolo11n-pose.pt",
        lstm_model_path="fall_detection/models/activity_lstm_4class.keras",
        sequence_length=30,
        confidence_threshold=0.6,
        immobility_seconds=5
    ):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pose_model = YOLO(pose_model_path)
        self.lstm_model = tf.keras.models.load_model(lstm_model_path)

        self.sequence_length = sequence_length
        self.confidence_threshold = confidence_threshold
        self.class_names = ["Walk", "Sit", "Fall", "Lie"]

        self.sequence = deque(maxlen=self.sequence_length)
        self.prev_hip_y = None
        self.fall_detected = False
        self.emergency_triggered = False

        self.training_max_value = 3840.0
        
        # Simpler thresholds tied to frame shape, not time
        self.min_drop_ratio = 0.05 # An 8% drop in screen height over a few frames
        self.immobility_threshold = 0.03

        self.immobile_start_time = None
        self.required_immobile_seconds = immobility_seconds
        
        # Frame-based memory for fast drops (no time.time() needed)
        self.recent_drops = deque(maxlen=10) # Look back at the last 10 frames
        
    def _extract_keypoints(self, results):
        if (
            results[0].keypoints is None
            or results[0].keypoints.xy is None
            or len(results[0].keypoints.xy) == 0
        ):
            return np.zeros(34), None

        kpts = results[0].keypoints.xy[0].cpu().numpy()
        return kpts.flatten(), kpts

    def process_frame(self, frame):
        current_time = time.time()

        results = self.pose_model(frame, verbose=False)
        keypoints_flat, kpts = self._extract_keypoints(results)
        
        # Always pad sequence (1 frame = 1 sequence entry)
        self.sequence.append(keypoints_flat)

        # ---------------- Frame-Aware Motion Analysis ----------------
        hip_y = None
        if kpts is not None and len(kpts) > 12:
            hip_y = (kpts[11][1] + kpts[12][1]) / 2

            if self.prev_hip_y is not None:
                drop_distance = hip_y - self.prev_hip_y
                drop_ratio = drop_distance / frame.shape[0]
                
                # Keep a history of recent drops
                self.recent_drops.append(drop_ratio)
            
            self.prev_hip_y = hip_y
        else:
            self.prev_hip_y = None
            self.recent_drops.append(0.0)

        # Ensure we have enough frames to make a prediction
        if len(self.sequence) < self.sequence_length:
            return {
                "label": "Collecting",
                "confidence": 0.0,
                "fall_detected": False,
                "emergency": False
            }

        # ---------------- LSTM Prediction ----------------
        input_data = np.expand_dims(
            np.array(self.sequence) / self.training_max_value,
            axis=0
        )

        probs = self.lstm_model.predict(input_data, verbose=0)[0]
        confidence = float(np.max(probs))

        predicted_class = None
        if confidence >= self.confidence_threshold:
            predicted_class = self.class_names[np.argmax(probs)]

        # ==========================================
        # Improved Fall Logic (Frame Memory)
        # ==========================================
        # Calculate cumulative drop over the last 10 frames
        total_recent_drop = sum([d for d in self.recent_drops if d > 0])
        
        # Trigger Fall if LSTM explicitly says "Fall" OR (LSTM says "Lie" right after a sudden drop)
        if predicted_class == "Fall" or (predicted_class == "Lie" and total_recent_drop > self.min_drop_ratio):
            if not self.fall_detected:
                self.fall_detected = True
                self.emergency_triggered = False
                self.immobile_start_time = None

        # ==========================================
        # Time-Based Immobility Detection
        # ==========================================
        if self.fall_detected and predicted_class in ["Lie", "Fall", "Uncertain"]:
            frame_displacement = 0
            if self.prev_hip_y and hip_y:
                frame_displacement = abs(hip_y - self.prev_hip_y) / frame.shape[0]

            if frame_displacement < self.immobility_threshold:
                if self.immobile_start_time is None:
                    self.immobile_start_time = time.time()
            else:
                self.immobile_start_time = None

            if self.immobile_start_time is not None:
                elapsed = time.time() - self.immobile_start_time
                if elapsed >= self.required_immobile_seconds:
                    self.emergency_triggered = True

        # ==========================================
        # Reset Logic (Recovery)
        # ==========================================
        # If they get up and sit/walk, reset the alert state
        if self.fall_detected and predicted_class in ["Walk", "Sit"]:
            self.fall_detected = False
            self.emergency_triggered = False
            self.immobile_start_time = None
            self.recent_drops.clear() # clear memory

        return {
            "label": predicted_class if predicted_class else "Uncertain",
            "confidence": confidence,
            "fall_detected": self.fall_detected,
            "emergency": self.emergency_triggered
        }