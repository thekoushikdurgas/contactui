
import React from 'react';
import { Send, Save, Plus, Trash2, AlertCircle, Wand2, Loader2, X, Code, Mic, MicOff, Check, ArrowRight, Lightbulb, Info } from 'lucide-react';
import { HttpMethod, ApiRequest, KeyValue } from '../types';
import { generateRequestFromPrompt } from '../services/geminiService';

interface RequestBuilderProps {
  request: ApiRequest;
  onUpdate: (updates: Partial<ApiRequest>) => void;
  onSend: () => void;
  onSave: () => void;
  isSending: boolean;
  isDirty?: boolean;
}

const RequestBuilder: React.FC<RequestBuilderProps> = ({ request, onUpdate, onSend, onSave, isSending, isDirty }) => {
  const [activeTab, setActiveTab] = React.useState('params');
  const [isMagicOpen, setIsMagicOpen] = React.useState(false);
  const [magicPrompt, setMagicPrompt] = React.useState('');
  const [magicSchema, setMagicSchema] = React.useState('');
  const [isMagicGenerating, setIsMagicGenerating] = React.useState(false);
  const [pendingRequest, setPendingRequest] = React.useState<Partial<ApiRequest> | null>(null);

  // Voice Command States
  const [isListening, setIsListening] = React.useState(false);
  const [lastCommand, setLastCommand] = React.useState<string | null>(null);
  const recognitionRef = React.useRef<any>(null);

  const handleMagicGenerate = async () => {
    if (!magicPrompt.trim()) return;
    setIsMagicGenerating(true);
    const result = await generateRequestFromPrompt(magicPrompt, magicSchema);
    if (result) {
      setPendingRequest(result);
    } else {
      alert("AI failed to generate a valid request. Try again!");
    }
    setIsMagicGenerating(false);
  };

  const handleConfirmPending = () => {
    if (pendingRequest) {
      onUpdate(pendingRequest);
      setPendingRequest(null);
      setIsMagicOpen(false);
      setMagicPrompt('');
      setMagicSchema('');
    }
  };

  const handleDiscardPending = () => {
    setPendingRequest(null);
  };

  // Voice recognition logic
  const toggleVoiceControl = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);

    recognition.onresult = (event: any) => {
      const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase().trim();
      
      if (transcript.includes('send request')) {
        setLastCommand('Sending...');
        onSend();
        setTimeout(() => setLastCommand(null), 2000);
      } else if (transcript.includes('save request')) {
        setLastCommand('Saving...');
        onSave();
        setTimeout(() => setLastCommand(null), 2000);
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const updateKV = (type: 'params' | 'headers', id: string, field: keyof KeyValue, value: any) => {
    const list = [...request[type]];
    const index = list.findIndex(item => item.id === id);
    if (index !== -1) {
      list[index] = { ...list[index], [field]: value };
      onUpdate({ [type]: list });
    }
  };

  const addKV = (type: 'params' | 'headers') => {
    const newItem: KeyValue = { id: Math.random().toString(36).substr(2, 9), key: '', value: '', enabled: true };
    onUpdate({ [type]: [...request[type], newItem] });
  };

  const removeKV = (type: 'params' | 'headers', id: string) => {
    onUpdate({ [type]: request[type].filter(item => item.id !== id) });
  };

  const tabs = [
    { id: 'params', name: 'Params' },
    { id: 'auth', name: 'Auth' },
    { id: 'headers', name: 'Headers' },
    { id: 'body', name: 'Body' },
    { id: 'schema', name: 'Schema' },
    { id: 'pre-request', name: 'Pre-request' },
    { id: 'tests', name: 'Tests' },
  ];

  return (
    <div className="flex flex-col h-full bg-slate-900 border-r border-slate-800">
      {/* REQUEST INFO BAR */}
      <div className="px-4 py-2 border-b border-slate-800 bg-slate-950/20 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Active Request:</span>
          <span className="text-xs font-semibold text-slate-200">{request.name}</span>
          {isDirty && (
            <div className="flex items-center gap-1.5 px-2 py-0.5 bg-orange-500/10 border border-orange-500/20 rounded text-[10px] font-bold text-orange-500 animate-pulse">
              <AlertCircle size={10} /> MODIFIED
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* Voice Control Toggle */}
          <div className="flex items-center gap-2">
            {lastCommand && (
              <span className="text-[10px] font-bold text-indigo-400 animate-bounce">{lastCommand}</span>
            )}
            <button 
              onClick={toggleVoiceControl}
              className={`flex items-center gap-2 px-3 py-1 rounded-full text-[10px] font-bold transition-all ${
                isListening 
                  ? 'bg-red-500/10 text-red-500 border border-red-500/20 animate-pulse' 
                  : 'bg-slate-800 text-slate-400 border border-slate-700 hover:text-white'
              }`}
              title="Voice Commands: Say 'Send Request' or 'Save Request'"
            >
              {isListening ? <Mic size={12} className="text-red-500" /> : <MicOff size={12} />}
              {isListening ? 'LISTENING' : 'VOICE OFF'}
            </button>
          </div>

          <button 
            onClick={() => setIsMagicOpen(true)}
            className="flex items-center gap-2 px-3 py-1 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-full text-[10px] font-bold shadow-lg shadow-indigo-500/20 transition-all hover:scale-105"
          >
            <Wand2 size={12} />
            AI MAGIC GENERATE
          </button>
        </div>
      </div>

      {/* URL BAR */}
      <div className="p-4 border-b border-slate-800 flex gap-2">
        <select 
          value={request.method}
          onChange={(e) => onUpdate({ method: e.target.value as HttpMethod })}
          className="bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm font-bold text-orange-400 outline-none focus:ring-1 focus:ring-blue-500"
        >
          {Object.values(HttpMethod).map(m => <option key={m} value={m}>{m}</option>)}
        </select>
        <input 
          type="text"
          value={request.url}
          onChange={(e) => onUpdate({ url: e.target.value })}
          placeholder="https://api.example.com/v1/resource"
          className="flex-1 bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-slate-200 placeholder-slate-500 outline-none focus:ring-1 focus:ring-blue-500"
        />
        <button 
          onClick={onSend}
          disabled={isSending}
          className={`bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-medium px-6 py-2 rounded flex items-center gap-2 transition-all shadow-lg ${
            lastCommand === 'Sending...' ? 'ring-4 ring-blue-500/50 scale-105' : ''
          }`}
        >
          <Send size={16} />
          {isSending ? 'Sending...' : 'Send'}
        </button>
        <button 
          onClick={onSave}
          className={`px-4 py-2 rounded flex items-center gap-2 transition-all border ${
            isDirty 
              ? 'bg-orange-600/10 hover:bg-orange-600/20 text-orange-500 border-orange-500/30 shadow-[0_0_15px_rgba(249,115,22,0.1)]' 
              : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
          } ${lastCommand === 'Saving...' ? 'ring-4 ring-orange-500/50 scale-105' : ''}`}
        >
          <Save size={16} />
          Save
        </button>
      </div>

      {/* TABS HEADER */}
      <div className="flex border-b border-slate-800 bg-slate-900/50">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-5 py-3 text-xs font-medium border-b-2 transition-colors ${
              activeTab === tab.id ? 'border-orange-500 text-orange-500' : 'border-transparent text-slate-500 hover:text-slate-300'
            }`}
          >
            {tab.name}
          </button>
        ))}
      </div>

      {/* TABS CONTENT */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'params' && (
          <KVEditor items={request.params} onUpdate={(id, k, v) => updateKV('params', id, k, v)} onAdd={() => addKV('params')} onRemove={(id) => removeKV('params', id)} title="Query Parameters" />
        )}
        {activeTab === 'headers' && (
          <KVEditor items={request.headers} onUpdate={(id, k, v) => updateKV('headers', id, k, v)} onAdd={() => addKV('headers')} onRemove={(id) => removeKV('headers', id)} title="Headers" />
        )}
        {activeTab === 'body' && (
          <div className="h-full flex flex-col">
            <div className="flex gap-4 mb-3 text-xs text-slate-500">
              <label className="flex items-center gap-1 cursor-pointer"><input type="radio" checked readOnly /> raw (JSON)</label>
            </div>
            <textarea
              value={request.body}
              onChange={(e) => onUpdate({ body: e.target.value })}
              className="flex-1 w-full bg-slate-900 border border-slate-800 rounded p-4 text-sm font-mono text-blue-300 placeholder-slate-700 focus:ring-1 focus:ring-blue-500 outline-none min-h-[300px]"
              placeholder='{"key": "value"}'
            />
          </div>
        )}
        {activeTab === 'schema' && (
          <div className="h-full flex flex-col">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Expected Response Schema</h3>
            </div>
            <textarea
              value={request.responseSchema || ''}
              onChange={(e) => onUpdate({ responseSchema: e.target.value })}
              className="flex-1 w-full bg-slate-950 border border-slate-800 rounded p-4 text-sm font-mono text-indigo-300 placeholder-slate-800 focus:ring-1 focus:ring-blue-500 outline-none min-h-[300px]"
              placeholder='{ "type": "object", ... }'
            />
          </div>
        )}
        {['auth', 'pre-request', 'tests'].includes(activeTab) && (
          <div className="flex flex-col items-center justify-center h-full text-slate-600 opacity-50">
            <Plus size={48} className="mb-2" />
            <p className="text-sm">Tab "{activeTab}" config goes here</p>
          </div>
        )}
      </div>

      {/* MAGIC GENERATOR MODAL */}
      {isMagicOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-[100] p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden ring-1 ring-white/10">
            
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-indigo-600/10">
              <div className="flex items-center gap-2">
                <Wand2 size={20} className="text-indigo-400" />
                <h3 className="font-bold text-sm text-slate-200 uppercase tracking-widest">
                  {pendingRequest ? 'Analyze Generated Request' : 'AI Request Builder'}
                </h3>
              </div>
              <button 
                onClick={() => {
                  setIsMagicOpen(false);
                  setPendingRequest(null);
                }} 
                className="text-slate-500 hover:text-white"
              >
                <X size={20} />
              </button>
            </div>

            <div className="p-6">
              {!pendingRequest ? (
                /* Input Phase */
                <div className="space-y-4">
                  <div>
                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Request Description</label>
                    <textarea 
                      value={magicPrompt}
                      onChange={(e) => setMagicPrompt(e.target.value)}
                      autoFocus
                      placeholder="Describe what kind of API request you want to create (e.g. 'A POST request to update user profile')..."
                      className="w-full h-24 bg-slate-950 border border-slate-800 rounded-lg p-4 text-sm text-white focus:ring-2 focus:ring-indigo-500 outline-none resize-none transition-all"
                    />
                  </div>

                  <div>
                    <label className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">
                      <Code size={12} className="text-indigo-400" />
                      Response Schema Requirements (Optional)
                    </label>
                    <textarea 
                      value={magicSchema}
                      onChange={(e) => setMagicSchema(e.target.value)}
                      placeholder="e.g. 'Must return a list of products with id, name, and price fields'..."
                      className="w-full h-24 bg-slate-950 border border-slate-800 rounded-lg p-4 text-sm text-white focus:ring-2 focus:ring-indigo-500 outline-none resize-none transition-all"
                    />
                  </div>

                  <button 
                    onClick={handleMagicGenerate}
                    disabled={isMagicGenerating || !magicPrompt.trim()}
                    className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold rounded-lg flex items-center justify-center gap-2 transition-all shadow-lg active:scale-95"
                  >
                    {isMagicGenerating ? <Loader2 size={18} className="animate-spin" /> : <Wand2 size={18} />}
                    {isMagicGenerating ? 'Gemini is Thinking...' : 'Generate Definition'}
                  </button>
                </div>
              ) : (
                /* Review Phase */
                <div className="space-y-6">
                  <div className="p-4 bg-indigo-500/5 border border-indigo-500/20 rounded-lg">
                    <div className="flex items-start gap-3 mb-4">
                       <div className="p-2 bg-indigo-500/20 rounded-full text-indigo-400">
                          <Lightbulb size={18} />
                       </div>
                       <div>
                          <h4 className="text-xs font-bold text-slate-200">Review generated definition</h4>
                          <p className="text-[11px] text-slate-500">Gemini has parsed your prompt into a structured API request. Learn and verify the details below.</p>
                       </div>
                    </div>

                    <div className="space-y-4">
                      {/* Name & URL */}
                      <div className="grid grid-cols-12 gap-3 items-center">
                        <div className="col-span-2">
                          <span className={`w-full py-1 text-center block rounded font-bold text-[11px] ${getMethodColor(pendingRequest.method || 'GET')} bg-slate-950 border border-slate-800`}>
                            {pendingRequest.method}
                          </span>
                        </div>
                        <div className="col-span-10">
                          <div className="bg-slate-950 border border-slate-800 rounded px-3 py-1 text-xs text-blue-400 font-mono truncate">
                            {pendingRequest.url}
                          </div>
                        </div>
                      </div>

                      {/* Summary Data */}
                      <div className="grid grid-cols-3 gap-3">
                         <div className="bg-slate-950 border border-slate-800 p-2 rounded">
                            <span className="block text-[9px] text-slate-600 uppercase font-bold mb-1">Params</span>
                            <span className="text-xs text-slate-300">{(pendingRequest.params || []).length} defined</span>
                         </div>
                         <div className="bg-slate-950 border border-slate-800 p-2 rounded">
                            <span className="block text-[9px] text-slate-600 uppercase font-bold mb-1">Headers</span>
                            <span className="text-xs text-slate-300">{(pendingRequest.headers || []).length} defined</span>
                         </div>
                         <div className="bg-slate-950 border border-slate-800 p-2 rounded">
                            <span className="block text-[9px] text-slate-600 uppercase font-bold mb-1">Has Body</span>
                            <span className="text-xs text-slate-300">{pendingRequest.body ? 'Yes' : 'No'}</span>
                         </div>
                      </div>

                      {/* Schema Preview */}
                      {pendingRequest.responseSchema && (
                        <div className="space-y-1.5">
                          <label className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                            <Info size={10} /> Generated Response Schema
                          </label>
                          <div className="bg-slate-950 border border-slate-800 rounded p-3 text-[10px] font-mono text-indigo-300 max-h-32 overflow-y-auto whitespace-pre-wrap">
                            {pendingRequest.responseSchema}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <button 
                      onClick={handleDiscardPending}
                      className="flex-1 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold rounded-lg flex items-center justify-center gap-2 transition-all border border-slate-700"
                    >
                      Discard & Retry
                    </button>
                    <button 
                      onClick={handleConfirmPending}
                      className="flex-[2] py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-lg flex items-center justify-center gap-2 transition-all shadow-lg active:scale-95"
                    >
                      <Check size={18} />
                      Confirm & Apply
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const KVEditor: React.FC<{ items: KeyValue[], onUpdate: (id: string, field: keyof KeyValue, value: any) => void, onAdd: () => void, onRemove: (id: string) => void, title: string }> = ({ items, onUpdate, onAdd, onRemove, title }) => (
  <div className="flex flex-col gap-2">
    <div className="flex items-center justify-between mb-2">
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{title}</h3>
      <button onClick={onAdd} className="text-blue-500 hover:text-blue-400 text-xs flex items-center gap-1"><Plus size={14} /> Add New</button>
    </div>
    <div className="border border-slate-800 rounded overflow-hidden">
      <table className="w-full text-left text-xs">
        <thead className="bg-slate-800/50 text-slate-400">
          <tr>
            <th className="px-3 py-2 w-10"></th>
            <th className="px-3 py-2 border-l border-slate-800">Key</th>
            <th className="px-3 py-2 border-l border-slate-800">Value</th>
            <th className="px-3 py-2 border-l border-slate-800 w-10"></th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {items.map(item => (
            <tr key={item.id} className="hover:bg-slate-800/30">
              <td className="px-3 py-1">
                <input type="checkbox" checked={item.enabled} onChange={(e) => onUpdate(item.id, 'enabled', e.target.checked)} />
              </td>
              <td className="border-l border-slate-800">
                <input type="text" value={item.key} onChange={(e) => onUpdate(item.id, 'key', e.target.value)} className="w-full bg-transparent px-3 py-2 text-slate-300 outline-none" placeholder="Key" />
              </td>
              <td className="border-l border-slate-800">
                <input type="text" value={item.value} onChange={(e) => onUpdate(item.id, 'value', e.target.value)} className="w-full bg-transparent px-3 py-2 text-slate-300 outline-none" placeholder="Value" />
              </td>
              <td className="px-3 py-1 text-center">
                <button onClick={() => onRemove(item.id)} className="text-slate-600 hover:text-red-500 transition-colors"><Trash2 size={14} /></button>
              </td>
            </tr>
          ))}
          {items.length === 0 && (
            <tr>
              <td colSpan={4} className="px-3 py-8 text-center text-slate-600 italic">No items defined</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  </div>
);

function getMethodColor(method: string) {
  switch (method) {
    case 'GET': return 'text-green-500';
    case 'POST': return 'text-orange-400';
    case 'PUT': return 'text-blue-400';
    case 'PATCH': return 'text-purple-400';
    case 'DELETE': return 'text-red-500';
    default: return 'text-slate-400';
  }
}

export default RequestBuilder;
