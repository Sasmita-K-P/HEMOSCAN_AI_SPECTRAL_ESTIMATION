import React from 'react';
import { ArrowRight, Info, AlertCircle, CheckCircle2, Zap, Calendar } from 'lucide-react';
import { ViewState, AnalysisResult } from '../types';

interface HomeProps {
  onNavigate: (view: ViewState) => void;
  lastResult: AnalysisResult | null;
}

const Home: React.FC<HomeProps> = ({ onNavigate, lastResult }) => {
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good Morning";
    if (hour < 18) return "Good Afternoon";
    return "Good Evening";
  };

  return (
    <div className="p-4 space-y-6">
      
      {/* Header / Greeting */}
      <div className="px-1">
        <h2 className="text-xl font-bold text-slate-800">{getGreeting()}</h2>
        <p className="text-sm text-slate-500">Ready for your health check?</p>
      </div>

      {/* Latest Result Card */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-100 relative overflow-hidden">
        {/* Background Accent */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-slate-50 rounded-full -mr-10 -mt-10 z-0"></div>
        
        <div className="relative z-10">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest flex items-center gap-2">
              <Calendar className="w-3 h-3" /> Latest Screening
            </h2>
            {lastResult && (
              <span className="text-xs font-medium text-slate-400 bg-slate-50 px-2 py-1 rounded-full">
                {new Date(lastResult.timestamp).toLocaleDateString()}
              </span>
            )}
          </div>

          {lastResult ? (
            <div className="space-y-4">
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-bold text-slate-900 tracking-tight">{lastResult.hb_estimate_g_dl}</span>
                <span className="text-lg font-medium text-slate-500">g/dL</span>
              </div>
              <div className="flex flex-wrap gap-2">
                <span className={`px-3 py-1.5 rounded-full text-xs font-bold border ${
                  lastResult.anemia_class === 'Normal' ? 'bg-emerald-50 text-emerald-700 border-emerald-100' :
                  lastResult.anemia_class === 'Severe' ? 'bg-rose-50 text-rose-700 border-rose-100' :
                  'bg-amber-50 text-amber-700 border-amber-100'
                }`}>
                  {lastResult.anemia_class}
                </span>
                <span className="px-3 py-1.5 rounded-full text-xs font-bold bg-slate-50 text-slate-600 border border-slate-100">
                  Confidence: {Math.round(lastResult.confidence * 100)}%
                </span>
              </div>
              <button 
                onClick={() => onNavigate('RESULT')}
                className="w-full mt-2 py-2.5 text-sm text-teal-700 font-bold bg-teal-50 hover:bg-teal-100 rounded-xl transition-colors flex items-center justify-center gap-1"
              >
                View Full Report <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="text-center py-6 text-slate-400">
              <p className="text-sm mb-4">No recent scans found.</p>
              <button 
                onClick={() => onNavigate('SCAN')}
                className="text-teal-600 font-bold text-sm hover:underline"
              >
                Start your first scan
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Quick Action - Improved Gradient */}
      <div className="bg-gradient-to-br from-teal-600 via-teal-700 to-teal-800 rounded-3xl p-6 shadow-xl shadow-teal-900/10 text-white relative overflow-hidden group">
        <div className="relative z-10">
          <div className="flex items-start justify-between">
            <div>
                <h3 className="text-2xl font-bold mb-2">Check Hemoglobin</h3>
                <p className="text-teal-100/90 text-sm mb-6 max-w-[80%] leading-relaxed">
                    Clinical-grade AI analysis using just your smartphone camera.
                </p>
            </div>
            <div className="bg-white/10 p-2 rounded-xl backdrop-blur-sm">
                <Zap className="w-6 h-6 text-teal-200" />
            </div>
          </div>
          <button
            onClick={() => onNavigate('SCAN')}
            className="bg-white text-teal-800 px-8 py-3.5 rounded-xl font-bold text-sm shadow-lg shadow-black/5 active:scale-95 transition-transform flex items-center gap-2 group-hover:gap-3"
          >
            Start Scan <ArrowRight className="w-4 h-4 transition-all" />
          </button>
        </div>
        
        {/* Decorative Circles */}
        <div className="absolute -right-8 -top-8 w-40 h-40 bg-white/10 rounded-full blur-2xl group-hover:bg-white/15 transition-all duration-500"></div>
        <div className="absolute -right-4 bottom-0 w-32 h-32 bg-teal-400/20 rounded-full blur-xl group-hover:scale-110 transition-transform duration-500"></div>
      </div>

      {/* Daily Health Tip */}
      <div className="bg-amber-50 border border-amber-100 rounded-2xl p-5 flex items-start gap-4">
        <div className="bg-amber-100 p-2 rounded-full shrink-0">
            <Info className="w-5 h-5 text-amber-600" />
        </div>
        <div>
            <h4 className="text-sm font-bold text-amber-800 mb-1">Daily Health Tip</h4>
            <p className="text-xs text-amber-700/80 leading-relaxed">
                Iron-rich foods like spinach, lentils, and red meat can help improve hemoglobin levels. Combine with Vitamin C for better absorption.
            </p>
        </div>
      </div>

      {/* Education / Info */}
      <div className="space-y-4 pt-2">
        <div className="flex items-center justify-between px-1">
             <h3 className="text-sm font-bold text-slate-800">How it works</h3>
        </div>
        
        <div className="grid grid-cols-2 gap-3">
            <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm flex flex-col gap-3">
                <div className="p-2 bg-blue-50 rounded-lg w-fit">
                    <AlertCircle className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                    <h4 className="font-bold text-xs text-slate-800 mb-1">Visual Analysis</h4>
                    <p className="text-[10px] text-slate-500 leading-relaxed">
                        We analyze nail bed color absorption and vascular density.
                    </p>
                </div>
            </div>
            <div className="bg-white p-4 rounded-2xl border border-slate-100 shadow-sm flex flex-col gap-3">
                <div className="p-2 bg-emerald-50 rounded-lg w-fit">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                    <h4 className="font-bold text-xs text-slate-800 mb-1">Privacy First</h4>
                    <p className="text-[10px] text-slate-500 leading-relaxed">
                        No personal images are stored on servers without specific consent.
                    </p>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
};

export default Home;