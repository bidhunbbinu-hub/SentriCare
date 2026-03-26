from twilio.rest import Client
from config import Config
from datetime import datetime


account_sid = Config.TWILIO_ACCOUNT_SID
auth_token = Config.TWILIO_AUTH_TOKEN
client = Client(account_sid, auth_token)

def trigger_emergency_call(to_phone_number: str):
    """
    Initiates an automated phone call using Twilio Studio Flow.
    """
    try:
        client = Client(Config.TWILIO_ACCOUNT_SID, Config.TWILIO_AUTH_TOKEN)

        
        execution = client.studio.v2.flows(
            "FW521afda7761e581372a9b134a2785ef7"
        ).executions.create(
            to=to_phone_number, 
            from_=Config.TWILIO_PHONE_NUMBER 
        )
        
        print(f"📞 Twilio Studio Flow Executed! SID: {execution.sid}")
        return True

    except Exception as e:
        print(f"❌ Failed to trigger Twilio call: {e}")
        return False
    
def send_whatsapp_alert(to_number: str, alert_type: str, details: str):
    """
    Sends a formatted WhatsApp message to the caregiver.
    """
    try:
        
        from_whatsapp_number = 'whatsapp:+14155238886' 
        
        # Ensure the recipient number is formatted correctly for WhatsApp
        to_whatsapp_number = f'whatsapp:{to_number}'
        
        # Create a nicely formatted message using emojis and markdown (bold/italics)
        msg_body = (
            f"🚨 *ANOMOLY ALERT: {alert_type.replace('_', ' ')}* 🚨\n\n"
            f"{details}\n\n"
            f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"🔗 Please check the dashboard immediately!"
        )
        
        message = client.messages.create(
            body=msg_body,
            from_=from_whatsapp_number,
            to=to_whatsapp_number
        )
        
        print(f"✅ WhatsApp message sent successfully! SID: {message.sid}")
        return message.sid
        
    except Exception as e:
        print(f"❌ Failed to send WhatsApp message: {e}")
        return None