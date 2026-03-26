from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import Config
from frame_engine import FrameEngine
from alerts.alert_manager import alert_system
import threading
import cv2
import asyncio
import time
from websocket.ws_manager import manager
from database.db import engine, SessionLocal
from database.models import Base
from alerts.alert_router import router as alerts_router
from camera.camera_stream import CameraStream
from auth.auth_router import router as auth_router
from patients.patient_router import router as patient_router
from external_detection.anomaly_engine import ExternalAnomalyEngine
from video_recorder import indoor_recorder, outdoor_recorder
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.makedirs("video_clips", exist_ok=True)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)
app.mount("/clips", StaticFiles(directory="video_clips"), name="clips")

app.include_router(alerts_router)
app.include_router(auth_router)
app.include_router(patient_router)

indoor_camera = CameraStream(source="videos/indoor2.mp4", width=Config.CAMERA_WIDTH, height=Config.CAMERA_HEIGHT)
outdoor_camera = CameraStream(source=0, width=Config.CAMERA_WIDTH, height=Config.CAMERA_HEIGHT)
frame_engine = FrameEngine()
outdoor_engine = ExternalAnomalyEngine(threshold=0.75)

latest_status = {}
active_cameras = {}
CURRENT_CAMERA_ID = 1

# --- STATE VARIABLES ---
is_shutting_down = False
latest_indoor_jpeg = None
latest_outdoor_jpeg = None
main_loop = None

@app.on_event("startup")
def start_processing():
    global main_loop
    main_loop = asyncio.get_running_loop()
    
    threading.Thread(target=stream_loop, daemon=True).start()
    threading.Thread(target=process_loop, daemon=True).start()

@app.on_event("shutdown")
def shutdown_event():
    global is_shutting_down
    print("Initiating server shutdown... stopping camera loops.")
    is_shutting_down = True
    indoor_camera.release()
    outdoor_camera.release()


def stream_loop():
    """Reads frames quickly for the live video feeds."""
    global is_shutting_down, latest_indoor_jpeg, latest_outdoor_jpeg
    
    last_in_id = -1
    last_out_id = -1
    
    while not is_shutting_down:
        # 1. Handle Indoor Stream (Only if it's a NEW frame)
        in_data = indoor_camera.get_frame()
        if in_data[0] is not None and in_data[1] != last_in_id:
            in_frame, in_id = in_data
            last_in_id = in_id  # Remember this frame
            
            indoor_recorder.add_frame(in_frame)
            ret, buffer = cv2.imencode('.jpg', in_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            if ret: latest_indoor_jpeg = buffer.tobytes()

        # 2. Handle Outdoor Stream (Only if it's a NEW frame)
        out_data = outdoor_camera.get_frame()
        if out_data[0] is not None and out_data[1] != last_out_id:
            out_frame, out_id = out_data
            last_out_id = out_id # Remember this frame
            
            outdoor_recorder.add_frame(out_frame)
            ret, buffer = cv2.imencode('.jpg', out_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
            if ret: latest_outdoor_jpeg = buffer.tobytes()
                
        # Briefly yield CPU to prevent 100% lockup
        time.sleep(0.01)


# --- HEAVY AI PROCESSING LOOP ---
def process_loop():
    global latest_status, is_shutting_down, main_loop

    last_in_id = -1
    last_out_seq_id = -1

    while not is_shutting_down:
        
        # 1. Process Indoor Fall/EVM (Only if it's a NEW frame)
        in_data = indoor_camera.get_frame()
        if in_data[0] is not None and in_data[1] != last_in_id:
            in_frame, in_id = in_data
            last_in_id = in_id
            
            result = frame_engine.process(in_frame, camera_id=CURRENT_CAMERA_ID)
            
            future = asyncio.run_coroutine_threadsafe(
                alert_system.evaluate(result), main_loop
            )
            alert = future.result()
            latest_status = {
                "data": result,
                "alert": alert
            }

        # 2. Process Outdoor Sequence (Only if sequence has updated)
        out_seq_data = outdoor_camera.get_recent_sequence()
        if out_seq_data[0] is not None and out_seq_data[1] != last_out_seq_id:
            out_frames_sequence, out_seq_id = out_seq_data
            last_out_seq_id = out_seq_id
            
            outdoor_result = outdoor_engine.process_sequence(out_frames_sequence)
            if outdoor_result:
                print(f"Outdoor Security Result: {outdoor_result['status']} (Score: {outdoor_result['score']:.3f})")
            
            if outdoor_result and outdoor_result["is_anomaly"]:
                print(f"🚨 OUTDOOR ANOMALY DETECTED! Score: {outdoor_result['score']:.2f}")
                
                alert_data = {
                    "camera_id": 2, 
                    "outdoor_anomaly": True,
                    "anomaly_score": outdoor_result["score"],
                    "fall": {"fall_detected": False, "emergency": False},
                    "heart_rate": {"faces": []}
                }
                asyncio.run_coroutine_threadsafe(
                    alert_system.evaluate(alert_data), main_loop
                )

        
        time.sleep(0.01)

async def generate_indoor_frames():
    global is_shutting_down, latest_indoor_jpeg
    last_sent = None # Keep track of the last frame sent
    try:
        while not is_shutting_down:
           
            if latest_indoor_jpeg is not None and latest_indoor_jpeg != last_sent:
                last_sent = latest_indoor_jpeg
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + latest_indoor_jpeg + b'\r\n')
            
           
            await asyncio.sleep(0.01) 
    except asyncio.CancelledError:
        pass

async def generate_outdoor_frames():
    global is_shutting_down, latest_outdoor_jpeg
    last_sent = None # Keep track of the last frame sent
    try:
        while not is_shutting_down:
            # --- FIX 2: ONLY send the image if it is a BRAND NEW frame! ---
            if latest_outdoor_jpeg is not None and latest_outdoor_jpeg != last_sent:
                last_sent = latest_outdoor_jpeg
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + latest_outdoor_jpeg + b'\r\n')
            
            # Check really fast, but don't spam the network
            await asyncio.sleep(0.01) 
    except asyncio.CancelledError:
        pass



@app.get("/status")
def get_status():
    return latest_status

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while not is_shutting_down:
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/video-stream/indoor")
async def indoor_video_stream():
    return StreamingResponse(generate_indoor_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/video-stream/outdoor")
async def outdoor_video_stream():
    return StreamingResponse(generate_outdoor_frames(), media_type="multipart/x-mixed-replace; boundary=frame")