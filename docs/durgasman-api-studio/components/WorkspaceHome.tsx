
import React from 'react';
import { Collection, HistoryItem } from '../types';
import { LayoutGrid, Clock, Plus, Zap, ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';

interface WorkspaceHomeProps {
  collections: Collection[];
  history: HistoryItem[];
  onNewRequest: () => void;
  onImport: () => void;
}

const WorkspaceHome: React.FC<WorkspaceHomeProps> = ({ collections, history, onNewRequest, onImport }) => {
  return (
    <div className="flex-1 bg-[#0f172a] overflow-y-auto p-12 custom-scrollbar">
      <div className="max-w-5xl mx-auto space-y-12">
        {/* HERO */}
        <div className="space-y-4">
          <div className="flex items-center gap-3">
             <div className="px-3 py-1 bg-orange-500/10 border border-orange-500/20 rounded-full text-orange-500 text-[10px] font-bold uppercase tracking-widest animate-pulse">
                Active Workspace
             </div>
             <div className="flex items-center gap-1.5 text-indigo-400 text-[10px] font-bold uppercase tracking-widest">
                <Sparkles size={12} /> Gemini Enhanced
             </div>
          </div>
          <h1 className="text-4xl font-extrabold text-white tracking-tight">Welcome to Durgasman Studio</h1>
          <p className="text-slate-400 text-lg max-w-2xl">High-performance API development with native AI assistance. Debug, document, and test your services faster than ever.</p>
        </div>

        {/* QUICK ACTIONS */}
        <div className="grid grid-cols-3 gap-6">
          <button onClick={onNewRequest} className="group p-6 bg-slate-900 border border-slate-800 rounded-xl hover:border-orange-500/50 transition-all text-left shadow-xl hover:shadow-orange-500/5">
            <div className="w-12 h-12 bg-orange-500/10 rounded-lg flex items-center justify-center text-orange-500 mb-4 group-hover:scale-110 transition-transform">
              <Plus size={24} />
            </div>
            <h3 className="text-white font-bold mb-1">Create New Request</h3>
            <p className="text-xs text-slate-500">Start from scratch or use AI to generate a definition.</p>
          </button>
          <button onClick={onImport} className="group p-6 bg-slate-900 border border-slate-800 rounded-xl hover:border-blue-500/50 transition-all text-left shadow-xl hover:shadow-blue-500/5">
            <div className="w-12 h-12 bg-blue-500/10 rounded-lg flex items-center justify-center text-blue-500 mb-4 group-hover:scale-110 transition-transform">
              <Zap size={24} />
            </div>
            <h3 className="text-white font-bold mb-1">Import Collection</h3>
            <p className="text-xs text-slate-500">Drop a Postman JSON or cURL command to import.</p>
          </button>
          <div className="p-6 bg-indigo-600/10 border border-indigo-500/20 rounded-xl text-left shadow-xl">
            <div className="w-12 h-12 bg-indigo-500/10 rounded-lg flex items-center justify-center text-indigo-400 mb-4">
              <ShieldCheck size={24} />
            </div>
            <h3 className="text-white font-bold mb-1">AI Mocking Active</h3>
            <p className="text-xs text-slate-500">Your mock endpoints are ready to intercept traffic.</p>
          </div>
        </div>

        {/* RECENT ACTIVITY */}
        <div className="grid grid-cols-2 gap-8">
           <div className="space-y-4">
              <div className="flex items-center justify-between">
                 <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                    <Clock size={16} /> Recent History
                 </h2>
                 <button className="text-[10px] font-bold text-orange-500 hover:underline">View All</button>
              </div>
              <div className="space-y-2">
                 {history.slice(0, 5).map(item => (
                    <div key={item.id} className="p-3 bg-slate-900/50 border border-slate-800/50 rounded-lg flex items-center justify-between hover:bg-slate-800 transition-colors cursor-pointer">
                       <div className="flex items-center gap-3">
                          <span className="text-[10px] font-bold text-green-500">{item.method}</span>
                          <span className="text-xs text-slate-300 truncate max-w-[200px]">{item.url}</span>
                       </div>
                       <span className="text-[10px] text-slate-600">{new Date(item.timestamp).toLocaleTimeString()}</span>
                    </div>
                 ))}
                 {history.length === 0 && <p className="text-xs text-slate-600 italic py-4">No recent history.</p>}
              </div>
           </div>

           <div className="space-y-4">
              <div className="flex items-center justify-between">
                 <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                    <LayoutGrid size={16} /> My Collections
                 </h2>
                 <button className="text-[10px] font-bold text-orange-500 hover:underline">Manage</button>
              </div>
              <div className="grid grid-cols-1 gap-2">
                 {collections.map(col => (
                    <div key={col.id} className="p-4 bg-slate-900/50 border border-slate-800/50 rounded-lg flex items-center justify-between group cursor-pointer hover:border-slate-700">
                       <div>
                          <h4 className="text-sm font-bold text-slate-200">{col.name}</h4>
                          <p className="text-[10px] text-slate-600 uppercase tracking-tighter">{col.requests.length} Requests</p>
                       </div>
                       <ArrowRight size={14} className="text-slate-700 group-hover:text-orange-500 transition-colors" />
                    </div>
                 ))}
                 {collections.length === 0 && <p className="text-xs text-slate-600 italic py-4">No collections found.</p>}
              </div>
           </div>
        </div>
      </div>
    </div>
  );
};

export default WorkspaceHome;
