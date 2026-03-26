import cv2
import numpy as np
import importlib
from collections import deque
from .evm_processor import EVMProcessor

# ==========================================
# Robust Face Detector Setup
# ==========================================
mp_face = None
face_detector = None
USE_MEDIAPIPE = False

for _mod in (
    'mediapipe.solutions.face_detection',
    'mediapipe.python.solutions.face_detection',
    'mediapipe.face_detection'
):
    try:
        mp_face = importlib.import_module(_mod)
        break
    except Exception:
        continue

if mp_face is not None:
    try:
        face_detector = mp_face.FaceDetection(
            model_selection=1,
            min_detection_confidence=0.7
        )
        USE_MEDIAPIPE = True
    except Exception:
        face_detector = None

# Fallback: OpenCV Haar cascade if MediaPipe is unavailable
if not USE_MEDIAPIPE:
    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        opencv_face_cascade = cv2.CascadeClassifier(cascade_path)
    except Exception:
        opencv_face_cascade = None

# ==========================================
# OpenCV Tracker Version Handler
# ==========================================
def create_tracker():
    """Robust helper to handle OpenCV version differences for trackers"""
    try:
        # Try modern OpenCV 4.5.1+ legacy namespace
        return cv2.legacy.TrackerKCF_create()
    except AttributeError:
        try:
            # Try older OpenCV / standard contrib namespace
            return cv2.TrackerKCF_create()
        except AttributeError:
            raise RuntimeError(
                "TrackerKCF not found. Please run: pip install opencv-contrib-python"
            )

# ==========================================
# Clean Service Class for Backend Integration
# ==========================================
class EVMService:
    def __init__(
        self,
        fs=30,
        min_face_width=120,
        min_detection_confidence=0.7,
        multiple_faces=False,
        face_tracking=True,
        debug=False
    ):
        self.debug = debug
        self.fs = fs
        self.min_face_width = min_face_width
        self.multiple_faces = multiple_faces
        self.face_tracking = face_tracking
        self.min_detection_confidence = min_detection_confidence

        # internal detection scheduling
        self.frame_counter = 0
        self.detection_interval = 5

        if USE_MEDIAPIPE and face_detector is not None:
            self.face_detector = face_detector
            self.use_mediapipe = True
        else:
            self.face_detector = None
            self.use_mediapipe = False
            self.opencv_face_cascade = opencv_face_cascade

        # tracking state
        self.trackers = {}
        self.tracking_lost_frames = {}
        self.face_counter = 0
        self.MAX_TRACKING_LOST_FRAMES = 10

        # per-face EVM data
        self.evm_processors = {}
        self.face_colors = {}
        self.bpm_history = {}
        self.current_frame_data = []

    def _is_same_face(self, boxA, boxB):
        """
        Uses Center-Point (Centroid) distance instead of strict overlap.
        This survives frame-dropping and fast sudden movements.
        """
        # Center of Box A
        cx_A = (boxA[0] + boxA[2]) / 2.0
        cy_A = (boxA[1] + boxA[3]) / 2.0
        
        # Center of Box B
        cx_B = (boxB[0] + boxB[2]) / 2.0
        cy_B = (boxB[1] + boxB[3]) / 2.0
        
        # Calculate distance between centers
        distance = np.sqrt((cx_A - cx_B)**2 + (cy_A - cy_B)**2)
        
        # Calculate face width
        face_width = boxA[2] - boxA[0]
        
        # If the center moved less than 1.5x the width of the face, it's the same person
        return distance < (face_width * 1.5)

    def _calculate_forehead_roi(self, x1, y1, x2, y2):
        face_height = y2 - y1
        face_width = x2 - x1
        fh_y1 = y1
        fh_y2 = y1 + int(face_height * 0.45)
        fh_x1 = x1 + int(face_width * 0.15)
        fh_x2 = x2 - int(face_width * 0.2)
        if fh_x2 > fh_x1 and fh_y2 > fh_y1:
            if (fh_x2 - fh_x1) >= 20 and (fh_y2 - fh_y1) >= 10:
                return fh_x1, fh_y1, fh_x2, fh_y2
        return None

    def _calculate_bpm_accuracy(self, history):
        if len(history) < 3:
            return None
        recent = list(history)[-10:]
        mean = float(np.mean(recent))
        std = float(np.std(recent))
        return {
            "mean": mean, "std": std,
            "min": float(np.min(recent)), "max": float(np.max(recent))
        }

    def process_frame(self, frame):
        """
        Ingests a frame, updates trackers, runs EVM, and returns structured JSON.
        """
        faces_detected = []
        response = {"faces": []}
        self.current_frame_data = []

        self.frame_counter += 1
        if not self.face_tracking:
            run_detection = True
        elif len(self.trackers) == 0:
            run_detection = True
        else:
            run_detection = (self.frame_counter % self.detection_interval) == 0

        # Update existing trackers
        if self.face_tracking and len(self.trackers) > 0:
            to_remove = []
            for fid, tr in list(self.trackers.items()):
                try:
                    ok, bb = tr.update(frame)
                except Exception:
                    ok = False
                    bb = None

                if not ok or bb is None:
                    self.tracking_lost_frames[fid] = self.tracking_lost_frames.get(fid, 0) + 1
                    if self.tracking_lost_frames[fid] > self.MAX_TRACKING_LOST_FRAMES:
                        to_remove.append(fid)
                    continue

                x, y, w_box, h_box = [int(v) for v in bb]
                x1, y1, x2, y2 = x, y, x + w_box, y + h_box
                face_width = x2 - x1
                if face_width < self.min_face_width:
                    self.tracking_lost_frames[fid] = self.tracking_lost_frames.get(fid, 0) + 1
                    continue

                self.tracking_lost_frames[fid] = 0
                faces_detected.append({
                    'bbox': (x1, y1, x2, y2),
                    'face_id': fid,
                    'detection_score': 0.0,
                    'is_tracked': True
                })

            for fid in to_remove:
                try:
                    del self.trackers[fid]
                except Exception:
                    pass
                self.tracking_lost_frames.pop(fid, None)

        # Run Face Detection
        if run_detection:
            if self.use_mediapipe and self.face_detector is not None:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = self.face_detector.process(rgb)
                if result.detections:
                    for i, detection in enumerate(result.detections):
                        score = detection.score[0]
                        if score < self.min_detection_confidence:
                            continue
                        bbox = detection.location_data.relative_bounding_box
                        h, w = frame.shape[:2]
                        x1 = max(0, int(bbox.xmin * w))
                        y1 = max(0, int(bbox.ymin * h))
                        x2 = min(w, int((bbox.xmin + bbox.width) * w))
                        y2 = min(h, int((bbox.ymin + bbox.height) * h))
                        
                        face_width = x2 - x1
                        if face_width < self.min_face_width:
                            continue
                        if not self.multiple_faces and len(faces_detected) > 0:
                            continue
                        
                        is_new = True
                        for existing in faces_detected:
                            # CHANGED: Use _is_same_face instead of _bbox_iou
                            if self._is_same_face((x1,y1,x2,y2), existing['bbox']):
                                if score > existing['detection_score']:
                                    existing['bbox'] = (x1,y1,x2,y2)
                                    existing['detection_score'] = score
                                fid = existing['face_id']
                                if self.face_tracking and fid in self.trackers:
                                    tr_new = create_tracker() # Updated!
                                    tr_new.init(frame, (x1, y1, face_width, y2-y1))
                                    self.trackers[fid] = tr_new
                                    self.tracking_lost_frames[fid] = 0
                                is_new = False
                                break
                        if is_new:
                            fid = self.face_counter
                            self.face_counter += 1
                            if self.face_tracking:
                                tr = create_tracker() # Updated!
                                tr.init(frame, (x1, y1, face_width, y2-y1))
                                self.trackers[fid] = tr
                                self.tracking_lost_frames[fid] = 0
                            faces_detected.append({
                                'bbox': (x1, y1, x2, y2),
                                'face_id': fid,
                                'detection_score': score,
                                'is_tracked': False
                            })

        # Process BPM for each face
        for f in faces_detected:
            x1,y1,x2,y2 = f['bbox']
            fid = f['face_id']
            face_width = x2-x1
            
            if fid not in self.evm_processors:
                self.evm_processors[fid] = EVMProcessor(fs=self.fs, debug=self.debug)
                self.bpm_history[fid] = deque(maxlen=20)

            roi_coords = self._calculate_forehead_roi(x1,y1,x2,y2)
            bpm=None; confidence="LOW"; accuracy=None; peak_dom=0.0; sig_q=0.0; motion_r=0.0
            
            if roi_coords:
                rx1,ry1,rx2,ry2 = roi_coords
                roi = frame[ry1:ry2, rx1:rx2]

                evm = self.evm_processors[fid]
                bpm, confidence = evm.update(roi)
                dbg = evm.get_debug_info()
                peak_dom = dbg.get('peak_dominance',0.0)
                sig_q = dbg.get('signal_quality',0.0)
                motion_r = dbg.get('motion_ratio',0.0)
                
                if bpm:
                    self.bpm_history[fid].append(bpm)
                    accuracy = self._calculate_bpm_accuracy(self.bpm_history[fid])
            
            clean_bpm = int(round(bpm)) if bpm is not None else None
            clean_accuracy = None
            if accuracy:
                clean_accuracy = {
                    "mean": float(round(accuracy["mean"], 1)),
                    "std": float(round(accuracy["std"], 1)),
                    "min": int(round(accuracy["min"])),
                    "max": int(round(accuracy["max"]))
                }

            face_result = {
                "face_id": int(fid),
                "bpm": clean_bpm,
                "confidence": confidence,
                "peak_dominance": int(round(peak_dom * 100)),
                "signal_quality": int(round(sig_q * 100)),
                "motion_ratio": int(round(motion_r * 100)),
                "accuracy": clean_accuracy,
                "bbox": f['bbox']
            }
            response["faces"].append(face_result)
            
            self.current_frame_data.append({
                "face_id": fid,
                "bbox": f['bbox'],
                "is_tracked": f.get('is_tracked', False)
            })
            
        return response

    def reset(self):
        for evm in self.evm_processors.values():
            evm.reset()
        self.evm_processors.clear()
        self.bpm_history.clear()
        self.trackers.clear()
        self.tracking_lost_frames.clear()