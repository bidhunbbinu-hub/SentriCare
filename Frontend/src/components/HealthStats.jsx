import { Heart, Activity, PersonStanding } from "lucide-react";
import { motion } from "framer-motion";

export default function HealthStats({ heartRate, fallDetected, systemAlert }) {
  const isAlertActive = systemAlert !== "NORMAL";
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="rounded-xl bg-slate-900 border border-slate-800 p-4"
    >
      <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center gap-2">
        <Activity className="h-4 w-4 text-blue-500" />
        Health Status
      </h3>

      <div className="space-y-3">
        {/* Heart Rate */}
        <div className="rounded-lg border p-3 border-emerald-500/20 bg-emerald-500/10 text-emerald-500">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Heart className="h-5 w-5" />
              <span className="text-sm font-medium">Heart Rate</span>
            </div>
            <span className="text-2xl font-bold font-mono">{heartRate}</span>
          </div>
          <p className="text-xs mt-1 opacity-70">
            BPM — {systemAlert === "ABNORMAL_HEART_RATE" || systemAlert === "HIGH_RISK" ? "ABNORMAL" : "NORMAL"}
          </p>
        </div>

        {/* Activity Status */}
        <div className="rounded-lg border border-slate-800 bg-slate-800/50 p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-500" />
              <span className="text-sm font-medium text-slate-200">Activity</span>
            </div>
            <span className="text-sm font-semibold text-slate-200">{systemAlert}</span>
          </div>
          <p className="text-xs text-slate-400 mt-1">{isAlertActive ? "Attention required" : "System Active"}</p>
        </div>

        {/* Fall Detection (Ready for future dynamic state) */}
        <div className="rounded-lg border p-3 border-emerald-500/20 bg-emerald-500/10 text-emerald-500">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <PersonStanding className="h-5 w-5" />
              <span className="text-sm font-medium">Fall Detection</span>
            </div>
            <span className="text-sm font-semibold">{fallDetected ? "DETECTED" : "Clear"}</span>
          </div>
          <p className="text-xs mt-1 opacity-70">{fallDetected ? "Immediate attention needed" : "No falls detected"} </p>
        </div>
      </div>

      <p className="text-xs text-slate-500 mt-3">
        Updated {new Date().toLocaleTimeString()}
      </p>
    </motion.div>
  );
}