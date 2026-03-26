import { Camera, Maximize2, RefreshCw } from "lucide-react";
import { motion } from "framer-motion";
import { useState } from "react";

export default function VideoStream() {
  const [streamUrl, setStreamUrl] = useState("http://localhost:8000/video-stream/indoor");
  const [isRetrying, setIsRetrying] = useState(false);

  
  const handleStreamError = () => {
    setIsRetrying(true);
    
    setTimeout(() => {
      setStreamUrl(`http://localhost:8000/video-stream/indoor?t=${new Date().getTime()}`);
      setIsRetrying(false);
    }, 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl overflow-hidden bg-slate-900 border border-slate-800"
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Camera className="h-4 w-4 text-blue-500" />
          <span className="text-sm font-medium text-slate-200">Live Camera — Monitoring</span>
        </div>
        <div className="flex items-center gap-2">
          {isRetrying ? (
            <span className="flex items-center gap-1">
              <RefreshCw className="h-3 w-3 text-yellow-500 animate-spin" />
              <span className="text-xs text-yellow-500 font-mono">RECONNECTING...</span>
            </span>
          ) : (
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
              <span className="text-xs text-red-500 font-mono">LIVE</span>
            </span>
          )}
          <Maximize2 className="h-4 w-4 text-slate-400 cursor-pointer hover:text-slate-200 transition-colors ml-2" />
        </div>
      </div>
      
      <div className="relative aspect-video bg-black flex items-center justify-center">
        {/* Added onError to trigger the reconnect logic */}
        <img
          src={streamUrl}
          alt="Live Stream"
          onError={handleStreamError}
          className={`w-full h-full object-cover transition-opacity duration-300 ${isRetrying ? 'opacity-50' : 'opacity-100'}`}
        />
        
        {/* Overlay timestamp */}
        <div className="absolute bottom-3 left-3 bg-black/50 backdrop-blur-md rounded px-2 py-1">
          <p className="text-xs font-mono text-slate-200/80">
            CAM-01 • {new Date().toLocaleDateString()}
          </p>
        </div>
      </div>
    </motion.div>
  );
}