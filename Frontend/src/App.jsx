import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./lib/auth-context";
import { AlertProvider } from "./lib/alert-context"; 
import ProtectedRoute from "./components/ProtectedRoute";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import SecurityDashboard from "./pages/SecurityDashboard"; 
import AlertHistory from "./pages/AlertHistory";
import VideoPlayback from "./pages/VideoPlayback";
import Login from "./pages/Login";
import Register from "./pages/Register";
import PatientSetup from "./pages/PatientSetup";
import { SecurityAlertPopup } from "./components/SecurityAlertPopup"; 

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <AlertProvider> 
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route 
              path="/setup" 
              element={
                <ProtectedRoute>
                  <PatientSetup />
                </ProtectedRoute>
              } 
            />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <div className="flex min-h-screen bg-[#020817]">
                    <Sidebar />
                    <div className="flex-1 overflow-x-hidden relative">
                      <Routes>
    
                        <Route path="/" element={<Dashboard />} />
                        {/* New Security path */}
                        <Route path="/security" element={<SecurityDashboard />} />
                        <Route path="/alerts" element={<AlertHistory />} />
                        <Route path="/playback" element={<VideoPlayback />} />
                        <Route path="*" element={<Navigate to="/" replace />} />
                      </Routes>
                      
                      
                      <SecurityAlertPopup />
                    </div>
                  </div>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AlertProvider>
      </AuthProvider>
    </Router>
  );
}