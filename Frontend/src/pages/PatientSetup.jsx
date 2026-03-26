import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { User, Calendar, Phone, Camera, ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";
import { useAuth } from "../lib/auth-context";

export default function PatientSetup() {
  const [name, setName] = useState("");
  const [age, setAge] = useState("");
  const [emergencyContact, setEmergencyContact] = useState("");
  const [cameraId, setCameraId] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  
  const navigate = useNavigate();
  // 1. Destructure refreshUser from your Auth Context
  const { user, refreshUser } = useAuth(); 

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const token = localStorage.getItem("token");
      
      const response = await fetch("http://localhost:8000/patients/setup", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}` 
        },
        body: JSON.stringify({ 
          name, 
          age: parseInt(age), 
          emergency_contact: emergencyContact, 
          camera_id: cameraId 
        }),
      });

      if (response.ok) {
        await refreshUser(); 
        
        navigate("/");
      } else {
        const data = await response.json();
        setError(data.detail || "Failed to setup patient. Check Camera ID.");
      }
    } catch (err) {
      setError("Network error. Could not connect to server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#020817] p-4 font-sans text-slate-200">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 mb-4">
            <ShieldCheck className="h-8 w-8 text-emerald-500" />
          </div>
          <h1 className="text-2xl font-bold text-slate-100">Patient Setup</h1>
          <p className="text-sm text-slate-400 mt-1">
            Link your monitoring camera to a patient
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-4 shadow-xl"
        >
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-500 text-sm text-center">
              {error}
            </div>
          )}

          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Patient Name</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="e.g., Robert Johnson"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full pl-10 pr-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
                required
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Patient Age</label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <input
                type="number"
                placeholder="75"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                className="w-full pl-10 pr-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
                required
                min="1"
                max="120"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Emergency Contact Number</label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <input
                type="tel"
                placeholder="+1 234 567 8900"
                value={emergencyContact}
                onChange={(e) => setEmergencyContact(e.target.value)}
                className="w-full pl-10 pr-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
                required
              />
            </div>
          </div>

          <div className="pt-2">
            <label className="text-xs font-medium text-slate-400 mb-1.5 block">Hardware Camera ID</label>
            <div className="relative">
              <Camera className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="e.g., CAM-01"
                value={cameraId}
                onChange={(e) => setCameraId(e.target.value)}
                className="w-full pl-10 pr-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors uppercase"
                required
              />
            </div>
            <p className="text-[10px] text-slate-500 mt-1">Found on the sticker underneath your camera unit.</p>
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg transition-colors mt-4"
          >
            {loading ? "Registering..." : "Complete Setup"}
          </button>
        </form>
      </motion.div>
    </div>
  );
}