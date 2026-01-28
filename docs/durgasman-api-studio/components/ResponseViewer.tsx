
import React from 'react';
import { ApiResponse, ApiRequest } from '../types';
import { Terminal, Clock, Server, Copy, Check, Sparkles, ShieldCheck, ShieldAlert, ChevronDown, ChevronRight, Brain, Loader2, X } from 'lucide-react';

interface ResponseViewerProps {
  response: ApiResponse | null;
  activeRequest: ApiRequest;
  onAnalyze: () => void;
  isAnalyzing: boolean;
  analysisResult: string | null;
  onClearAnalysis: () => void;
  responseSchema?: string;
}

const ResponseViewer: React.FC<ResponseViewerProps> = ({ 
  response, activeRequest, onAnalyze, isAnalyzing, analysisResult, onClearAnalysis, responseSchema 
}) => {
  const [copied, setCopied] = React.useState(false);
  const [validationResult, setValidationResult] = React.useState<{ valid: boolean; error: string | null } | null>(null);

  React.useEffect(() => {
    if (response && response.data && responseSchema?.trim()) {
      validateResponse(response.data, responseSchema);
    } else {
      setValidationResult(null);
    }
  }, [response, responseSchema]);

  const validateResponse = (data: any, schemaStr: string) => {
    try {
      const schema = JSON.parse(schemaStr);
      
      if (schema.type === 'object' && (typeof data !== 'object' || Array.isArray(data) || data === null)) {
        throw new Error("Expected an object, but received " + (Array.isArray(data) ? "an array" : typeof data));
      }
      if (schema.type === 'array' && !Array.isArray(data)) {
        throw new Error("Expected an array, but received " + typeof data);
      }

      if (schema.required && Array.isArray(schema.required)) {
        for (const field of schema.required) {
          if (!(field in data)) {
            throw new Error(`Missing required field: "${field}"`);
          }
        }
      }

      setValidationResult({ valid: true, error: null });
    } catch (err: any) {
      setValidationResult({ valid: false, error: err.message || "Schema validation failed" });
    }
  };

  const handleCopy = () => {
    if (!response) return;
    navigator.clipboard.writeText(JSON.stringify(response.data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const renderHighlightedJSON = (data: any) => {
    if (data === null || data === undefined) return null;
    
    // Convert to string with indentation
    const jsonString = JSON.stringify(data, null, 2);
    
    // Regular expression for JSON components: strings, numbers, booleans, null
    const regex = /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g;
    
    // Using capturing group in split returns matches in the resulting array
    const parts = jsonString.split(regex);
    
    return parts.map((part, index) => {
      if (part === undefined || part === "") return null;
      
      // The tokens we captured in the regex will be checked for styling
      if (/^"/.test(part)) {
        if (/:$/.test(part)) {
          return <span key={index} className="json-key">{part}</span>;
        } else {
          return <span key={index} className="json-string">{part}</span>;
        }
      } else if (/true|false/.test(part)) {
        return <span key={index} className="json-boolean">{part}</span>;
      } else if (/null/.test(part)) {
        return <span key={index} className="json-null">{part}</span>;
      } else if (/^-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?$/.test(part)) {
        return <span key={index} className="json-number">{part}</span>;
      }
      
      // Return normal text (brackets, braces, whitespace, commas)
      return part;
    });
  };

  if (!response) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-slate-700 bg-[#0a0a0a]">
        <Terminal size={48} className="mb-4 opacity-10" />
        <p className="text-[10px] font-black uppercase tracking-[0.2em]">Ready for request</p>
      </div>
    );
  }

  const isSuccess = response.status >= 200 && response.status < 300;

  return (
    <div className="h-full flex flex-col bg-[#050505] border-l border-slate-800">
      {/* HEADER */}
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between bg-slate-900/10">
        <div className="flex gap-4 items-center">
          <div className="flex items-center gap-1.5">
            <span className={`text-[11px] font-black px-1.5 py-0.5 rounded ${isSuccess ? 'bg-emerald-500/10 text-emerald-500' : 'bg-rose-500/10 text-rose-500'}`}>
              {response.status} {response.statusText}
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500">
            <Clock size={12} />
            <span>{response.time} ms</span>
          </div>
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500">
            <Server size={12} />
            <span>{response.size}</span>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <button 
            onClick={onAnalyze}
            disabled={isAnalyzing}
            className="flex items-center gap-2 px-3 py-1.5 bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 border border-indigo-500/20 rounded-md text-[10px] font-black uppercase tracking-wider transition-all"
          >
            {isAnalyzing ? <Loader2 size={12} className="animate-spin" /> : <Brain size={12} />}
            {isAnalyzing ? 'Thinking...' : 'AI Analyze'}
          </button>
          <button 
            onClick={handleCopy}
            className="p-1.5 text-slate-500 hover:text-slate-300 transition-colors"
          >
            {copied ? <Check size={16} className="text-emerald-500" /> : <Copy size={16} />}
          </button>
        </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* AI ANALYSIS SECTION */}
        {analysisResult && (
          <div className="bg-indigo-600/5 border-b border-indigo-500/20 p-4 relative animate-in fade-in slide-in-from-top-2 duration-300">
             <button onClick={onClearAnalysis} className="absolute top-2 right-2 text-indigo-500 hover:text-indigo-400"><X size={14} /></button>
             <div className="flex items-start gap-3">
                <div className="mt-1 p-1.5 bg-indigo-500/20 rounded text-indigo-400"><Brain size={16} /></div>
                <div className="flex-1 min-w-0">
                   <h4 className="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-1">AI Response Insight</h4>
                   <div className="text-xs text-slate-300 prose prose-invert max-w-none prose-sm leading-relaxed whitespace-pre-wrap">
                      {analysisResult}
                   </div>
                </div>
             </div>
          </div>
        )}

        {/* VALIDATION ALERT */}
        {validationResult && (
          <div className={`px-4 py-2 border-b border-slate-800 flex items-center justify-between ${validationResult.valid ? 'bg-emerald-500/5' : 'bg-rose-500/5'}`}>
              <div className="flex items-center gap-2">
                {validationResult.valid ? (
                  <ShieldCheck size={14} className="text-emerald-500" />
                ) : (
                  <ShieldAlert size={14} className="text-rose-500" />
                )}
                <span className={`text-[9px] font-black uppercase tracking-[0.1em] ${validationResult.valid ? 'text-emerald-500' : 'text-rose-500'}`}>
                  Schema: {validationResult.valid ? 'Valid' : 'Invalid'}
                </span>
                {!validationResult.valid && <span className="text-[10px] text-rose-400/80 italic font-medium truncate max-w-[200px]">{validationResult.error}</span>}
              </div>
          </div>
        )}

        {/* CONTENT */}
        <div className="flex-1 overflow-y-auto p-4 font-mono text-sm custom-scrollbar bg-[#050505]">
          {response.error ? (
            <div className="text-rose-500 bg-rose-500/5 p-4 rounded border border-rose-500/20 flex flex-col gap-2">
              <span className="text-[10px] font-black uppercase tracking-widest opacity-60">Request Failure</span>
              <pre className="whitespace-pre-wrap">{response.error}</pre>
            </div>
          ) : (
            <pre className="text-slate-400 whitespace-pre-wrap leading-relaxed">
              {typeof response.data === 'string' ? response.data : renderHighlightedJSON(response.data)}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResponseViewer;
