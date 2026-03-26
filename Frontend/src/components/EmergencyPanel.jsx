export default function EmergencyPanel() {
  const callEmergency = () => {
    window.location.href = "tel:+919876543210"
  }

  return (
    <div className="bg-red-950/30 border border-red-900/50 rounded-2xl shadow-xl p-6 flex flex-col items-center justify-center text-center">
      <h2 className="text-red-400 font-bold mb-2 uppercase tracking-wide">Emergency Actions</h2>
      <p className="text-slate-400 text-sm mb-6">Instantly alert medical staff and responders.</p>
      
      <button 
        onClick={callEmergency}
        className="w-full bg-red-600 hover:bg-red-500 text-white font-bold py-4 rounded-xl shadow-[0_0_15px_rgba(220,38,38,0.5)] transition-all active:scale-95 text-lg tracking-wider"
      >
        CALL EMERGENCY
      </button>
    </div>
  )
}