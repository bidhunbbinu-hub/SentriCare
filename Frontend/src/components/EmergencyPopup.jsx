import { AlertTriangle, Camera, Phone, X, CheckCircle, Video } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function EmergencyPopup({ isOpen, onClose, alertData }) {
  const navigate = useNavigate();
  const [step, setStep] = useState("alert"); 

  useEffect(() => {
    let alarmSound;
    
    if (isOpen) {
      setStep("alert");
    
      alarmSound = new Audio('/alarm.mp3');
      alarmSound.loop = true;
      alarmSound.play().catch(e => console.log("Audio autoplay blocked by browser until user interacts"));
    }

    return () => {
      if (alarmSound) {
        alarmSound.pause();
        alarmSound.currentTime = 0;
      }
    };
  }, [isOpen]);

  const handleAction = async (status) => {
    try {
      const targetId = alertData?.alert_id;

      if (targetId) {
        console.log(`Cancelling exact timer for Alert ID: ${targetId}`);
        await fetch(`http://localhost:8000/alerts/${targetId}/confirm?status=${status}`, {
          method: "POST"
        });
      } else {
        console.log("No specific ID found, falling back to latest...");
        await fetch(`http://localhost:8000/alerts/latest/confirm?status=${status}`, {
          method: "POST"
        });
      }
    } catch (err) {
      console.error("Failed to update status", err);
    }
  };

  if (!isOpen) return null;

  const handleVerifyCamera = () => {
    onClose();
    // Navigate to playback AND pass the exact alert ID in the router state!
    navigate("/playback", { state: { targetAlertId: alertData?.alert_id } });
  };

  const handleFalseAlarm = () => {
    handleAction("FALSE_ALARM"); 
    onClose();
  };

  const handleConfirmEmergency = () => {
    handleAction("CONFIRMED"); 
    setStep("call");
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
      >
        {step === "alert" ? (
          <motion.div
            key="alert-step"
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            className="w-full max-w-md rounded-2xl bg-slate-900 border border-red-500/40 p-6 shadow-[0_0_40px_rgba(239,68,68,0.15)]"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-6 w-6 text-red-500 animate-pulse" />
                <h2 className="text-lg font-bold text-slate-200">
                  EMERGENCY DETECTED
                </h2>
              </div>
              <button onClick={onClose}>
                <X className="h-5 w-5 text-slate-400 hover:text-slate-200 transition-colors" />
              </button>
            </div>

            <div className="rounded-lg bg-black/50 aspect-video mb-4 flex items-center justify-center relative overflow-hidden border border-slate-800">
              <Camera className="h-10 w-10 text-slate-600" />
              <div className="absolute bottom-2 left-2 bg-black/60 rounded px-2 py-0.5">
                <span className="text-xs font-mono text-slate-300">
                  Camera 01 — {new Date().toLocaleTimeString()}
                </span>
              </div>
            </div>

            <div className="mb-6">
              <p className="text-sm font-medium text-slate-200">
                {alertData?.message || "Potential fall detected. Immediate verification required."}
              </p>
            </div>

            <div className="flex flex-col gap-3">
              {/* UPDATED: Changed icon to Video and text to Verify Event Video */}
              <button
                onClick={handleVerifyCamera}
                className="w-full flex items-center justify-center bg-blue-600 hover:bg-blue-500 text-white py-2.5 rounded-xl font-medium transition-colors"
              >
                <Video className="h-4 w-4 mr-2" />
                Verify Event Video
              </button>
              
              <button
                onClick={handleConfirmEmergency}
                className="w-full flex items-center justify-center bg-red-600 hover:bg-red-500 text-white py-2.5 rounded-xl font-medium transition-colors shadow-sm shadow-red-500/20"
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Confirm Emergency
              </button>
              
              <button
                onClick={handleFalseAlarm}
                className="w-full flex items-center justify-center py-2.5 border border-slate-700 text-slate-300 rounded-xl hover:bg-slate-800 transition-colors"
              >
                False Alarm
              </button>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="call-step"
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            className="w-full max-w-sm rounded-2xl bg-slate-900 border border-red-500/40 p-8 text-center shadow-[0_0_40px_rgba(239,68,68,0.2)]"
          >
            <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4 animate-pulse" />
            <h2 className="text-xl font-bold text-slate-200 mb-2">Emergency Confirmed</h2>
            <p className="text-sm text-slate-400 mb-6">
              Please call emergency services immediately.
            </p>

            <a
              href="tel:+911234567890"
              className="flex items-center justify-center w-full rounded-xl bg-red-600 hover:bg-red-500 text-white py-4 text-lg font-bold transition-all shadow-[0_0_15px_rgba(220,38,38,0.3)]"
            >
              <Phone className="h-6 w-6 mr-2" />
              CALL EMERGENCY
            </a>

            <button
              onClick={onClose}
              className="w-full mt-4 text-slate-400 hover:text-slate-200 py-2 border border-slate-700 rounded-xl hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
          </motion.div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}