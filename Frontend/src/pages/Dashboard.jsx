import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react"; // Import the spinner icon
import VideoStream from "../components/VideoStream";
import AlertPanel from "../components/AlertPanel";
import HealthStats from "../components/HealthStats";
import EmergencyPopup from "../components/EmergencyPopup";
import AddCaregiverModal from "../components/AddCaregiverModal";
import { useAuth } from "../lib/auth-context";

export default function Dashboard() {
  const [heartRate, setHeartRate] = useState("--");
  const [fallDetected, setFallDetected] = useState(false);
  const [systemAlert, setSystemAlert] = useState("NORMAL");
  const [isEmergencyPopupOpen, setIsEmergencyPopupOpen] = useState(false);
  const [popupAlertData, setPopupAlertData] = useState(null);
  const [isCaregiverModalOpen, setIsCaregiverModalOpen] = useState(false);
  
  
  const { user, isRefreshing } = useAuth(); 
  const navigate = useNavigate();

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch("http://localhost:8000/status");
        const data = await res.json();

        
        const faces = data?.data?.heart_rate?.faces;
        if (faces && faces.length > 0) {
          const bpm = faces[0]?.bpm;
          if (bpm !== null && bpm !== undefined) {
            setHeartRate(bpm);
          }
        }

       
        const isFall = data?.data?.fall?.fall_detected;
        setFallDetected(!!isFall);

        
        const alertStatus = data?.alert || "NORMAL";
        setSystemAlert(alertStatus);

        
        if (
          alertStatus === "EMERGENCY" ||
          alertStatus === "FALL_WARNING" ||
          alertStatus === "HIGH_RISK"
        ) {
          setPopupAlertData({
            message: `System detected: ${alertStatus.replace(/_/g, " ")}. Immediate verification required.`,
            severity: alertStatus === "EMERGENCY" ? "emergency" : "warning",
            location: "Camera 01",
            type: alertStatus,
          });

          setIsEmergencyPopupOpen(true);
        }
      } catch (err) {
        console.error("Status fetch error:", err);
      }
    };

    fetchStatus();

    // Polling every 2 seconds
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

 
  if (isRefreshing) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#020817] min-h-screen">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
          <p className="text-slate-400 text-sm animate-pulse">Syncing profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#020817] text-slate-200 font-sans">
      <header className="h-14 flex items-center justify-between border-b border-slate-800 px-4 lg:px-6 bg-[#020817]">
        <div>
          <h1 className="text-sm font-semibold text-slate-200">Dashboard</h1>
          <p className="text-xs text-slate-400">Real-time monitoring</p>
        </div>

        <div className="flex items-center gap-3">
          {user?.role === "PRIMARY" && (
            <button
              onClick={() => setIsCaregiverModalOpen(true)}
              className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-3 py-1.5 rounded-md font-medium transition-colors"
            >
              + Add Caregiver
            </button>
          )}

          <button
            onClick={() => setIsEmergencyPopupOpen(true)}
            className="text-xs bg-red-600 hover:bg-red-500 text-white px-3 py-1.5 rounded-md font-medium transition-colors shadow-sm shadow-red-500/20"
          >
            Trigger Emergency
          </button>
        </div>
      </header>

      
      {user?.role?.toUpperCase() === "PRIMARY" && !user?.patient_id && (
        <div className="bg-blue-500/10 border-b border-blue-500/20 px-4 lg:px-6 py-3 flex items-center justify-between">
          <p className="text-sm text-blue-400">
            <strong className="text-blue-300">Welcome!</strong> It looks like
            you haven't linked a camera to a patient yet.
          </p>
          <button
            onClick={() => navigate('/setup')}
            className="text-xs bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded font-medium transition-colors"
          >
            Setup Device
          </button>
        </div>
      )}

      <main className="flex-1 p-4 lg:p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <VideoStream />
          </div>
          <div className="space-y-6 flex flex-col">
            <HealthStats
              heartRate={heartRate}
              fallDetected={fallDetected}
              systemAlert={systemAlert}
            />
            <AlertPanel />
          </div>
        </div>
      </main>

      <EmergencyPopup
        isOpen={isEmergencyPopupOpen}
        onClose={() => setIsEmergencyPopupOpen(false)}
        alertData={popupAlertData}
      />
      <AddCaregiverModal
        isOpen={isCaregiverModalOpen}
        onClose={() => setIsCaregiverModalOpen(false)}
      />
    </div>
  );
}