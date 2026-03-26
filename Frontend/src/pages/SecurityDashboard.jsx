import { Eye, ShieldAlert, ShieldCheck, Clock } from "lucide-react";
import { useAlerts } from "../lib/alert-context";
import { motion } from "framer-motion";

export default function SecurityDashboard() {
  const { alerts } = useAlerts();
  
  // Filter for today's security events
  const securityEvents = alerts
    .filter((a) => a.category === "security" || a.type === "INTRUSION")
    .filter((a) => {
      const today = new Date();
      const alertDate = new Date(a.time || a.timestamp);
      return alertDate.toDateString() === today.toDateString();
    });

  const isSecure = securityEvents.length === 0 || securityEvents[0].status === "FALSE_ALARM";

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#020817] text-slate-200 font-sans">
      <header className="h-14 flex items-center justify-between border-b border-slate-800 px-4 lg:px-6 bg-[#020817]">
        <div>
          <h1 className="text-sm font-semibold text-slate-200">Outdoor Security</h1>
          <p className="text-xs text-slate-400">External threat & perimeter monitoring</p>
        </div>
      </header>

      <main className="flex-1 p-4 lg:p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* LEFT/CENTER: Large Outdoor Camera Feed */}
          <div className="lg:col-span-2 space-y-6">
            
            <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
              <div className="bg-slate-900 px-4 py-3 border-b border-slate-800 flex justify-between items-center">
                <h2 className="text-sm font-semibold flex items-center gap-2 text-slate-200">
                  <Eye className="h-4 w-4 text-orange-500" />
                  Live Feed: External Camera
                </h2>
                <span className="flex h-2.5 w-2.5 rounded-full bg-green-500 animate-pulse"></span>
              </div>
              <div className="aspect-video bg-black relative">
                <img 
                  src="http://localhost:8000/video-stream/outdoor" 
                  alt="Outdoor Security Stream"
                  className="w-full h-full object-cover"
                  onError={(e) => e.target.style.display = 'none'} // Hide if offline
                />
              </div>
            </div>
            
            {/* Quick System Status Indicator */}
            <div className={`p-4 rounded-xl border flex items-center gap-4 ${isSecure ? 'bg-green-500/5 border-green-500/20' : 'bg-orange-500/5 border-orange-500/20'}`}>
              <div className={`p-3 rounded-full ${isSecure ? 'bg-green-500/10' : 'bg-orange-500/10'}`}>
                {isSecure ? <ShieldCheck className="h-6 w-6 text-green-500" /> : <ShieldAlert className="h-6 w-6 text-orange-500" />}
              </div>
              <div>
                <h3 className="font-bold text-lg text-slate-200">{isSecure ? "System Secure" : "Anomaly Detected"}</h3>
                <p className="text-sm text-slate-400">
                  {isSecure ? "No recent external threats detected in the perimeter." : "Recent suspicious activity logged. Please review the footage."}
                </p>
              </div>
            </div>
          </div>

          {/* RIGHT: Today's Event Log */}
          <div className="flex flex-col">
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 flex-1 max-h-[calc(100vh-10rem)] flex flex-col">
              <h3 className="text-sm font-bold flex items-center gap-2 mb-4 border-b border-slate-800 pb-3 text-slate-200">
                <Clock className="h-4 w-4 text-orange-500" />
                Today's Security Log
                {securityEvents.length > 0 && (
                  <span className="ml-auto text-xs bg-orange-500/10 text-orange-500 px-2 py-0.5 rounded font-mono">
                    {securityEvents.length}
                  </span>
                )}
              </h3>
              
              <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
                {securityEvents.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-40 text-slate-500">
                    <ShieldCheck className="h-8 w-8 mb-2 opacity-50" />
                    <p className="text-sm">No security events today</p>
                  </div>
                ) : (
                  securityEvents.map((event, i) => (
                    <motion.div
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.05 }}
                      key={event.id}
                      className="p-3 rounded-lg border border-slate-800 bg-slate-800/50 flex flex-col gap-1"
                    >
                      <div className="flex justify-between items-start">
                        <span className="text-xs font-bold text-orange-500">
                          {event.type.replace(/_/g, " ")}
                        </span>
                        <span className="text-[10px] text-slate-400">
                          {new Date(event.time || event.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-sm text-slate-300">{event.message}</p>
                      <div className="mt-2 text-right">
                        <span className={`text-[10px] px-2 py-1 rounded capitalize font-medium ${
                          event.status === 'FALSE_ALARM' ? 'bg-slate-800 text-slate-400' : 'bg-orange-500/10 text-orange-400'
                        }`}>
                          {event.status.replace(/_/g, " ")}
                        </span>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}