import React, { createContext, useContext, useState, useEffect } from 'react';

// Create the context
const AlertContext = createContext();

export function AlertProvider({ children }) {
  // Global history of all alerts
  const [alerts, setAlerts] = useState([]);
  
  // States for the Indoor Wellness (Red) Popup
  const [activeAlert, setActiveAlert] = useState(null);
  const [showPopup, setShowPopup] = useState(false);

  // States for the Outdoor Security (Orange) Popup
  const [activeSecurityAlert, setActiveSecurityAlert] = useState(null);
  const [showSecurityPopup, setShowSecurityPopup] = useState(false);

  // Initialize the live WebSocket connection to the Python backend
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/alerts");

    ws.onopen = () => console.log("✅ Connected to Alert WebSocket");
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("🚨 New Alert Received:", data);

      // Format the incoming Python data so React can use it easily
      const newAlert = {
        ...data,
        id: data.alert_id,
        timestamp: new Date(data.time),
        // Determine if this belongs to the Security or Health dashboard
        category: data.type === "INTRUSION" ? "security" : "health", 
        location: data.type === "INTRUSION" ? "Outdoor Camera" : "Indoor Camera 01",
        status: "PENDING" // Default status until a user clicks a button
      };

      // Add the new alert to the top of the history log
      setAlerts((prev) => [newAlert, ...prev]);

      // Trigger the correct popup based on the alert category
      if (newAlert.category === "security") {
        setActiveSecurityAlert(newAlert);
        setShowSecurityPopup(true);
      } else {
        // Only pop up the giant red screen for real medical emergencies
        if (["EMERGENCY", "FALL_WARNING", "HIGH_RISK"].includes(newAlert.type)) {
          setActiveAlert(newAlert);
          setShowPopup(true);
        }
      }
    };

    ws.onclose = () => console.log("❌ Disconnected from Alert WebSocket");

    // Cleanup the WebSocket if the user logs out or closes the app
    return () => ws.close();
  }, []);

  // --- ACTIONS FOR INDOOR WELLNESS ---
  const dismissAlert = () => {
    setShowPopup(false);
  };

  // --- ACTIONS FOR OUTDOOR SECURITY ---
  const dismissSecurityAlert = () => {
    setShowSecurityPopup(false);
  };

  const acknowledgeSecurityAlert = () => {
    // Just hides the popup so the user can view the live outdoor feed
    setShowSecurityPopup(false);
  };

  const markSecurityFalseAlarm = async (alertId) => {
    try {
      // 1. Tell Python backend to kill the timer, snooze the AI, and update the DB
      await fetch(`http://localhost:8000/alerts/${alertId}/confirm?status=FALSE_ALARM`, {
        method: "POST"
      });
      
      // 2. Hide the popup on the React screen
      setShowSecurityPopup(false);
      setActiveSecurityAlert(null);
      
      // 3. Update the local state so the Dashboard log shows it was resolved
      setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, status: 'FALSE_ALARM' } : a));
      
      console.log(`Successfully cancelled security alert ${alertId}`);
    } catch (err) {
      console.error("Failed to mark security false alarm", err);
    }
  };

  // Provide all these variables and functions to the rest of the app
  return (
    <AlertContext.Provider
      value={{
        alerts,
        
        // Indoor Health Exports
        activeAlert,
        showPopup,
        dismissAlert,
        
        // Outdoor Security Exports
        activeSecurityAlert,
        showSecurityPopup,
        dismissSecurityAlert,
        acknowledgeSecurityAlert,
        markSecurityFalseAlarm
      }}
    >
      {children}
    </AlertContext.Provider>
  );
}

// Custom hook to use the context easily in any component
export const useAlerts = () => {
  const context = useContext(AlertContext);
  if (!context) {
    throw new Error("useAlerts must be used within an AlertProvider");
  }
  return context;
};