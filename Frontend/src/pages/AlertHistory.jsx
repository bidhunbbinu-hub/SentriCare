import { useEffect, useState } from "react";
import { getAlertHistory } from "../services/api";
import { Bell, PersonStanding, Heart, Play, ShieldAlert } from "lucide-react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

const iconMap = {
  FALL: PersonStanding,
  EMERGENCY: PersonStanding, // Added in case your backend uses EMERGENCY for falls
  HEART_RATE: Heart,
  INTRUSION: ShieldAlert,    // Added so Security alerts get the shield icon
  DEFAULT: Bell,
};

const statusBadge = {
  PENDING: "bg-red-500/10 text-red-500 border-red-500/20",
  CONFIRMED: "bg-yellow-500/10 text-yellow-500 border-yellow-500/20",
  FALSE_ALARM: "bg-slate-800 text-slate-400 border-slate-700",
  RESOLVED: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  ESCALATED: "bg-purple-500/10 text-purple-500 border-purple-500/20", // Added just in case
};

export default function AlertHistory() {
  const [alerts, setAlerts] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    getAlertHistory().then((data) => {
      setAlerts(Array.isArray(data) ? data : []);
    });
  }, []);

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#020817] text-slate-200">
      <header className="h-14 flex items-center border-b border-slate-800 px-4 lg:px-6">
        <div>
          <h1 className="text-sm font-semibold">Alert History</h1>
          <p className="text-xs text-slate-400">{alerts.length} total alerts</p>
        </div>
      </header>

      <main className="flex-1 p-4 lg:p-6">
        <div className="space-y-3">
          {alerts.length === 0 ? (
            <p className="text-slate-500 text-sm">No historical alerts found.</p>
          ) : (
            alerts.map((alert, i) => {
              const Icon = iconMap[alert.type] || iconMap.DEFAULT;
              const badgeStyle = statusBadge[alert.status] || statusBadge.FALSE_ALARM;

              return (
                <motion.div
                  key={alert.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="rounded-xl bg-slate-900 border border-slate-800 p-4 flex items-center gap-4"
                >
                  <div
                    className={`h-10 w-10 rounded-lg flex items-center justify-center shrink-0 ${
                      alert.status === "PENDING" ? "bg-red-500/10" : "bg-slate-800/50"
                    }`}
                  >
                    <Icon
                      className={`h-5 w-5 ${
                        alert.status === "PENDING" ? "text-red-500" : "text-slate-400"
                      }`}
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{alert.type.replace(/_/g, " ")} Alert</p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Camera 01 • {new Date(alert.time).toLocaleString()}
                    </p>
                  </div>
                  <span className={`text-[10px] px-2 py-1 rounded-full border font-bold uppercase tracking-wider shrink-0 ${badgeStyle}`}>
                    {alert.status.replace("_", " ")}
                  </span>
                  
                  {/* UPDATED: We now pass the exact alert ID in the router state */}
                  <button
                    onClick={() => navigate("/playback", { state: { targetAlertId: alert.id } })}
                    className="p-2 hover:bg-slate-800 rounded-md transition-colors text-slate-400 hover:text-blue-400 shrink-0 shadow-sm"
                    title="Play Event Video"
                  >
                    <Play className="h-4 w-4" />
                  </button>
                </motion.div>
              );
            })
          )}
        </div>
      </main>
    </div>
  );
}