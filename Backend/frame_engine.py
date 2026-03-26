from config import Config
from fall_detection.detector import FallDetector
from evm_module.evm_service import EVMService
from alerts.alert_manager import AlertManager
import asyncio


class FrameEngine:

    def __init__(self):
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            # Fallback if the loop isn't globally set yet
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        self.fall_detector = FallDetector(
            sequence_length=Config.SEQUENCE_LENGTH,
            confidence_threshold=Config.FALL_CONFIDENCE_THRESHOLD,
            immobility_seconds=Config.IMMOBILITY_SECONDS
        )

        self.evm_service = EVMService(
            min_face_width=Config.MIN_FACE_WIDTH,
            min_detection_confidence=Config.MIN_DETECTION_CONFIDENCE,
            multiple_faces=Config.MULTIPLE_FACES,
            debug=True
        )

        self.alert_manager = AlertManager()


    def process(self, frame,camera_id):

        
        fall_result = self.fall_detector.process_frame(frame)
        evm_result = self.evm_service.process_frame(frame)
        print(f"Fall Detection Result: {fall_result}")
        print(f"EVM Result: {evm_result}")  

        combined_data = {
            "camera_id": camera_id,
            "fall": fall_result,
            "heart_rate": evm_result
        }

        if self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.alert_manager.evaluate(combined_data), 
                self.loop
            )
        else:
            
            print("Warning: Main event loop not running. Alert skipped.")
        
        alert_status = self._quick_status(combined_data)
        combined_data["alert_status"] = alert_status

        print(f"System Status: {alert_status}")

        return combined_data


    def _quick_status(self, data):

        fall = data["fall"]["fall_detected"]
        emergency = data["fall"]["emergency"]

        heart_data = data["heart_rate"]["faces"]

        abnormal_hr = False

        for face in heart_data:

            bpm = face["bpm"]
            confidence = face.get("confidence", "LOW")

            if bpm and confidence in ["MEDIUM", "HIGH"]:

                if bpm < Config.HEART_RATE_LOW or bpm > Config.HEART_RATE_HIGH:
                    abnormal_hr = True

        if emergency:
            return "EMERGENCY"

        if fall and abnormal_hr:
            return "HIGH_RISK"

        if fall:
            return "FALL_WARNING"

        if abnormal_hr:
            return "ABNORMAL_HEART_RATE"

        return "NORMAL"