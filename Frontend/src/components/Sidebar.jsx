import { Link, useLocation } from "react-router-dom";
import { Shield, LayoutDashboard, Bell, Video, LogOut, ShieldAlert } from "lucide-react";
import { useAuth } from "../lib/auth-context";

export default function Sidebar() {
  const location = useLocation();
  const { user, logout } = useAuth();

  const navItems = [
    { name: "Indoor Wellness", path: "/", icon: LayoutDashboard },
    { name: "Outdoor Security", path: "/security", icon: ShieldAlert },
    { name: "Alert History", path: "/alerts", icon: Bell },
    { name: "Video Playback", path: "/playback", icon: Video },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 hidden lg:flex flex-col bg-[#0f172a] h-screen sticky top-0">
      <div className="p-5 border-b border-slate-800 flex items-center gap-2">
        <Shield className="h-6 w-6 text-blue-500" />
        <span className="font-bold text-lg tracking-wide text-slate-200">Steins Gate</span>
      </div>
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.name}
              to={item.path}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors font-medium ${
                isActive
                  ? "bg-slate-800/80 text-blue-400"
                  : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"
              }`}
            >
              <item.icon className="h-4 w-4" /> {item.name}
            </Link>
          );
        })}
      </nav>
      {user && (
        <div className="p-4 border-t border-slate-800">
          <div className="mb-3 px-2">
            <p className="text-sm font-medium text-slate-200">{user.name}</p>
            <p className="text-xs text-slate-500 capitalize">{user.role.toLowerCase()} User</p>
          </div>
          <button 
            onClick={logout}
            className="flex items-center gap-3 px-3 py-2 w-full rounded-lg text-slate-400 hover:bg-red-500/10 hover:text-red-500 transition-colors font-medium"
          >
            <LogOut className="h-4 w-4" /> Logout
          </button>
        </div>
      )}
    </aside>
  );
}