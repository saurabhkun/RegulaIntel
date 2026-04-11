import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster, toast } from 'sonner';
import { useNavigate, Link, useLocation } from 'react-router-dom';

export default function Chat() {
  const location = useLocation();
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);

  const fetchSessions = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/chat/sessions");
      const data = await res.json();
      if (data.sessions) setSessions(data.sessions);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchMessages = async (sid) => {
    try {
      const res = await fetch(`http://localhost:8000/api/chat/messages/${sid}`);
      const data = await res.json();
      if (data.messages) {
        setMessages(data.messages);
        setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const createNewSession = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/chat/session", { method: "POST" });
      const data = await res.json();
      if (data.session_id) {
        setCurrentSessionId(data.session_id);
        setMessages([]);
        fetchSessions();
      }
    } catch (e) {
      toast.error("Failed to create session.");
    }
  };

  const loadSession = (sid) => {
    setCurrentSessionId(sid);
    fetchMessages(sid);
  };

  // Auto-create on mount if none selected
  useEffect(() => {
    if (!currentSessionId && sessions.length === 0) {
      createNewSession();
    }
  }, [sessions, currentSessionId]);

  const sendMessage = async () => {
    if (!inputValue.trim()) return;
    
    let sid = currentSessionId;
    if (!sid) {
      // Force create if somehow missing
      const res = await fetch("http://localhost:8000/api/chat/session", { method: "POST" });
      const data = await res.json();
      sid = data.session_id;
      setCurrentSessionId(sid);
    }

    const newMsg = { role: "user", content: inputValue, circular_refs: null };
    setMessages(prev => [...prev, newMsg]);
    setInputValue('');
    setLoading(true);
    setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);

    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sid, message: newMsg.content })
      });
      const data = await res.json();
      
      setMessages(prev => [...prev, { 
        role: "ai", 
        content: data.response, 
        circular_refs: data.circular_refs 
      }]);
      fetchSessions();
    } catch (e) {
      toast.error("Failed to send message");
    } finally {
      setLoading(false);
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    }
  };

  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-50 font-sans selection:bg-indigo-500/30">
      <Toaster position="bottom-right" theme="dark" />
      
      {/* Sidebar - Navigation & History */}
      <aside className="w-72 border-r border-zinc-800 bg-zinc-900/40 flex flex-col py-8">
        <div className="px-6 mb-12">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-zinc-100 rounded-md flex items-center justify-center shadow-sm">
              <span className="material-symbols-outlined text-zinc-900 text-lg font-bold">terminal</span>
            </div>
            <div>
              <h1 className="text-zinc-50 font-bold tracking-tight text-lg leading-tight">RegulaIntel</h1>
              <p className="uppercase tracking-widest text-[10px] text-zinc-500 font-semibold mt-0.5">V.2.0 ACTIVE</p>
            </div>
          </div>
        </div>

        <nav className="px-3 space-y-1.5 mb-8">
          <Link to="/dashboard" className={`flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-200 group ${location.pathname === '/dashboard' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/30'}`}>
            <span className={`material-symbols-outlined text-lg ${location.pathname === '/dashboard' ? 'text-indigo-400' : 'text-zinc-500 group-hover:text-zinc-300'}`}>hub</span>
            <span className="uppercase tracking-widest text-[10px] font-bold">Intelligence Hub</span>
          </Link>
          
          <Link to="/chat" className={`flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-200 group ${location.pathname === '/chat' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/30'}`}>
            <span className={`material-symbols-outlined text-lg ${location.pathname === '/chat' ? 'text-indigo-400' : 'text-zinc-500 group-hover:text-zinc-300'}`}>memory</span>
            <span className="uppercase tracking-widest text-[10px] font-bold">Sentinel Chat</span>
          </Link>

          <Link to="/history" className={`flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-200 group ${location.pathname === '/history' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/30'}`}>
            <span className={`material-symbols-outlined text-lg ${location.pathname === '/history' ? 'text-indigo-400' : 'text-zinc-500 group-hover:text-zinc-300'}`}>timeline</span>
            <span className="uppercase tracking-widest text-[10px] font-bold">Historical Vault</span>
          </Link>
        </nav>

        <div className="px-6 pb-4 flex items-center justify-between border-b border-zinc-800/50 mb-4">
          <h3 className="text-[10px] text-zinc-500 uppercase tracking-widest font-bold">Recent Logic</h3>
          <button onClick={createNewSession} className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-zinc-800 text-zinc-300 font-bold text-[9px] uppercase tracking-widest border border-zinc-700 hover:bg-zinc-700 hover:text-white transition-all">
            <span className="material-symbols-outlined text-[13px]">add</span> New
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {sessions.map(s => (
            <div 
              key={s.session_id} 
              onClick={() => loadSession(s.session_id)}
              className={`p-3 rounded-lg cursor-pointer text-sm font-medium transition-colors ${currentSessionId === s.session_id ? 'bg-zinc-800 text-zinc-100' : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200'}`}
            >
              <div className="line-clamp-1">{s.title}</div>
              <div className="text-[10px] text-zinc-500 mt-1 uppercase tracking-widest">{new Date(s.created_at).toLocaleDateString()}</div>
            </div>
          ))}
        </div>
      </aside>

      {/* Main Chat Interface */}
      <main className="flex-1 flex flex-col relative h-full">
        {/* Header */}
        <header className="h-16 border-b border-zinc-800 flex items-center px-8 bg-zinc-950/80 backdrop-blur-md shrink-0">
          <h2 className="text-xl font-bold tracking-tight text-white flex items-center gap-3">
            <span className="material-symbols-outlined text-indigo-500">memory</span> Sentinel <span className="opacity-40">RAG Engine</span>
          </h2>
        </header>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 flex flex-col gap-6">
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-zinc-600">
              <span className="material-symbols-outlined text-4xl mb-4 opacity-50">smart_toy</span>
              <p className="text-lg font-medium">Hello, RegulaIntel user.</p>
              <p className="text-sm">How can I assist you with regulatory compliance today?</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`flex max-w-3xl w-full ${msg.role === 'user' ? 'ml-auto justify-end' : ''}`}>
                <div className={`p-4 rounded-xl text-[15px] leading-relaxed ${msg.role === 'user' ? 'bg-zinc-800 text-zinc-100 rounded-tr-sm' : 'bg-transparent text-zinc-300'}`}>
                  {msg.content}
                  
                  {/* AI Circular References Tag */}
                  {msg.role === 'ai' && msg.circular_refs && (
                    <div className="mt-4 flex items-center gap-2">
                       <span className="px-2 py-1 bg-indigo-500/10 text-indigo-400 text-[10px] uppercase font-bold tracking-widest rounded flex items-center gap-1 border border-indigo-500/20">
                          <span className="material-symbols-outlined text-[10px]">auto_stories</span>
                          {msg.circular_refs}
                       </span>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="flex max-w-3xl">
              <div className="p-4 text-zinc-500 flex items-center gap-2">
                 <span className="relative flex h-3 w-3"><span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span><span className="relative inline-flex rounded-full h-3 w-3 bg-indigo-500"></span></span>
                 Analyzing regulatory context...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Block */}
        <div className="p-4 border-t border-zinc-800 bg-zinc-950 shrink-0">
          <div className="max-w-4xl mx-auto relative rounded-xl border border-zinc-800 bg-zinc-900 focus-within:border-indigo-500/50 focus-within:ring-1 ring-indigo-500/50 transition-all p-1 flex">
            <input 
              type="text" 
              className="flex-1 bg-transparent border-none text-white px-4 py-3 focus:outline-none text-[15px]" 
              placeholder="Ask anything about Indian financial regulations..." 
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendMessage()}
            />
            <button 
              onClick={sendMessage}
              disabled={loading || !inputValue.trim()}
              className="px-4 bg-white text-black font-semibold rounded-lg m-1 hover:bg-zinc-200 disabled:opacity-50 transition"
            >
              <span className="material-symbols-outlined text-sm pt-1">arrow_upward</span>
            </button>
          </div>
          <div className="text-center mt-3 text-[10px] text-zinc-600 font-semibold uppercase tracking-widest">
            AI can make mistakes. Check important regulatory references.
          </div>
        </div>
      </main>
    </div>
  );
}
