from config import Config
from websocket.ws_manager import manager
from datetime import datetime, timedelta
from database.db import SessionLocal
from database.models import Alert, Camera
import asyncio
from notifications.twilio_service import trigger_emergency_call, send_whatsapp_alert
from video_recorder import indoor_recorder, outdoor_recorder


phone_number=Config.TO_PHONE_NUMBER

class AlertManager:
    def __init__(self):
        self.active_escalations = {}
        self.last_alert_time = None     
        self.cooldown_seconds = 30
        
   
        self.snooze_until = None 

    async def evaluate(self, data):
        camera_id = data.get("camera_id")

        
        if self.snooze_until and datetime.now() < self.snooze_until:
            return "NORMAL"

        if data.get("outdoor_anomaly"):
            alert = "INTRUSION"
            current_time = datetime.now()
            
            if self.last_alert_time is None or (current_time - self.last_alert_time) > timedelta(seconds=self.cooldown_seconds):
                self.last_alert_time = current_time 
                await self.send_alert(alert, "Suspicious activity detected outside", camera_id)
            return alert
        
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
            alert = "EMERGENCY"
        elif fall and abnormal_hr:
            alert = "HIGH_RISK"
        elif fall:
            alert = "FALL_WARNING"
        elif abnormal_hr:
            alert = "ABNORMAL_HEART_RATE"
        else:
            alert = "NORMAL"

        if alert != "NORMAL":
            current_time = datetime.now()
        
            if self.last_alert_time is None or (current_time - self.last_alert_time) > timedelta(seconds=self.cooldown_seconds):
                self.last_alert_time = current_time 
                await self.send_alert(alert, "Patient health alert detected", camera_id)

        return alert

    def _save_to_db_sync(self, alert_type, message, camera_id):
        """Runs the blocking database connection separately."""
        db = SessionLocal()
        alert_id = None
        actual_patient_id = None
        
        try:
            camera_record = db.query(Camera).filter(Camera.id == camera_id).first()
            actual_patient_id = camera_record.patient_id if camera_record else None
            
            alert = Alert(
                patient_id=actual_patient_id, 
                alert_type=alert_type,
                message=message,
                status="PENDING"
            )
            
            db.add(alert)
            db.commit()
            db.refresh(alert)
            alert_id = alert.id
        except Exception as e:
            print(f"Database error: {e}")
            db.rollback()
        finally:
            db.close()
            
        return actual_patient_id, alert_id

    async def send_alert(self, alert_type, message, camera_id):
        actual_patient_id, alert_id = await asyncio.to_thread(
            self._save_to_db_sync, alert_type, message, camera_id
        )
        if alert_id:
            if alert_type == "INTRUSION":
                outdoor_recorder.trigger(alert_id)
            elif alert_type in ["EMERGENCY", "FALL_WARNING", "HIGH_RISK"]:
                indoor_recorder.trigger(alert_id)

            alert_data = {
                "alert_id": alert_id,
                "patient_id": actual_patient_id, 
                "type": alert_type,
                "message": message,
                "time": datetime.utcnow().isoformat()
            }

           
            await manager.broadcast(alert_data)
            
           
            if alert_type == "INTRUSION":
                print(f"🚨 INTRUSION DETECTED! SENDING INSTANT WHATSAPP... 🚨")
               
                asyncio.create_task(asyncio.to_thread(
                    send_whatsapp_alert, 
                    to_number=phone_number,
                    alert_type=alert_type,
                    details="⚠️ UNAUTHORIZED MOTION DETECTED! A person has been spotted in the outdoor perimeter. Please open the SmartCare dashboard and verify the live camera feed immediately."
                ))
                
            # 3. DELAYED ESCALATION FOR MEDICAL EMERGENCIES
            elif alert_type in ["EMERGENCY", "FALL_WARNING", "HIGH_RISK"]:
                task = asyncio.create_task(self._countdown_task(alert_id, actual_patient_id))
                self.active_escalations[alert_id] = task


    async def _countdown_task(self, alert_id, patient_id):
        try:
            await asyncio.sleep(15) 
     
            db = SessionLocal()
            try:
                alert = db.query(Alert).filter(Alert.id == alert_id).first()
                if alert and alert.status == "PENDING":
                    alert.status = "ESCALATED"
                    db.commit()
                    
                    if alert.alert_type == "EMERGENCY":
                        print(f"🚨 EMERGENCY ALERT {alert_id} UNANSWERED! INITIATING PHONE CALL... 🚨")
                        print("Forcing Twilio call for demonstration purposes...")  
                        
                        await asyncio.to_thread(
                            trigger_emergency_call, 
                            phone_number 
                        )
                    else:
                        print(f"⚠️ Alert {alert_id} escalated. Skipping phone call to prevent spam.")
            finally:
                db.close()
                
        except asyncio.CancelledError:
            print(f"✅ Escalation cancelled for alert {alert_id}. No phone call needed.")
        finally:
            self.active_escalations.pop(alert_id, None)
    def cancel_timer(self, alert_id):
        """Cancels the Twilio call AND snoozes the AI so the person can stand up."""
        
        safe_id = int(alert_id) 
        
        task = self.active_escalations.get(safe_id)
        if task:
            task.cancel()
            
        
        self.snooze_until = datetime.now() + timedelta(seconds=60)
        print(f"🛑 FALSE ALARM REGISTERED! AI Snoozed for 60 seconds.")
    


alert_system = AlertManager()