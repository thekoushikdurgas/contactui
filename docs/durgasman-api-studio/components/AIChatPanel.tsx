
import React from 'react';
import { Send, Bot, User, Sparkles, Brain, Search, ExternalLink, Mic, X, Radio, Image as ImageIcon, Download, Loader2 } from 'lucide-react';
import { chatWithGemini, speak, connectLive, createPcmBlob, decode, decodeAudioData, generateImage } from '../services/geminiService';
import { ChatMessage } from '../types';

interface AIChatPanelProps {
  messages: ChatMessage[];
  onAddMessage: (msg: ChatMessage) => void;
  onClear: () => void;
}

const AIChatPanel: React.FC<AIChatPanelProps> = ({ messages, onAddMessage, onClear }) => {
  const [activeTab, setActiveTab] = React.useState<'chat' | 'images'>('chat');
  const [input, setInput] = React.useState('');
  const [isLoading, setIsLoading] = React.useState(false);
  const [useThinking, setUseThinking] = React.useState(false);
  const [useSearch, setUseSearch] = React.useState(false);
  const [isVoiceFeedback, setIsVoiceFeedback] = React.useState(false);
  const [isLiveMode, setIsLiveMode] = React.useState(false);
  
  // Image Generation States
  const [imagePrompt, setImagePrompt] = React.useState('');
  const [generatedImages, setGeneratedImages] = React.useState<string[]>([]);
  const [isGeneratingImage, setIsGeneratingImage] = React.useState(false);

  const scrollRef = React.useRef<HTMLDivElement>(null);
  const liveSessionRef = React.useRef<any>(null);
  const audioContextsRef = React.useRef<{ input: AudioContext; output: AudioContext } | null>(null);

  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, generatedImages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMsg: ChatMessage = { role: 'user', text: input, timestamp: Date.now() };
    onAddMessage(userMsg);
    setInput('');
    setIsLoading(true);

    try {
      const response = await chatWithGemini(input, messages, { 
        thinking: useThinking, 
        search: useSearch 
      });
      
      const botMsg: ChatMessage = { 
        role: 'model', 
        text: response.text, 
        timestamp: Date.now(),
        groundingUrls: response.groundingUrls
      };
      onAddMessage(botMsg);
      
      if (isVoiceFeedback) {
        speak(response.text);
      }
    } catch (err) {
      console.error(err);
      onAddMessage({ role: 'model', text: "Sorry, I encountered an error processing that request.", timestamp: Date.now() });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateImage = async () => {
    if (!imagePrompt.trim()) return;
    setIsGeneratingImage(true);
    try {
      const imgUrl = await generateImage(imagePrompt);
      if (imgUrl) {
        setGeneratedImages(prev => [imgUrl, ...prev]);
        setImagePrompt('');
      }
    } catch (e) {
      alert("Failed to generate image. Please check your Gemini settings.");
    } finally {
      setIsGeneratingImage(false);
    }
  };

  const toggleLiveMode = async () => {
    if (isLiveMode) {
      if (liveSessionRef.current) liveSessionRef.current.close();
      if (audioContextsRef.current) {
        audioContextsRef.current.input.close();
        audioContextsRef.current.output.close();
      }
      setIsLiveMode(false);
      return;
    }

    try {
      const inputAudioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
      const outputAudioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
      audioContextsRef.current = { input: inputAudioContext, output: outputAudioContext };

      let nextStartTime = 0;
      const sources = new Set<AudioBufferSourceNode>();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const sessionPromise = connectLive({
        onopen: () => {
          const source = inputAudioContext.createMediaStreamSource(stream);
          const scriptProcessor = inputAudioContext.createScriptProcessor(4096, 1, 1);
          scriptProcessor.onaudioprocess = (event) => {
            const inputData = event.inputBuffer.getChannelData(0);
            const pcmBlob = createPcmBlob(inputData);
            sessionPromise.then((session: any) => {
              session.sendRealtimeInput({ media: pcmBlob });
            });
          };
          source.connect(scriptProcessor);
          scriptProcessor.connect(inputAudioContext.destination);
          onAddMessage({ role: 'model', text: "[Live Connection Established]", timestamp: Date.now() });
        },
        onmessage: async (message: any) => {
          const base64Audio = message.serverContent?.modelTurn?.parts[0]?.inlineData?.data;
          if (base64Audio) {
            nextStartTime = Math.max(nextStartTime, outputAudioContext.currentTime);
            const audioBuffer = await decodeAudioData(decode(base64Audio), outputAudioContext, 24000, 1);
            const source = outputAudioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(outputAudioContext.destination);
            source.addEventListener('ended', () => sources.delete(source));
            source.start(nextStartTime);
            nextStartTime += audioBuffer.duration;
            sources.add(source);
          }
          if (message.serverContent?.interrupted) {
            sources.forEach(s => s.stop());
            sources.clear();
            nextStartTime = 0;
          }
        },
        onclose: () => {
          setIsLiveMode(false);
          onAddMessage({ role: 'model', text: "[Live Connection Closed]", timestamp: Date.now() });
        },
        onerror: (e: any) => {
          console.error("Live Error", e);
          setIsLiveMode(false);
        }
      });

      liveSessionRef.current = await sessionPromise;
      setIsLiveMode(true);
    } catch (err) {
      console.error("Failed to start live mode", err);
      alert("Microphone access is required for live mode.");
    }
  };

  return (
    <div className="fixed bottom-6 right-6 w-96 h-[640px] bg-slate-900 border border-slate-800 rounded-xl shadow-2xl flex flex-col z-50 overflow-hidden ring-1 ring-white/10">
      {/* HEADER */}
      <div className="p-4 bg-slate-800 border-b border-slate-700 flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${isLiveMode ? 'bg-red-600 animate-pulse' : 'bg-indigo-600'}`}>
              {isLiveMode ? <Radio size={18} className="text-white" /> : <Bot size={18} className="text-white" />}
            </div>
            <div>
              <h3 className="text-sm font-bold text-white leading-none">
                {isLiveMode ? 'Durgasman LIVE' : (activeTab === 'chat' ? 'Durgasman AI' : 'Image Studio')}
              </h3>
              <span className="text-[10px] text-green-400 uppercase tracking-widest font-bold">
                {isLiveMode ? 'Voice Active' : 'Online Assistant'}
              </span>
            </div>
          </div>
          <div className="flex gap-1">
              <button 
                  onClick={toggleLiveMode}
                  className={`p-1.5 rounded transition-colors ${isLiveMode ? 'bg-red-600 text-white' : 'hover:bg-slate-700 text-slate-400'}`}
                  title="Toggle Real-time Voice"
              >
                  <Mic size={16} />
              </button>
              <button 
                  onClick={() => setUseThinking(!useThinking)}
                  className={`p-1.5 rounded transition-colors ${useThinking ? 'bg-indigo-600 text-white' : 'hover:bg-slate-700 text-slate-400'}`}
                  title="Thinking Mode"
              >
                  <Brain size={16} />
              </button>
              <button 
                  onClick={() => setUseSearch(!useSearch)}
                  className={`p-1.5 rounded transition-colors ${useSearch ? 'bg-blue-600 text-white' : 'hover:bg-slate-700 text-slate-400'}`}
                  title="Search Grounding"
              >
                  <Search size={16} />
              </button>
          </div>
        </div>
        <div className="flex bg-slate-950/50 p-1 rounded-lg">
          <button 
            onClick={() => setActiveTab('chat')}
            className={`flex-1 flex items-center justify-center gap-2 py-1.5 text-[10px] font-bold uppercase rounded-md transition-all ${activeTab === 'chat' ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}
          >
            <Bot size={12} /> Chat
          </button>
          <button 
            onClick={() => setActiveTab('images')}
            className={`flex-1 flex items-center justify-center gap-2 py-1.5 text-[10px] font-bold uppercase rounded-md transition-all ${activeTab === 'images' ? 'bg-slate-800 text-white shadow-sm' : 'text-slate-500 hover:text-slate-300'}`}
          >
            <ImageIcon size={12} /> Visuals
          </button>
        </div>
      </div>

      {/* CONTENT AREA */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-900/50">
        {activeTab === 'chat' ? (
          <>
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 mt-10">
                <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center mb-4">
                  <Sparkles size={32} className="text-indigo-400" />
                </div>
                <h4 className="text-slate-200 font-semibold mb-2">Power up your API workflow</h4>
                <p className="text-xs text-slate-500">Ask for code snippets, debug response errors, or generate mock data structures.</p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-lg p-3 text-sm shadow-sm ${
                  msg.role === 'user' 
                    ? 'bg-indigo-600 text-white' 
                    : 'bg-slate-800 text-slate-200 border border-slate-700'
                }`}>
                  <div className="whitespace-pre-wrap font-sans">{msg.text}</div>
                  {msg.groundingUrls && msg.groundingUrls.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-slate-700 space-y-1">
                      <p className="text-[10px] text-slate-500 uppercase font-bold">Sources:</p>
                      {msg.groundingUrls.map((url, idx) => (
                        <a key={idx} href={url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-[10px] text-blue-400 hover:underline">
                          <ExternalLink size={10} /> {new URL(url).hostname}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </>
        ) : (
          <div className="space-y-4">
            <div className="p-4 bg-indigo-600/10 border border-indigo-500/20 rounded-lg">
              <p className="text-xs text-indigo-300 font-medium mb-2">Generate diagrams or documentation assets</p>
              <div className="flex gap-2">
                <input 
                  type="text"
                  value={imagePrompt}
                  onChange={(e) => setImagePrompt(e.target.value)}
                  placeholder="e.g. A high-tech API architecture diagram..."
                  className="flex-1 bg-slate-950 border border-slate-700 rounded-md px-3 py-1.5 text-xs text-white outline-none focus:ring-1 focus:ring-indigo-500"
                />
                <button 
                  onClick={handleGenerateImage}
                  disabled={isGeneratingImage || !imagePrompt.trim()}
                  className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 p-2 rounded-md text-white transition-all"
                >
                  {isGeneratingImage ? <Loader2 size={16} className="animate-spin" /> : <ImageIcon size={16} />}
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {generatedImages.map((img, idx) => (
                <div key={idx} className="relative group rounded-lg overflow-hidden border border-slate-800 aspect-square">
                  <img src={img} alt="Generated" className="w-full h-full object-cover" />
                  <div className="absolute inset-0 bg-slate-950/60 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity">
                    <a href={img} download={`api-asset-${idx}.png`} className="p-2 bg-indigo-600 rounded-full text-white">
                      <Download size={16} />
                    </a>
                  </div>
                </div>
              ))}
              {generatedImages.length === 0 && !isGeneratingImage && (
                <div className="col-span-2 py-20 text-center text-slate-600">
                  <ImageIcon size={48} className="mx-auto mb-4 opacity-10" />
                  <p className="text-xs">No images generated yet.</p>
                </div>
              )}
            </div>
          </div>
        )}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 flex gap-1">
              <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        )}
      </div>

      {/* INPUT BAR (CHAT ONLY) */}
      {!isLiveMode && activeTab === 'chat' && (
        <div className="p-4 border-t border-slate-800 bg-slate-800/30">
            <div className="relative">
            <input 
                type="text" 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask Durgasman AI..."
                className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-4 pr-12 py-3 text-sm text-white focus:ring-1 focus:ring-indigo-500 outline-none"
            />
            <button 
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-indigo-500 hover:text-indigo-400 disabled:opacity-30 transition-colors"
            >
                <Send size={18} />
            </button>
            </div>
        </div>
      )}
      
      {isLiveMode && (
        <div className="p-6 border-t border-slate-800 bg-slate-900 text-center">
            <div className="inline-flex items-center gap-3 px-4 py-2 bg-red-600/10 border border-red-500/20 rounded-full text-red-500 text-xs font-bold uppercase tracking-widest animate-pulse">
                <Radio size={14} /> Recording Live
            </div>
        </div>
      )}
    </div>
  );
};

export default AIChatPanel;
