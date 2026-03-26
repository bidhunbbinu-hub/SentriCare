
import cv2
import threading
from collections import deque
import os
from database.db import SessionLocal
from database.models import Alert

class RollingVideoRecorder:
    def __init__(self, fps=30, pre_seconds=15, post_seconds=15):
        self.fps = fps
        
        self.pre_frames = fps * pre_seconds
        self.post_frames = fps * post_seconds
        
        
        self.buffer = deque(maxlen=self.pre_frames)
        
        self.is_recording = False
        self.frames_left = 0
        self.current_alert_id = None
        self.recording_buffer = []
        
        
        self.output_dir = "video_clips"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def add_frame(self, frame):
        
        small_frame = cv2.resize(frame, (640, 480))
        self.buffer.append(small_frame)
        
        if self.is_recording:
            self.recording_buffer.append(small_frame)
            self.frames_left -= 1
            
            if self.frames_left <= 0:
                self._finish_recording()
                
    def trigger(self, alert_id):
        if not self.is_recording:
            print(f"🎥 Started recording 60-second clip for Alert {alert_id}...")
            self.is_recording = True
            self.current_alert_id = alert_id
            self.frames_left = self.post_frames
            
            self.recording_buffer = list(self.buffer) 
            
    def _finish_recording(self):
        self.is_recording = False
        frames_to_save = self.recording_buffer
        alert_id = self.current_alert_id
        
       
        self.recording_buffer = []
        self.current_alert_id = None
        
       
        threading.Thread(target=self._save_to_disk, args=(frames_to_save, alert_id), daemon=True).start()
        
    def _save_to_disk(self, frames, alert_id):
        if not frames: return
        
        filename = f"alert_{alert_id}.webm"
        filepath = os.path.join(self.output_dir, filename)
        
        height, width, _ = frames[0].shape
        
        fourcc = cv2.VideoWriter_fourcc(*'VP80') 
        out = cv2.VideoWriter(filepath, fourcc, self.fps, (width, height))
        
        for f in frames:
            out.write(f)
        out.release()
        
        print(f"✅ Video saved successfully: {filepath}")
        
       
        db = SessionLocal()
        try:
            alert = db.query(Alert).filter(Alert.id == alert_id).first()
            if alert:
                alert.video_clip_path = f"/clips/{filename}"
                db.commit()
        finally:
            db.close()

indoor_recorder = RollingVideoRecorder()
outdoor_recorder = RollingVideoRecorder()