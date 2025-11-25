import React from 'react';
import { AnalysisResult, AnemiaClass } from '../types';
import { ChevronRight, Calendar, TrendingUp } from 'lucide-react';

interface HistoryProps {
  history: AnalysisResult[];
  onSelect: (result: AnalysisResult) => void;
}

const History: React.FC<HistoryProps> = ({ history, onSelect }) => {
  if (history.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-slate-400">
        <div className="bg-slate-100 p-6 rounded-full mb-6">
            <Calendar className="w-10 h-10 text-slate-300" />
        </div>
        <h3 className="text-lg font-bold text-slate-700 mb-1">No history yet</h3>
        <p className="text-sm">Your past scans will appear here.</p>
      </div>
    );
  }

  const sortedHistory = [...history].sort((a, b) => a.timestamp - b.timestamp);
  const reversedHistory = [...sortedHistory].reverse();

  const getBadgeColor = (cls: AnemiaClass) => {
    switch (cls) {
      case AnemiaClass.NORMAL: return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case AnemiaClass.SEVERE: return 'bg-rose-100 text-rose-800 border-rose-200';
      default: return 'bg-amber-100 text-amber-800 border-amber-200';
    }
  };

  // --- SVG Chart Logic ---
  const chartHeight = 100;
  const chartWidth = 340; // Approx mobile width
  const padding = 20;

  // Normalize data for chart
  const dataPoints = sortedHistory.slice(-5); // Last 5 points for cleanliness
  const maxHb = Math.max(...dataPoints.map(d => d.hb_estimate_g_dl), 14) + 1;
  const minHb = Math.min(...dataPoints.map(d => d.hb_estimate_g_dl), 8) - 1;
  
  const getX = (index: number) => {
    if (dataPoints.length === 1) return chartWidth / 2;
    return padding + (index * ((chartWidth - (padding * 2)) / (dataPoints.length - 1)));
  };
  
  const getY = (hb: number) => {
    return chartHeight - padding - ((hb - minHb) / (maxHb - minHb)) * (chartHeight - (padding * 2));
  };

  const points = dataPoints.map((d, i) => `${getX(i)},${getY(d.hb_estimate_g_dl)}`).join(' ');

  return (
    <div className="p-4 space-y-6">
      
      {/* Trend Chart Card */}
      {history.length > 1 && (
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-100">
          <div className="flex items-center gap-2 mb-4">
             <div className="p-1.5 bg-teal-50 rounded-lg">
                <TrendingUp className="w-4 h-4 text-teal-600" />
             </div>
             <h3 className="font-bold text-slate-800 text-sm">Hemoglobin Trend</h3>
          </div>
          
          <div className="relative h-[100px] w-full">
            <svg width="100%" height="100%" viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="overflow-visible">
               {/* Reference Lines */}
               <line x1="0" y1={getY(12)} x2={chartWidth} y2={getY(12)} stroke="#cbd5e1" strokeWidth="1" strokeDasharray="4 4" opacity="0.5" />
               <text x={chartWidth} y={getY(12) - 4} fontSize="10" fill="#94a3b8" textAnchor="end">Normal (12)</text>

               {/* Trend Line */}
               <polyline
                 points={points}
                 fill="none"
                 stroke="#0d9488"
                 strokeWidth="3"
                 strokeLinecap="round"
                 strokeLinejoin="round"
                 className="drop-shadow-sm"
               />
               {/* Data Points */}
               {dataPoints.map((d, i) => (
                 <circle 
                    key={d.id} 
                    cx={getX(i)} 
                    cy={getY(d.hb_estimate_g_dl)} 
                    r="4" 
                    fill="white" 
                    stroke="#0d9488" 
                    strokeWidth="2" 
                 />
               ))}
            </svg>
          </div>
          <p className="text-[10px] text-slate-400 text-center mt-2">Last 5 scans</p>
        </div>
      )}

      <div className="space-y-3">
        <h2 className="text-sm font-bold text-slate-500 uppercase tracking-wider px-1">Recent Scans</h2>
        {reversedHistory.map((scan) => (
            <button
            key={scan.id}
            onClick={() => onSelect(scan)}
            className="w-full bg-white p-4 rounded-xl border border-slate-100 shadow-sm flex items-center gap-4 hover:shadow-md transition-all active:scale-[0.99] group"
            >
            <div className="relative w-14 h-14 rounded-xl bg-slate-100 overflow-hidden shrink-0 border border-slate-200">
                <img src={scan.imageUrl} alt="Thumb" className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
            </div>
            <div className="flex-1 text-left">
                <div className="flex justify-between items-center mb-1">
                    <span className="font-bold text-slate-900 text-lg">{scan.hb_estimate_g_dl} <span className="text-xs font-normal text-slate-400">g/dL</span></span>
                    <span className="text-[10px] font-medium text-slate-400 bg-slate-50 px-2 py-1 rounded-full">
                        {new Date(scan.timestamp).toLocaleDateString()}
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${getBadgeColor(scan.anemia_class)}`}>
                        {scan.anemia_class}
                    </span>
                    <span className="text-[10px] text-slate-400 flex items-center gap-1">
                        • {Math.round(scan.confidence * 100)}% conf.
                    </span>
                </div>
            </div>
            <ChevronRight className="w-5 h-5 text-slate-300 group-hover:text-teal-500 transition-colors" />
            </button>
        ))}
      </div>
    </div>
  );
};

export default History;