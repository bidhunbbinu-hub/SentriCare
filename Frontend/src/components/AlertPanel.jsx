import { useEffect, useState } from "react";
import { connectWebSocket,disconnectWebSocket } from "../services/websocket";
import { getAlertHistory } from "../services/api";
import { Bell, PersonStanding, Heart, CheckCircle, XCircle } from "lucide-react";
import { motion } from "framer-motion";

const iconMap = {
  FALL: PersonStanding,
  HEART_RATE: Heart,
  DEFAULT: Bell,
};

export default function AlertPanel() {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    getAlertHistory().then((data) => {
      if (Array.isArray(data)) {
        setAlerts(data);
      } else {
        setAlerts([]);
      }
    });

    connectWebSocket((data) => {
      setAlerts((prev) => [data, ...prev].slice(0, 10));
    });
    return () => {
      disconnectWebSocket();
    };
  }, []);

  async function updateAlert(alertId, status) {
    setAlerts((prevAlerts) =>
      prevAlerts.map((alert) =>
        alert.id === alertId ? { ...alert, status: status } : alert
      )
    );
    try {
      const response = await fetch(
        `http://localhost:8000/alerts/${alertId}/confirm?status=${status}`,
        { method: "POST" }
      );
      
      if (!response.ok) {
        console.error("Failed to update alert on the server");
        
      }
    } catch (error) {
      console.error("Network error updating alert:", error);
    }
  }

  const activeAlertsCount = alerts.filter((a) => a.status === "PENDING").length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="rounded-xl bg-slate-900 border border-slate-800 p-4 flex flex-col h-[400px]"
    >
      <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
        <Bell className="h-4 w-4 text-blue-500" />
        Recent Alerts
        {activeAlertsCount > 0 && (
          <span className="ml-auto text-xs bg-red-500/10 text-red-500 px-2 py-0.5 rounded-full font-mono border border-red-500/20">
            {activeAlertsCount} active
          </span>
        )}
      </h3>

      <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar pr-1">
        {alerts.length === 0 ? (
          <p className="text-slate-500 text-sm text-center mt-4">No recent alerts.</p>
        ) : (
          alerts.map((alert) => {
            const Icon = iconMap[alert.type] || iconMap.DEFAULT;
            const isPending = alert.status === "PENDING";

            return (
              <div
                key={alert.id}
                className={`w-full text-left rounded-lg border p-3 transition-colors ${
                  isPending 
                    ? "border-red-500/30 bg-red-500/5" 
                    : "border-slate-800 bg-slate-800/30"
                }`}
              >
                <div className="flex items-start gap-3">
                  <Icon
                    className={`h-4 w-4 mt-0.5 shrink-0 ${
                      isPending ? "text-red-500" : "text-yellow-500"
                    }`}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start">
                      <p className="text-sm text-slate-200 truncate font-medium">
                        {alert.type} Alert
                      </p>
                      <span className="text-xs text-slate-400">{alert.time}</span>
                    </div>
                    
                    <p className="text-xs text-slate-500 mt-0.5">
                      Status: <span className="font-mono">{alert.status}</span>
                    </p>

                    {isPending && (
                      <div className="flex gap-2 mt-3">
                        <button
                          onClick={() => updateAlert(alert.id, "CONFIRMED")}
                          className="flex-1 flex justify-center items-center gap-1 bg-red-500 hover:bg-red-600 text-white text-xs font-semibold py-1.5 rounded transition-colors shadow-sm shadow-red-500/20"
                        >
                          <CheckCircle className="h-3 w-3" /> Confirm
                        </button>
                        <button
                          onClick={() => updateAlert(alert.id, "FALSE_ALARM")}
                          className="flex-1 flex justify-center items-center gap-1 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-semibold py-1.5 rounded transition-colors"
                        >
                          <XCircle className="h-3 w-3" /> False
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </motion.div>
  );
}