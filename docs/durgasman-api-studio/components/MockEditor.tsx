
import React from 'react';
import { Save, Trash2, X, AlertCircle, ShieldCheck, ShieldAlert, Code } from 'lucide-react';
import { HttpMethod, MockEndpoint } from '../types';

interface MockEditorProps {
  mock: MockEndpoint;
  onUpdate: (updates: Partial<MockEndpoint>) => void;
  onDelete: () => void;
  onClose: () => void;
}

const STATUS_CODES = [
  { code: 200, label: '200 OK' },
  { code: 201, label: '201 Created' },
  { code: 202, label: '202 Accepted' },
  { code: 204, label: '204 No Content' },
  { code: 301, label: '301 Moved Permanently' },
  { code: 302, label: '302 Found' },
  { code: 304, label: '304 Not Modified' },
  { code: 400, label: '400 Bad Request' },
  { code: 401, label: '401 Unauthorized' },
  { code: 403, label: '403 Forbidden' },
  { code: 404, label: '404 Not Found' },
  { code: 405, label: '405 Method Not Allowed' },
  { code: 409, label: '409 Conflict' },
  { code: 422, label: '422 Unprocessable Entity' },
  { code: 429, label: '429 Too Many Requests' },
  { code: 500, label: '500 Internal Server Error' },
  { code: 501, label: '501 Not Implemented' },
  { code: 502, label: '502 Bad Gateway' },
  { code: 503, label: '503 Service Unavailable' },
  { code: 504, label: '504 Gateway Timeout' },
];

const MockEditor: React.FC<MockEditorProps> = ({ mock, onUpdate, onDelete, onClose }) => {
  const [schemaError, setSchemaError] = React.useState<string | null>(null);
  const [isValidating, setIsValidating] = React.useState(false);

  // Simple validation logic without external heavy libraries for now, 
  // checking if both are valid JSON and if schema is reachable.
  const validateAgainstSchema = () => {
    setIsValidating(true);
    setSchemaError(null);
    
    setTimeout(() => {
      try {
        if (!mock.responseSchema?.trim()) {
          setSchemaError("No schema defined.");
          setIsValidating(false);
          return;
        }

        const body = JSON.parse(mock.responseBody);
        const schema = JSON.parse(mock.responseSchema);
        
        // Basic type validation implementation
        if (schema.type === 'object' && typeof body !== 'object') {
          throw new Error("Body is not an object as required by schema.");
        }
        if (schema.required && Array.isArray(schema.required)) {
          for (const field of schema.required) {
            if (!(field in body)) {
              throw new Error(`Missing required field: ${field}`);
            }
          }
        }

        alert("Validation successful! The response body matches the basic constraints of your schema.");
      } catch (err: any) {
        setSchemaError(err.message || "Invalid JSON or Schema mismatch.");
      } finally {
        setIsValidating(false);
      }
    }, 500);
  };

  return (
    <div className="h-full flex flex-col bg-slate-900 border-r border-slate-800">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-blue-500/10 rounded text-blue-400">
            <AlertCircle size={16} />
          </div>
          <h3 className="text-sm font-bold text-slate-200">Mock Configuration</h3>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={onDelete}
            className="p-1.5 text-slate-500 hover:text-red-500 transition-colors"
            title="Delete Mock"
          >
            <Trash2 size={16} />
          </button>
          <button 
            onClick={onClose}
            className="p-1.5 text-slate-500 hover:text-slate-200 transition-colors"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* ENABLE / DISABLE */}
        <div className="flex items-center justify-between bg-slate-800/30 p-3 rounded border border-slate-800">
          <div>
            <p className="text-xs font-bold text-slate-200 uppercase tracking-wider">Active Status</p>
            <p className="text-[10px] text-slate-500">Enable this mock to intercept matching requests</p>
          </div>
          <button 
            onClick={() => onUpdate({ enabled: !mock.enabled })}
            className={`w-12 h-6 rounded-full transition-all relative ${mock.enabled ? 'bg-green-600' : 'bg-slate-700'}`}
          >
            <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${mock.enabled ? 'right-1' : 'left-1'}`} />
          </button>
        </div>

        {/* PATH & METHOD */}
        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-1">
            <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1.5">Method</label>
            <select 
              value={mock.method}
              onChange={(e) => onUpdate({ method: e.target.value as HttpMethod })}
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-orange-400 font-bold outline-none focus:ring-1 focus:ring-blue-500"
            >
              {Object.values(HttpMethod).map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div className="col-span-2">
            <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1.5">Request Path Intercept</label>
            <input 
              type="text"
              value={mock.path}
              onChange={(e) => onUpdate({ path: e.target.value })}
              placeholder="/api/v1/resource"
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-slate-200 outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* STATUS CODE DROPDOWN */}
        <div>
          <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1.5">Response Status Code</label>
          <select 
            value={mock.status}
            onChange={(e) => onUpdate({ status: parseInt(e.target.value) || 200 })}
            className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm text-slate-200 outline-none focus:ring-1 focus:ring-blue-500 font-medium"
          >
            {STATUS_CODES.map(s => (
              <option key={s.code} value={s.code}>{s.label}</option>
            ))}
          </select>
        </div>

        {/* RESPONSE BODY */}
        <div className="flex flex-col h-64">
          <label className="block text-[10px] font-bold text-slate-500 uppercase mb-1.5">Response JSON</label>
          <textarea
            value={mock.responseBody}
            onChange={(e) => onUpdate({ responseBody: e.target.value })}
            className="flex-1 w-full bg-slate-950 border border-slate-800 rounded p-4 text-sm font-mono text-green-400 placeholder-slate-800 focus:ring-1 focus:ring-blue-500 outline-none"
            placeholder='{"status": "success", "data": {}}'
          />
        </div>

        {/* JSON SCHEMA SECTION */}
        <div className="border-t border-slate-800 pt-6">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Code size={14} className="text-indigo-400" />
              <label className="block text-[10px] font-bold text-slate-500 uppercase">Response Schema (Draft-07)</label>
            </div>
            <button 
              onClick={validateAgainstSchema}
              disabled={isValidating}
              className="px-3 py-1 bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 rounded text-[10px] font-bold uppercase transition-all flex items-center gap-1.5"
            >
              {isValidating ? 'Validating...' : (
                <>
                  <ShieldCheck size={12} />
                  Test Validation
                </>
              )}
            </button>
          </div>

          <textarea
            value={mock.responseSchema || ''}
            onChange={(e) => onUpdate({ responseSchema: e.target.value })}
            className="w-full h-48 bg-slate-950 border border-slate-800 rounded p-4 text-sm font-mono text-indigo-300 placeholder-slate-800 focus:ring-1 focus:ring-blue-500 outline-none"
            placeholder='{
  "type": "object",
  "required": ["status"],
  "properties": {
    "status": { "type": "string" }
  }
}'
          />

          {schemaError && (
            <div className="mt-3 p-3 bg-red-900/10 border border-red-500/20 rounded flex items-start gap-3">
              <ShieldAlert size={16} className="text-red-500 shrink-0 mt-0.5" />
              <div>
                <p className="text-[10px] font-bold text-red-500 uppercase">Validation Error</p>
                <p className="text-[11px] text-red-400/80 leading-relaxed">{schemaError}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="p-4 border-t border-slate-800 bg-slate-950/30">
        <button 
          onClick={onClose}
          className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold rounded flex items-center justify-center gap-2 transition-all"
        >
          <Save size={14} />
          Save Mock Definition
        </button>
      </div>
    </div>
  );
};

export default MockEditor;
