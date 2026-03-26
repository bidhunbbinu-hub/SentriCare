import os
from dotenv import load_dotenv

load_dotenv()


class Config:
   
    DEBUG = os.getenv("DEBUG", "False") == "True"

   
    CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "0")
    CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", 640))
    CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", 480))

  
    FALL_CONFIDENCE_THRESHOLD = float(
        os.getenv("FALL_CONFIDENCE_THRESHOLD", 0.85)
    )

    SEQUENCE_LENGTH = int(
        os.getenv("SEQUENCE_LENGTH", 30)
    )

    IMMOBILITY_SECONDS  = int(
        os.getenv("IMMOBILITY_SECONDS ", 20)
    )

   
    MIN_FACE_WIDTH = int(
        os.getenv("MIN_FACE_WIDTH", 120)
    )

    MIN_DETECTION_CONFIDENCE = float(
        os.getenv("MIN_DETECTION_CONFIDENCE", 0.7)
    )

    MULTIPLE_FACES = os.getenv("MULTIPLE_FACES", "False") == "True"

    
    HEART_RATE_LOW = int(
        os.getenv("HEART_RATE_LOW", 45)
    )

    HEART_RATE_HIGH = int(
        os.getenv("HEART_RATE_HIGH", 130)
    )
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")    
    TO_PHONE_NUMBER= os.getenv("TO_PHONE_NUMBER")