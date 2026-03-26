from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import Alert
from alerts.alert_manager import alert_system

router = APIRouter()

@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db)):
    try:
        alerts = (
            db.query(Alert)
            .order_by(Alert.created_at.desc()) 
            .limit(10)
            .all()
        )

        return [
            {
                "id": a.id,
                "type": a.alert_type,        
                "status": a.status,
                "message": a.message,
                "time": str(a.created_at),
                "video_clip_path": a.video_clip_path    
            }
            for a in alerts
        ]
    except Exception as e:
        print(f"Error fetching alerts: {e}")
        return [] 

@router.post("/alerts/latest/confirm")
def confirm_latest_alert(status: str, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.status == "PENDING").order_by(Alert.created_at.desc()).first()
    
    if not alert:
        return {"message": "No pending alerts found"}
        
    alert.status = status
    db.commit()
    
    if status in ["CONFIRMED", "FALSE_ALARM"]:
        alert_system.cancel_timer(alert.id)
        
    return {"message": "Latest alert updated"}

@router.post("/alerts/{alert_id}/confirm")
def confirm_alert(alert_id: int, status: str, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = status
    db.commit()
    if status in ["CONFIRMED", "FALSE_ALARM"]:
        alert_system.cancel_timer(alert_id)

    return {"message": f"alert updated to {status}"}

