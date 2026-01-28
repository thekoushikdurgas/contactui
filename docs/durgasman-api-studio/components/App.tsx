
import React from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Collection, HttpMethod, ApiRequest, ApiResponse, HistoryItem, MockEndpoint, ChatMessage, Environment, EnvVariable, AppView } from './types';
import Sidebar from './components/Sidebar';
import RequestBuilder from './components/RequestBuilder';
import ResponseViewer from './components/ResponseViewer';
import AIChatPanel from './components/AIChatPanel';
import MockEditor from './components/MockEditor';
import WorkspaceHome from './components/WorkspaceHome';
import { chatWithGemini, generateCollectionDocs, analyzeApiResponse } from './services/geminiService';
import { Settings, LayoutGrid, Bot, X, Box, ChevronDown, Cat, Home, Sparkles, Loader2, FileText, Search } from 'lucide-react';

const INITIAL_REQUEST: ApiRequest = {
  id: uuidv4(),
  name: 'New Request',
  method: HttpMethod.GET,
  url: 'https://jsonplaceholder.typicode.com/posts/1',
  params: [],
  headers: [{ id: uuidv4(), key: 'Accept', value: 'application/json', enabled: true }],
  body: '',
  authType: 'None',
  preRequestScript: '',
  testScript: '',
};

const App: React.FC = () => {
  const [view, setView] = React.useState<AppView>('HOME');
  const [collections, setCollections] = React.useState<Collection[]>(() => {
    const saved = localStorage.getItem('durgasman_collections');
    return saved ? JSON.parse(saved) : [{ id: uuidv4(), name: 'Standard Examples', requests: [INITIAL_REQUEST] }];
  });

  const [history, setHistory] = React.useState<HistoryItem[]>(() => {
    const saved = localStorage.getItem('durgasman_history');
    return saved ? JSON.parse(saved) : [];
  });

  const [mocks, setMocks] = React.useState<MockEndpoint[]>(() => {
    const saved = localStorage.getItem('durgasman_mocks');
    return saved ? JSON.parse(saved) : [];
  });

  const [environments, setEnvironments] = React.useState<Environment[]>(() => {
    const saved = localStorage.getItem('durgasman_environments');
    return saved ? JSON.parse(saved) : [];
  });

  const [activeEnvironmentId, setActiveEnvironmentId] = React.useState<string | null>(localStorage.getItem('durgasman_active_env'));
  const [chatMessages, setChatMessages] = React.useState<ChatMessage[]>([]);
  const [activeRequest, setActiveRequest] = React.useState<ApiRequest>(INITIAL_REQUEST);
  const [activeMock, setActiveMock] = React.useState<MockEndpoint | null>(null);
  const [lastResponse, setLastResponse] = React.useState<ApiResponse | null>(null);
  const [isSending, setIsSending] = React.useState(false);
  const [isAnalyzing, setIsAnalyzing] = React.useState(false);
  const [analysisResult, setAnalysisResult] = React.useState<string | null>(null);
  const [isAIOpen, setIsAIOpen] = React.useState(false);
  const [isGeneratingDocs, setIsGeneratingDocs] = React.useState(false);
  const [selectedDocCollection, setSelectedDocCollection] = React.useState<Collection | null>(null);

  // Persistence
  React.useEffect(() => { localStorage.setItem('durgasman_collections', JSON.stringify(collections)); }, [collections]);
  React.useEffect(() => { localStorage.setItem('durgasman_history', JSON.stringify(history)); }, [history]);
  React.useEffect(() => { localStorage.setItem('durgasman_mocks', JSON.stringify(mocks)); }, [mocks]);
  React.useEffect(() => { localStorage.setItem('durgasman_environments', JSON.stringify(environments)); }, [environments]);
  React.useEffect(() => { localStorage.setItem('durgasman_active_env', activeEnvironmentId || ''); }, [activeEnvironmentId]);

  const handleUpdateActiveRequest = (updates: Partial<ApiRequest>) => setActiveRequest(prev => ({ ...prev, ...updates }));

  const resolveVariables = (str: string): string => {
    if (!str) return str;
    const activeEnv = environments.find(e => e.id === activeEnvironmentId);
    if (!activeEnv) return str;
    let resolved = str;
    activeEnv.variables.filter(v => v.enabled).forEach(v => {
      const regex = new RegExp(`{{${v.key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}}}`, 'g');
      resolved = resolved.replace(regex, v.value);
    });
    return resolved;
  };

  const handleSendRequest = async () => {
    setIsSending(true);
    setAnalysisResult(null);
    const start = Date.now();
    const resolvedUrl = resolveVariables(activeRequest.url);
    const resolvedBody = resolveVariables(activeRequest.body);
    const resolvedHeaders = activeRequest.headers.filter(h => h.enabled).reduce((acc, h) => ({ ...acc, [resolveVariables(h.key)]: resolveVariables(h.value) }), {});

    const hItem: HistoryItem = { id: uuidv4(), timestamp: start, method: activeRequest.method, url: activeRequest.url, body: activeRequest.body, headers: activeRequest.headers };
    setHistory(prev => [hItem, ...prev].slice(0, 50));

    try {
      const matchedMock = mocks.find(m => m.enabled && m.method === activeRequest.method && (resolvedUrl.endsWith(resolveVariables(m.path)) || resolvedUrl.includes(resolveVariables(m.path))));
      if (matchedMock) {
        await new Promise(r => setTimeout(r, 400));
        const data = JSON.parse(matchedMock.responseBody || '{}');
        setLastResponse({ status: matchedMock.status, statusText: 'Mock Response', time: Date.now() - start, size: (JSON.stringify(data).length / 1024).toFixed(2) + ' KB', headers: { 'X-Mock-Server': 'Durgasman-Local' }, data });
      } else {
        const response = await fetch(resolvedUrl, { 
          method: activeRequest.method, 
          headers: resolvedHeaders, 
          body: ['GET', 'HEAD'].includes(activeRequest.method) ? undefined : resolvedBody 
        });
        const contentType = response.headers.get('content-type');
        let data;
        if (contentType && contentType.includes('application/json')) {
            data = await response.json();
        } else {
            data = await response.text();
        }
        setLastResponse({ status: response.status, statusText: response.statusText, time: Date.now() - start, size: (JSON.stringify(data).length / 1024).toFixed(2) + ' KB', headers: Object.fromEntries(response.headers.entries()), data });
      }
    } catch (err: any) {
      setLastResponse({ status: 0, statusText: 'Error', time: Date.now() - start, size: '0 B', headers: {}, data: null, error: err.message || 'Failed to fetch' });
    } finally { setIsSending(false); }
  };

  const handleAnalyzeResponse = async () => {
    if (!lastResponse) return;
    setIsAnalyzing(true);
    try {
      const analysis = await analyzeApiResponse(lastResponse, activeRequest);
      setAnalysisResult(analysis);
    } catch (err) {
      alert("AI failed to analyze response.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSaveRequest = () => {
    setCollections(prev => prev.map(col => {
      const idx = col.requests.findIndex(r => r.id === activeRequest.id);
      if (idx !== -1) {
        const nr = [...col.requests]; nr[idx] = activeRequest;
        return { ...col, requests: nr };
      }
      return col;
    }));
  };

  const handleGenerateDocsAction = async (col: Collection) => {
    setIsGeneratingDocs(true);
    setView('DOCS');
    setSelectedDocCollection(col);
    try {
      const docs = await generateCollectionDocs(col);
      setCollections(prev => prev.map(c => c.id === col.id ? { ...c, aiDocs: docs } : c));
      setSelectedDocCollection(prev => prev ? { ...prev, aiDocs: docs } : null);
    } catch (err) {
      alert("AI failed to generate documentation.");
    } finally {
      setIsGeneratingDocs(false);
    }
  };

  const activeEnv = environments.find(e => e.id === activeEnvironmentId);

  return (
    <div className="flex flex-col h-screen overflow-hidden text-slate-200 bg-slate-950 font-sans">
      <header className="h-12 bg-[#0a0a0a] border-b border-slate-800 flex items-center justify-between px-4 shrink-0 z-50">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 cursor-pointer group" onClick={() => setView('HOME')}>
            <div className="w-7 h-7 bg-orange-600 rounded-lg flex items-center justify-center font-black text-white text-[11px] shadow-[0_0_20px_rgba(234,88,12,0.3)] transition-transform group-hover:scale-105">D</div>
            <div className="flex flex-col">
              <span className="font-black text-[10px] tracking-tight text-white uppercase italic leading-none">Durgasman</span>
              <span className="text-[8px] text-slate-600 font-bold uppercase tracking-widest leading-none mt-0.5">API Studio</span>
            </div>
          </div>
          <nav className="flex items-center gap-1">
            <button 
              onClick={() => setView('HOME')}
              className={`px-3 py-1.5 rounded-md flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider transition-all ${view === 'HOME' ? 'bg-orange-600/10 text-orange-500' : 'text-slate-500 hover:text-slate-300'}`}
            >
              <Home size={13} /> Home
            </button>
            <button 
              onClick={() => setView('BUILDER')}
              className={`px-3 py-1.5 rounded-md flex items-center gap-2 text-[10px] font-bold uppercase tracking-wider transition-all ${view === 'BUILDER' ? 'bg-orange-600/10 text-orange-500' : 'text-slate-500 hover:text-slate-300'}`}
            >
              <LayoutGrid size={13} /> Builder
            </button>
          </nav>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-md overflow-hidden h-7">
            <div className="px-2 flex items-center border-r border-slate-800 bg-slate-950">
               <Box size={10} className={activeEnv ? "text-orange-500" : "text-slate-600"} />
            </div>
            <div className="relative group">
              <button className="flex items-center gap-2 px-3 h-full text-[9px] font-black text-slate-400 uppercase tracking-widest hover:text-slate-200 transition-all">
                {activeEnv ? activeEnv.name : "Local Workspace"}
                <ChevronDown size={8} />
              </button>
              <div className="absolute right-0 top-full mt-1 w-48 bg-slate-900 border border-slate-800 rounded-md shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-[100] overflow-hidden">
                 <button onClick={() => setActiveEnvironmentId(null)} className="w-full text-left px-4 py-2.5 text-[9px] hover:bg-slate-800 text-slate-500 font-bold border-b border-slate-800 uppercase tracking-widest">Global Environment</button>
                {environments.map(env => (
                  <button key={env.id} onClick={() => setActiveEnvironmentId(env.id)} className={`w-full text-left px-4 py-2.5 text-[9px] font-bold uppercase tracking-widest hover:bg-slate-800 ${activeEnvironmentId === env.id ? 'text-orange-500 bg-orange-600/5' : 'text-slate-400'}`}>{env.name}</button>
                ))}
              </div>
            </div>
          </div>
          
          <div className="h-4 w-px bg-slate-800"></div>

          <div className="flex items-center gap-2 px-3 py-1 bg-indigo-600/10 rounded-full text-[9px] font-black text-indigo-400 border border-indigo-500/10 uppercase tracking-widest">
            <Sparkles size={10} /> AI Enhanced
          </div>
          <button className="p-1.5 hover:bg-slate-800 rounded-md transition-colors text-slate-500"><Settings size={15} /></button>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        <Sidebar 
          collections={collections} history={history} mocks={mocks} environments={environments} activeRequestId={activeRequest.id}
          onSelectRequest={(req) => { setActiveRequest(prev => ({ ...prev, ...req, id: req.id || prev.id })); setActiveMock(null); setView('BUILDER'); setAnalysisResult(null); }}
          onSelectMock={(mock) => { setActiveMock(mock); setView('BUILDER'); }}
          onSelectEnvironment={setActiveEnvironmentId}
          onUpdateEnvironment={env => setEnvironments(prev => prev.map(e => e.id === env.id ? env : e))}
          onCreateCollection={() => setCollections(prev => [...prev, { id: uuidv4(), name: 'New Collection', requests: [] }])}
          onCreateMock={() => { const nm: MockEndpoint = { id: uuidv4(), method: HttpMethod.GET, path: '/api/resource', responseBody: '{}', status: 200, enabled: true }; setMocks(prev => [...prev, nm]); setActiveMock(nm); setView('BUILDER'); }}
          onCreateEnvironment={() => setEnvironments(prev => [...prev, { id: uuidv4(), name: 'New Env', variables: [] }])}
          onClearHistory={() => setHistory([])}
          onImport={(file) => { /* Reuse import logic */ }}
          onGenerateDocs={handleGenerateDocsAction}
        />

        <div className="flex-1 flex overflow-hidden relative">
          {view === 'HOME' && <WorkspaceHome collections={collections} history={history} onNewRequest={() => setView('BUILDER')} onImport={() => {}} />}
          
          {view === 'BUILDER' && (
             <div className="flex-1 flex overflow-hidden">
                <div className="flex-1 flex flex-col min-w-0">
                  {activeMock ? (
                    <MockEditor mock={activeMock} onUpdate={u => { const nm = { ...activeMock, ...u }; setActiveMock(nm); setMocks(prev => prev.map(m => m.id === nm.id ? nm : m)); }} onDelete={() => { setMocks(prev => prev.filter(m => m.id !== activeMock.id)); setActiveMock(null); }} onClose={() => setActiveMock(null)} />
                  ) : (
                    <RequestBuilder request={activeRequest} onUpdate={handleUpdateActiveRequest} onSend={handleSendRequest} onSave={handleSaveRequest} isSending={isSending} />
                  )}
                </div>
                <div className="w-[480px] shrink-0 border-l border-slate-800 bg-slate-900/20">
                  <ResponseViewer 
                    response={lastResponse} 
                    activeRequest={activeRequest}
                    onAnalyze={handleAnalyzeResponse} 
                    isAnalyzing={isAnalyzing} 
                    analysisResult={analysisResult}
                    onClearAnalysis={() => setAnalysisResult(null)}
                    responseSchema={activeRequest.responseSchema} 
                  />
                </div>
             </div>
          )}

          {view === 'DOCS' && (
            <div className="flex-1 bg-[#0f172a] overflow-y-auto p-12 custom-scrollbar">
               <div className="max-w-4xl mx-auto space-y-8">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-6">
                     <div>
                        <h1 className="text-3xl font-bold text-white mb-2">{selectedDocCollection?.name}</h1>
                        <p className="text-slate-500 text-[10px] uppercase font-black tracking-[0.2em] flex items-center gap-2">
                           <FileText size={14} /> AI Engine Docs
                        </p>
                     </div>
                     <button onClick={() => setView('BUILDER')} className="px-5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-md text-[10px] font-black uppercase tracking-widest transition-all">Return to Workspace</button>
                  </div>
                  
                  {isGeneratingDocs ? (
                    <div className="flex flex-col items-center justify-center py-24 space-y-6">
                       <Loader2 size={64} className="text-orange-500 animate-spin opacity-50" />
                       <div className="text-center">
                          <p className="text-slate-200 font-black text-xs uppercase tracking-[0.3em] mb-2">Analyzing Endpoints</p>
                          <p className="text-slate-500 text-[11px]">Gemini is drafting your documentation structure...</p>
                       </div>
                    </div>
                  ) : (
                    <div className="prose prose-invert max-w-none text-slate-300 font-sans leading-relaxed">
                       <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 whitespace-pre-wrap font-mono text-sm overflow-x-auto shadow-2xl">
                          {selectedDocCollection?.aiDocs || "No documentation content available."}
                       </div>
                    </div>
                  )}
               </div>
            </div>
          )}
        </div>
      </main>

      {/* Floating AI Panel */}
      {isAIOpen ? (
        <AIChatPanel messages={chatMessages} onAddMessage={m => setChatMessages(prev => [...prev, m])} onClear={() => setChatMessages([])} />
      ) : (
        <button 
          onClick={() => setIsAIOpen(true)}
          className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-br from-orange-500 to-orange-700 hover:from-orange-400 hover:to-orange-600 text-white rounded-2xl shadow-[0_10px_40px_rgba(234,88,12,0.3)] flex items-center justify-center transition-all hover:scale-105 active:scale-95 z-50 ring-4 ring-orange-500/10 group"
        >
          <Bot size={28} className="group-hover:rotate-12 transition-transform" />
        </button>
      )}
      
      {isAIOpen && (
        <button onClick={() => setIsAIOpen(false)} className="fixed bottom-[655px] right-6 p-2 bg-slate-800/80 backdrop-blur-md hover:bg-slate-700 text-slate-400 rounded-full z-[100] border border-slate-700 transition-all shadow-lg"><X size={14} /></button>
      )}
    </div>
  );
};

export default App;
