import { ShieldAlert, Camera, X, ShieldX, Video } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAlerts } from "../lib/alert-context";

export function SecurityAlertPopup() {
  const navigate = useNavigate();
  const {
    activeSecurityAlert,
    showSecurityPopup,
    dismissSecurityAlert,
    markSecurityFalseAlarm,
  } = useAlerts();

  // Play a notification sound when an intrusion is detected
  useEffect(() => {
    let securityChime;
    if (showSecurityPopup) {
      // You can use a different sound here like a short 'beep' instead of the looping medical alarm
      securityChime = new Audio('/alarm.mp3'); 
      // securityChime.loop = true; // Typically, security alerts might just beep once or twice
      securityChime.play().catch(e => console.log("Audio autoplay blocked by browser"));
    }

    return () => {
      if (securityChime) {
        securityChime.pause();
        securityChime.currentTime = 0;
      }
    };
  }, [showSecurityPopup]);

  if (!showSecurityPopup || !activeSecurityAlert) return null;

  const handleVerifyCamera = () => {
    dismissSecurityAlert();
    // Navigate to playback AND pass the exact alert ID in the router state!
    navigate("/playback", { state: { targetAlertId: activeSecurityAlert.id } });
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
      >
        <motion.div
          key="security-alert-step"
          initial={{ scale: 0.9, y: 20 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.9, y: 20 }}
          // Using Orange/Amber colors to distinguish from the Red medical emergencies
          className="w-full max-w-md rounded-2xl bg-slate-900 border border-orange-500/40 p-6 shadow-[0_0_40px_rgba(249,115,22,0.15)]"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-6 w-6 text-orange-500 animate-pulse" />
              <h2 className="text-lg font-bold text-slate-200">
                SECURITY INTRUSION
              </h2>
            </div>
            <button onClick={dismissSecurityAlert}>
              <X className="h-5 w-5 text-slate-400 hover:text-slate-200 transition-colors" />
            </button>
          </div>

          {/* Camera Snapshot Simulation */}
          <div className="rounded-lg bg-black/50 aspect-video mb-4 flex items-center justify-center relative overflow-hidden border border-slate-800">
            <Camera className="h-10 w-10 text-slate-600" />
            
            {/* Simulated Bounding Box for Intruder */}
            <div className="absolute top-[20%] left-[30%] w-[35%] h-[55%] border-2 border-orange-500 rounded-sm">
              <div className="absolute -top-5 left-0 bg-orange-500 text-slate-900 text-[10px] px-1.5 py-0.5 rounded-t font-mono font-bold">
                PERSON DETECTED
              </div>
            </div>

            <div className="absolute bottom-2 left-2 bg-black/60 rounded px-2 py-0.5">
              <span className="text-xs font-mono text-slate-300">
                {activeSecurityAlert.location || "Outdoor Camera"} — {new Date(activeSecurityAlert.time || activeSecurityAlert.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </div>

          <div className="mb-6">
            <p className="text-sm font-medium text-slate-200">
              {activeSecurityAlert.message || "Suspicious activity detected in the perimeter. Please review footage."}
            </p>
          </div>

          <div className="flex flex-col gap-3">
            {/* UPDATED: Changed icon to Video and text to Verify Event Video */}
            <button
              onClick={handleVerifyCamera}
              className="w-full flex items-center justify-center bg-orange-600 hover:bg-orange-500 text-white py-2.5 rounded-xl font-medium transition-colors shadow-sm shadow-orange-500/20"
            >
              <Video className="h-4 w-4 mr-2" />
              Verify Event Video
            </button>
            
            <button
              onClick={() => markSecurityFalseAlarm(activeSecurityAlert.id)}
              className="w-full flex items-center justify-center py-2.5 border border-slate-700 text-slate-300 rounded-xl hover:bg-slate-800 transition-colors"
            >
              <ShieldX className="h-4 w-4 mr-2" />
              Mark as False Alarm
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}