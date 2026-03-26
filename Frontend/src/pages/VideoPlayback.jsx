import { Camera, Rewind, FastForward, Pause, Play, AlertTriangle, ShieldAlert, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { useState, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";

export default function VideoPlayback() {
  const [playing, setPlaying] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState(null);
  
  // NEW: State to track if the video is currently being recorded by the backend
  const [isProcessing, setIsProcessing] = useState(false);
  
  const videoRef = useRef(null);
  const location = useLocation();

  // Unified function to fetch data so we can reuse it for polling
  const loadVideoData = () => {
    fetch("http://localhost:8000/alerts")
      .then((res) => res.json())
      .then((data) => {
        // Filter alerts to only show those that have finished compiling a video
        const completedVideos = data.filter((a) => a.video_clip_path);
        setAlerts(completedVideos);

        // Check if we came from a popup with a specific target ID
        const targetId = location.state?.targetAlertId;
        
        if (targetId) {
          const specificAlert = completedVideos.find(a => a.id === targetId);
          
          if (specificAlert && specificAlert.video_clip_path) {
            // Video is ready! Stop processing and play it.
            setSelectedVideo(specificAlert.video_clip_path);
            setIsProcessing(false);
          } else {
            // Target was requested, but video isn't in the DB yet. It's still recording!
            setIsProcessing(true);
          }
        }
      })
      .catch((err) => console.error("Error fetching video clips:", err));
  };

  // 1. Initial Load
  useEffect(() => {
    loadVideoData();
  }, [location.state?.targetAlertId]);

  // 2. Auto-Polling: If processing, check the backend every 3 seconds
  useEffect(() => {
    let interval;
    if (isProcessing) {
      interval = setInterval(() => {
        console.log("Polling backend for finished video clip...");
        loadVideoData();
      }, 3000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isProcessing, location.state?.targetAlertId]);

  const togglePlay = () => {
    if (videoRef.current) {
      if (playing) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setPlaying(!playing);
    }
  };

  const skip = (seconds) => {
    if (videoRef.current) {
      videoRef.current.currentTime += seconds;
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-[#020817] text-slate-200">
      <header className="h-14 flex items-center border-b border-slate-800 px-4 lg:px-6">
        <div>
          <h1 className="text-sm font-semibold">Video Playback</h1>
          <p className="text-xs text-slate-400">Recorded 60-second event clips</p>
        </div>
      </header>

      <main className="flex-1 p-4 lg:p-6 space-y-8 overflow-y-auto">
        
        {/* --- MAIN VIDEO PLAYER --- */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl bg-slate-900 border border-slate-800 overflow-hidden max-w-5xl mx-auto shadow-lg"
        >
          <div className="aspect-video bg-black flex items-center justify-center relative border-b border-slate-800 overflow-hidden">
            
            {/* conditional rendering for Processing vs Playing vs Placeholder */}
            {isProcessing ? (
              <div className="text-center z-10 flex flex-col items-center">
                <Loader2 className="h-12 w-12 text-blue-500 animate-spin mx-auto mb-4" />
                <p className="text-sm font-bold text-slate-200">Compiling Event Video...</p>
                <p className="text-xs text-slate-500 mt-2 max-w-[250px]">
                  The system is capturing the 30 seconds after the event. Please wait, the video will auto-play shortly.
                </p>
              </div>
            ) : selectedVideo ? (
              <video
                ref={videoRef}
                src={`http://localhost:8000${selectedVideo}`}
                className="w-full h-full object-contain"
                onPlay={() => setPlaying(true)}
                onPause={() => setPlaying(false)}
                onEnded={() => setPlaying(false)}
                autoPlay
                controls
              />
            ) : (
              <div className="text-center z-10">
                <Camera className="h-16 w-16 text-slate-700 mx-auto mb-3" />
                <p className="text-sm text-slate-500">Select an event below to play the recording</p>
              </div>
            )}

            <div className="absolute bottom-3 left-3 bg-black/60 rounded px-2 py-1 pointer-events-none">
              <span className="text-xs font-mono text-slate-300 flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${isProcessing ? 'bg-blue-500' : 'bg-red-500'} animate-pulse`}></span>
                {isProcessing ? 'PROCESSING' : 'REC — Event Playback'}
              </span>
            </div>
          </div>
          
          {/* Custom Controls */}
          <div className="flex items-center justify-center gap-6 p-4">
            <button 
              onClick={() => skip(-5)}
              disabled={isProcessing || !selectedVideo}
              className="text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Rewind className="h-5 w-5" />
            </button>
            <button
              onClick={togglePlay}
              disabled={isProcessing || !selectedVideo}
              className={`p-3 rounded-full transition-colors ${
                selectedVideo && !isProcessing
                  ? "bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_15px_rgba(37,99,235,0.3)]" 
                  : "bg-slate-800 text-slate-600 cursor-not-allowed"
              }`}
            >
              {playing ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5 fill-current ml-0.5" />}
            </button>
            <button 
              onClick={() => skip(5)}
              disabled={isProcessing || !selectedVideo}
              className="text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FastForward className="h-5 w-5" />
            </button>
          </div>
        </motion.div>

        {/* --- EVENT ARCHIVE GRID --- */}
        <div className="max-w-5xl mx-auto">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4 px-1">
            Archived Event Clips
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {alerts.length === 0 ? (
              <div className="col-span-full p-8 text-center border border-dashed border-slate-800 rounded-xl text-slate-500">
                No video clips have been fully recorded yet.
              </div>
            ) : (
              alerts.map((alert) => {
                const isSecurity = alert.type === "INTRUSION";
                const Icon = isSecurity ? ShieldAlert : AlertTriangle;
                
                return (
                  <button
                    key={alert.id}
                    onClick={() => {
                      setSelectedVideo(alert.video_clip_path);
                      setIsProcessing(false); // Cancel processing state if user manually clicks an older video
                    }}
                    className={`flex items-start gap-4 p-4 rounded-xl border text-left transition-all ${
                      selectedVideo === alert.video_clip_path && !isProcessing
                        ? "bg-slate-800 border-blue-500/50 shadow-md"
                        : "bg-slate-900/50 border-slate-800 hover:bg-slate-800 hover:border-slate-700"
                    }`}
                  >
                    <div className={`p-2.5 rounded-lg shrink-0 ${
                      isSecurity ? "bg-orange-500/10 text-orange-500" : "bg-red-500/10 text-red-500"
                    }`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                      <h4 className="font-bold text-sm text-slate-200 truncate">
                        {alert.type.replace(/_/g, " ")}
                      </h4>
                      <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">
                        {alert.message}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-medium tracking-wide ${
                          alert.status === "FALSE_ALARM" ? "bg-slate-800 text-slate-400" : "bg-slate-800 text-slate-300"
                        }`}>
                          {alert.status.replace(/_/g, " ")}
                        </span>
                        <span className="text-[10px] text-slate-500 font-mono">
                          {new Date(alert.time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </span>
                      </div>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>

      </main>
    </div>
  );
}