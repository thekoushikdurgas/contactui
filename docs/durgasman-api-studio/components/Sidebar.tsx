
import React from 'react';
import { Folder, Plus, Search, ChevronRight, ChevronDown, History, Server, Layers, Trash2, Download, Box, Check, X, FileText, Sparkles, Filter } from 'lucide-react';
import { Collection, ApiRequest, HistoryItem, MockEndpoint, Environment, EnvVariable } from '../types';

interface SidebarProps {
  collections: Collection[];
  history: HistoryItem[];
  mocks: MockEndpoint[];
  environments: Environment[];
  activeRequestId: string | null;
  onSelectRequest: (request: Partial<ApiRequest>) => void;
  onSelectMock: (mock: MockEndpoint) => void;
  onSelectEnvironment: (id: string | null) => void;
  onUpdateEnvironment: (env: Environment) => void;
  onCreateCollection: () => void;
  onCreateMock: () => void;
  onCreateEnvironment: () => void;
  onClearHistory: () => void;
  onImport: (file: File) => void;
  onGenerateDocs: (collection: Collection) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  collections, history, mocks, environments, activeRequestId, onSelectRequest, 
  onSelectMock, onSelectEnvironment, onUpdateEnvironment, onCreateCollection, 
  onCreateMock, onCreateEnvironment, onClearHistory, onImport, onGenerateDocs
}) => {
  const [activeTab, setActiveTab] = React.useState<'collections' | 'history' | 'mocks' | 'envs'>('collections');
  const [expanded, setExpanded] = React.useState<Record<string, boolean>>({});
  const [searchTerm, setSearchTerm] = React.useState('');
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const toggleExpand = (id: string) => setExpanded(prev => ({ ...prev, [id]: !prev[id] }));

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) { onImport(file); if (fileInputRef.current) fileInputRef.current.value = ''; }
  };

  const filteredCollections = collections.filter(col => 
    col.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    col.requests.some(req => req.name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="w-72 bg-[#050505] border-r border-slate-800 flex flex-col h-full select-none shadow-2xl z-20">
      <div className="flex border-b border-slate-800 shrink-0 bg-slate-900/20">
        {(['collections', 'envs', 'history', 'mocks'] as const).map(tab => (
          <button 
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`flex-1 py-3 text-[10px] font-bold uppercase tracking-widest flex flex-col items-center gap-1 transition-all ${activeTab === tab ? 'text-orange-500 bg-orange-500/10 border-b-2 border-orange-500' : 'text-slate-500 hover:text-slate-300'}`}
          >
            {tab === 'collections' && <Layers size={14} />}
            {tab === 'envs' && <Box size={14} />}
            {tab === 'history' && <History size={14} />}
            {tab === 'mocks' && <Server size={14} />}
            {tab.slice(0, 4)}
          </button>
        ))}
      </div>

      <div className="p-3 space-y-3 shrink-0">
        <div className="flex items-center justify-between">
          <h2 className="font-bold text-[10px] text-slate-500 uppercase tracking-widest">
            {activeTab}
          </h2>
          <div className="flex items-center gap-0.5">
            <button onClick={() => fileInputRef.current?.click()} className="p-1 hover:bg-slate-800 rounded text-slate-500 transition-colors" title="Import JSON"><Download size={14} /></button>
            <button onClick={() => {
              if (activeTab === 'collections') onCreateCollection();
              if (activeTab === 'envs') onCreateEnvironment();
              if (activeTab === 'mocks') onCreateMock();
            }} className="p-1 hover:bg-slate-800 rounded text-slate-500 transition-colors" title="New Item"><Plus size={14} /></button>
            <input type="file" ref={fileInputRef} onChange={handleFileChange} className="hidden" accept=".json" />
          </div>
        </div>

        <div className="relative">
          <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" />
          <input 
            type="text" 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder={`Filter ${activeTab}...`}
            className="w-full bg-slate-900/50 border border-slate-800 rounded-md pl-8 pr-3 py-1.5 text-[11px] text-slate-300 placeholder-slate-600 outline-none focus:ring-1 focus:ring-orange-500/50"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-2 pb-4 space-y-0.5 custom-scrollbar">
        {activeTab === 'collections' && filteredCollections.map(col => (
          <div key={col.id} className="mb-0.5">
            <div 
              onClick={() => toggleExpand(col.id)}
              className="flex items-center px-2 py-2 hover:bg-slate-800/40 rounded-md cursor-pointer text-slate-400 group transition-colors"
            >
              <div className="flex items-center flex-1 min-w-0">
                {expanded[col.id] || searchTerm ? <ChevronDown size={14} className="mr-2 text-slate-600" /> : <ChevronRight size={14} className="mr-2 text-slate-600" />}
                <Folder size={14} className={`mr-2 ${expanded[col.id] ? 'text-orange-500' : 'text-slate-500'}`} />
                <span className={`text-xs font-semibold truncate ${expanded[col.id] ? 'text-slate-200' : 'text-slate-400'}`}>{col.name}</span>
              </div>
              <button 
                onClick={(e) => { e.stopPropagation(); onGenerateDocs(col); }}
                className="opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-700 rounded text-indigo-400 transition-all"
                title="Generate AI Docs"
              >
                <Sparkles size={12} />
              </button>
            </div>
            
            {(expanded[col.id] || searchTerm) && (
              <div className="ml-4 mt-0.5 pl-2 border-l border-slate-800 space-y-0.5">
                {col.requests.filter(req => req.name.toLowerCase().includes(searchTerm.toLowerCase())).map(req => (
                  <div 
                    key={req.id}
                    onClick={() => onSelectRequest(req)}
                    className={`flex items-center px-3 py-1.5 cursor-pointer group rounded-md text-[11px] transition-all ${
                      activeRequestId === req.id ? 'bg-orange-500/10 text-orange-500 shadow-sm' : 'hover:bg-slate-800/60 text-slate-500 hover:text-slate-300'
                    }`}
                  >
                    <span className={`w-10 font-black ${getMethodColor(req.method)} text-[9px] uppercase`}>{req.method}</span>
                    <span className="truncate font-medium">{req.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {activeTab === 'envs' && environments.map(env => (
            <div 
              key={env.id}
              onClick={() => onSelectEnvironment(env.id)}
              className={`flex items-center px-3 py-2 rounded-md cursor-pointer transition-all ${onSelectEnvironment === env.id ? 'bg-orange-500/10 text-orange-500' : 'hover:bg-slate-800/40 text-slate-400'}`}
            >
                <Box size={14} className="mr-2" />
                <span className="text-xs font-medium">{env.name}</span>
            </div>
        ))}

        {activeTab === 'history' && history.map(item => (
            <div 
              key={item.id}
              onClick={() => onSelectRequest({ method: item.method, url: item.url, name: 'Historical Request', headers: item.headers, body: item.body })}
              className="flex items-center px-3 py-1.5 hover:bg-slate-800/40 rounded-md cursor-pointer group transition-all"
            >
                <span className={`w-10 font-black ${getMethodColor(item.method)} text-[9px] uppercase shrink-0`}>{item.method}</span>
                <span className="truncate text-[11px] text-slate-500 group-hover:text-slate-300">{item.url}</span>
            </div>
        ))}

        {activeTab === 'mocks' && mocks.map(mock => (
            <div 
              key={mock.id}
              onClick={() => onSelectMock(mock)}
              className="flex items-center px-3 py-1.5 hover:bg-slate-800/40 rounded-md cursor-pointer group transition-all"
            >
                <span className={`w-10 font-black ${getMethodColor(mock.method)} text-[9px] uppercase shrink-0`}>{mock.method}</span>
                <div className="flex flex-col min-w-0">
                    <span className="truncate text-[11px] text-slate-300 font-medium">{mock.path}</span>
                    <span className="text-[9px] text-slate-600 font-bold">{mock.status} {mock.enabled ? 'ACTIVE' : 'OFF'}</span>
                </div>
            </div>
        ))}
      </div>
    </div>
  );
};

function getMethodColor(method: string) {
  switch (method) {
    case 'GET': return 'text-emerald-500';
    case 'POST': return 'text-amber-500';
    case 'PUT': return 'text-sky-500';
    case 'PATCH': return 'text-violet-500';
    case 'DELETE': return 'text-rose-500';
    default: return 'text-slate-500';
  }
}

export default Sidebar;
