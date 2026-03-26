import cv2
import threading
import time
from collections import deque

class CameraStream:
    def __init__(self, source=0, width=640, height=480):
        self.cap = cv2.VideoCapture(int(source) if str(source).isdigit() else source)
        self.width = width
        self.height = height
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Failed to open video source: {source}")

        self.ret = False
        self.frame = None
        self.stopped = False
        self.frame_id = 0  # <--- NEW: Tracks unique frames
        
        self.sequence_buffer = deque(maxlen=16) 

        self.thread = threading.Thread(target=self._update, args=())
        self.thread.daemon = True
        self.thread.start()

    def _update(self):
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps == 0 or fps is None:
            fps = 30.0 
            
        frame_time = 1.0 / fps

        while not self.stopped:
            start_time = time.time()
            
            ret, frame = self.cap.read()
            
            if not ret:
                time.sleep(0.1)
                continue
            
            frame = cv2.resize(frame, (self.width, self.height))
            
            self.ret = True
            self.frame = frame
            self.frame_id += 1 # <--- NEW: Increment ID
            self.sequence_buffer.append(frame) 
                
            process_time = time.time() - start_time
            sleep_time = frame_time - process_time
            
            if sleep_time > 0:
                time.sleep(sleep_time)

    def get_frame(self):
        # NEW: Return the frame AND its unique ID
        if self.ret and self.frame is not None:
            return self.frame.copy(), self.frame_id
        return None, None
        
    def get_recent_sequence(self):
        # NEW: Return the sequence AND the latest ID
        if len(self.sequence_buffer) == 16:
            return list(self.sequence_buffer), self.frame_id
        return None, None

    def release(self):
        self.stopped = True
        if self.thread.is_alive():
            self.thread.join()
        self.cap.release()