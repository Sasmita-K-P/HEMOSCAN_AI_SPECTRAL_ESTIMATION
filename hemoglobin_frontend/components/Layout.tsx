import React from 'react';
import { Home, Camera, History, User, Activity } from 'lucide-react';
import { ViewState } from '../types';

interface LayoutProps {
  currentView: ViewState;
  onChangeView: (view: ViewState) => void;
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ currentView, onChangeView, children }) => {
  
  const navItems = [
    { id: 'HOME', icon: Home, label: 'Home' },
    { id: 'SCAN', icon: Camera, label: 'Scan' },
    { id: 'HISTORY', icon: History, label: 'History' },
    { id: 'PROFILE', icon: User, label: 'Profile' },
  ];

  return (
    <div className="min-h-screen bg-slate-50/50 flex flex-col max-w-md mx-auto shadow-2xl overflow-hidden relative border-x border-slate-200">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 p-4 sticky top-0 z-20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="bg-gradient-to-tr from-teal-600 to-teal-500 p-1.5 rounded-lg shadow-sm">
              <Activity className="text-white w-5 h-5" />
            </div>
            <h1 className="text-xl font-bold text-slate-800 tracking-tight">HemoScan AI</h1>
          </div>
          <div className="text-[10px] font-bold text-teal-700 bg-teal-50 px-2.5 py-1 rounded-full border border-teal-100 tracking-wide uppercase">
            Beta v1.0
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto pb-24 scroll-smooth no-scrollbar">
        {children}
      </main>

      {/* Bottom Navigation */}
      <nav className="absolute bottom-0 left-0 right-0 bg-white/90 backdrop-blur-lg border-t border-slate-200 px-6 py-2 z-30 flex justify-between items-center shadow-[0_-4px_20px_-5px_rgba(0,0,0,0.05)] pb-6 pt-3">
        {navItems.map((item) => {
          const isActive = currentView === item.id;
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => onChangeView(item.id as ViewState)}
              className={`flex flex-col items-center gap-1.5 transition-all duration-300 relative group px-2 ${
                isActive ? 'text-teal-600 -translate-y-1' : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              {isActive && (
                <div className="absolute -top-3 w-8 h-1 bg-teal-500 rounded-b-full"></div>
              )}
              <Icon className={`w-6 h-6 ${isActive ? 'fill-teal-100' : ''}`} strokeWidth={isActive ? 2.5 : 2} />
              <span className={`text-[10px] font-bold ${isActive ? 'opacity-100' : 'opacity-80'}`}>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
};

export default Layout;