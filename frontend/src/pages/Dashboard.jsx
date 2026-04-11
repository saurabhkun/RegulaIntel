import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster, toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../utils/supabaseClient';
import { Link, useLocation } from 'react-router-dom';

export default function Dashboard() {
  const location = useLocation();
  const [oldFile, setOldFile] = useState(null);
  const [newFile, setNewFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [tracking, setTracking] = useState(false);
  const [trackResult, setTrackResult] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [showProfile, setShowProfile] = useState(false);
  const [autoScrape, setAutoScrape] = useState(false);
  const [highContrast, setHighContrast] = useState(false);
  const [audibleAlerts, setAudibleAlerts] = useState(true);
  const { user, signOut } = useAuth();

  const clean = (text) => {
    if (!text) return "";
    return text.replace(/[#*`_~]/g, '').replace(/\s+/g, ' ').trim();
  };

  const [sources, setSources] = useState([
    { name: "RBI", full: "Reserve Bank of India", live: false },
    { name: "SEBI", full: "Securities & Exchange Board", live: false },
    { name: "MCA", full: "Ministry of Corporate Affairs", live: false },
    { name: "IRDAI", full: "Insurance Regulatory Auth.", live: false },
  ]);

  useEffect(() => {
    // Simulate real-time node connection pinging on dashboard boot
    const pingDelays = [800, 1600, 2900, 3500]; // ms
    const finalStates = [true, true, false, true]; // Sets 3/4 to true for 75% Integrity

    pingDelays.forEach((delay, idx) => {
      setTimeout(() => {
        setSources(prev => {
          const next = [...prev];
          next[idx].live = finalStates[idx];
          return next;
        });
      }, delay);
    });
  }, []);

  const getHeaders = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return {
      'Authorization': `Bearer ${session?.access_token}`
    };
  };

  const handleAnalyze = async () => {
    if (!oldFile || !newFile) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("old_pdf", oldFile);
      formData.append("new_pdf", newFile);
      
      const headers = await getHeaders();
      const res = await fetch("http://localhost:8000/api/analyze", {
        method: "POST",
        headers: headers,
        body: formData
      });
      
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.message || "Backend error");
      }

      const data = await res.json();
      setResults(data);
      setSelectedIdx(0);
      toast.success("Analysis complete! 🧠");
    } catch (e) {
      toast.error("Failed to analyze: " + e.message);
    }
    setLoading(false);
  };

  const triggerScraper = async () => {
    setTracking(true);
    setTrackResult(null);
    try {
      const headers = await getHeaders();
      const res = await fetch("http://localhost:8000/api/monitor/check-once/live", {
        headers: headers
      });
      if (!res.ok) throw new Error("Scraper service unavailable");
      const data = await res.json();
      setTrackResult(data);
      toast.success("Live Scrape successful!");
    } catch(e) {
      toast.error("Scraper Error: " + e.message);
    }
    setTracking(false);
  };

  const analyzeLive = async () => {
    setLoading(true);
    setResults(null);
    try {
      const headers = await getHeaders();
      const res = await fetch("http://localhost:8000/api/analyze/live", { 
        method: "POST",
        headers: headers
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.message || "Live analysis failed");
      }
      const data = await res.json();
      if(data.message) {
        toast.error(data.message);
      } else {
        setResults(data);
        setSelectedIdx(0);
        toast.success("Live intercept analyzed!");
      }
    } catch (e) {
      toast.error("Network Error: " + e.message);
    }
    setLoading(false);
  };

  const downloadReport = async () => {
    if (!results) {
      toast.error("No results to download");
      return;
    }
    try {
      const headers = await getHeaders();
      const res = await fetch("http://localhost:8000/api/report", {
        method: "POST",
        headers: { 
          ...headers,
          'Content-Type': 'application/json' 
        },
        body: JSON.stringify(results)
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.message || "Failed to generate report");
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = "RegulaIntel_Report.pdf";
      a.click();
      toast.success("Professional Audit exported!");
    } catch (e) {
      toast.error("Failed to download PDF: " + e.message);
    }
  };

  const handleLogout = async () => {
    await signOut();
    toast.success("Logged out successfully");
  };

  // Helper to get PDF URL for preview
  const [oldUrl, setOldUrl] = useState(null);
  const [newUrl, setNewUrl] = useState(null);

  useEffect(() => {
    if (oldFile) setOldUrl(URL.createObjectURL(oldFile));
    if (newFile) setNewUrl(URL.createObjectURL(newFile));
  }, [oldFile, newFile]);

  const changes = results?.changes || [];
  const impacts = results?.impacts || [];
  const amends = results?.amendments || [];

  const nCrit = changes.filter(c => c.severity === 'CRITICAL').length;
  const nMod = changes.filter(c => c.severity === 'MODERATE').length;
  const nLow = changes.length - nCrit - nMod;

  const selCard = changes[selectedIdx];
  const sImpacts = selCard ? impacts.filter(i => i.section_id === selCard.section_id) : [];
  const sAmends = selCard ? amends.filter(a => a.section_id === selCard.section_id) : [];

  const integrityPercent = Math.round((sources.filter(s => s.live).length / Math.max(sources.length, 1)) * 100);

  return (
    <div className={`text-zinc-50 min-h-screen ${highContrast ? 'bg-black' : 'bg-zinc-950'} relative selection:bg-indigo-500/30`}>
      <Toaster position="bottom-right" theme="dark" toastOptions={{ style: { background: '#18181b', border: '1px solid #27272a', color: '#fafafa' } }} />

      {/* Side Navigation */}
      <aside className={`fixed left-0 top-0 h-screen w-64 border-r ${highContrast ? 'border-zinc-700 bg-black' : 'border-zinc-800 bg-zinc-950/80'} backdrop-blur-2xl flex flex-col py-8 z-50 transition-colors`}>
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
        <nav className="flex-1 mt-4 px-3 space-y-1.5">
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
        <div className="mt-auto px-6 space-y-4">
          <div className="pt-6 border-t border-zinc-800/80">
            <div onClick={() => setShowSettings(true)} className="flex items-center gap-4 text-zinc-400 hover:text-zinc-50 cursor-pointer py-2.5 transition-colors">
              <span className="material-symbols-outlined text-sm">settings</span>
              <span className="text-[11px] uppercase tracking-widest font-semibold">Settings</span>
            </div>
            <div onClick={handleLogout} className="flex items-center gap-4 text-zinc-400 hover:text-red-400 cursor-pointer py-2.5 transition-colors">
              <span className="material-symbols-outlined text-sm">logout</span>
              <span className="text-[11px] uppercase tracking-widest font-semibold">Logout</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Wrapper */}
      <main className="ml-64 min-h-screen flex flex-col relative z-10">
        
        {/* Top Header */}
        <header className={`w-full top-0 sticky z-40 ${highContrast ? 'bg-black' : 'bg-zinc-950/80'} backdrop-blur-xl border-b border-zinc-800/80 flex justify-between items-center px-8 py-5 transition-colors`}>
          <div className="flex items-center gap-8">
            <h2 className="text-xl font-bold tracking-tight text-zinc-100">Project Command</h2>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex gap-3">
              <button onClick={triggerScraper} disabled={tracking} className={`px-4 py-2 rounded-md font-semibold text-[11px] uppercase tracking-wider transition-all ${tracking ? 'bg-zinc-800 text-zinc-400' : 'bg-zinc-100 text-zinc-900 hover:bg-white shadow-sm'}`}>
                {tracking ? 'Scraping...' : 'Live Scrape'}
              </button>
              <button disabled={!results} onClick={downloadReport} className={`px-4 py-2 rounded-md border font-semibold text-[11px] uppercase tracking-wider transition-all ${!results ? 'border-zinc-800 text-zinc-600 cursor-not-allowed' : 'border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-50'}`}>
                Export Report
              </button>
            </div>
            <div className="flex items-center gap-3 border-l border-zinc-800 pl-6">
              <div className="text-right">
                <p className="text-[11px] text-zinc-100 font-bold uppercase tracking-wide">{user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'AUTHORIZED USER'}</p>
                <p className="text-[9px] text-zinc-500 tracking-widest font-semibold mt-0.5">CLEARANCE: L5</p>
              </div>
              <div onClick={() => setShowProfile(true)} className="w-9 h-9 rounded-full bg-zinc-800 flex items-center justify-center cursor-pointer hover:bg-zinc-700 transition-colors">
                <span className="material-symbols-outlined text-zinc-400 text-lg">person</span>
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Grid */}
        <div className="p-8 grid grid-cols-1 lg:grid-cols-12 gap-8 flex-1">
          
          {/* Column 1: System Status & File Input */}
          <div className="col-span-12 lg:col-span-3 space-y-8">
            <section className="glass-panel p-6 rounded-xl relative overflow-hidden">
              {/* Upload Interface */}
              <div className="mb-8">
                 <h4 className="text-[10px] text-zinc-400 uppercase tracking-widest mb-4 font-bold">Load Parameters</h4>
                 <div className="space-y-4">
                   <div className="bg-zinc-900/40 border border-zinc-800 p-2.5 rounded-lg hover:border-zinc-700 transition-colors">
                     <label className="text-[9px] uppercase tracking-widest font-semibold text-zinc-500 mb-2 block px-1">Baseline Document</label>
                     <input type="file" accept=".pdf" onChange={e => setOldFile(e.target.files[0])} 
                      className="text-[10px] w-full text-zinc-300 file:bg-zinc-800 file:text-zinc-300 file:border-none file:px-3 file:py-1.5 file:rounded file:cursor-pointer file:font-semibold hover:file:bg-zinc-700 transition-all focus:outline-none" />
                   </div>
                   <div className="bg-zinc-900/40 border border-zinc-800 p-2.5 rounded-lg hover:border-zinc-700 transition-colors">
                     <label className="text-[9px] uppercase tracking-widest font-semibold text-zinc-500 mb-2 block px-1">Update Document</label>
                     <input type="file" accept=".pdf" onChange={e => setNewFile(e.target.files[0])} 
                      className="text-[10px] w-full text-zinc-300 file:bg-zinc-800 file:text-zinc-300 file:border-none file:px-3 file:py-1.5 file:rounded file:cursor-pointer file:font-semibold hover:file:bg-zinc-700 transition-all focus:outline-none" />
                   </div>
                   <button 
                      onClick={handleAnalyze} 
                      disabled={!oldFile || !newFile || loading}
                      className={`w-full py-3 mt-4 rounded-lg font-bold text-[11px] uppercase tracking-wider transition-all ${loading ? 'bg-zinc-800 text-zinc-500' : (!oldFile || !newFile ? 'bg-zinc-900 border border-zinc-800 text-zinc-600 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20')}`}>
                      {loading ? 'Initializing Analysis...' : 'Start Review'}
                   </button>
                 </div>
              </div>

              {/* PDF Preview Segment */}
              {(oldUrl || newUrl) && (
                <div className="border-t border-zinc-800/80 pt-6 mb-6">
                  <h4 className="text-[10px] text-zinc-400 uppercase tracking-widest mb-4 font-bold flex items-center gap-1.5">
                    <span className="material-symbols-outlined text-[13px]">visibility</span> Document Preview
                  </h4>
                  <div className="flex gap-2">
                    {oldUrl && (
                      <a href={oldUrl} target="_blank" rel="noreferrer" className="flex-1 bg-zinc-900 border border-zinc-800 p-3 rounded-lg flex flex-col items-center hover:bg-zinc-800 transition-all">
                        <span className="material-symbols-outlined text-zinc-500 text-lg mb-1">picture_as_pdf</span>
                        <span className="text-[8px] uppercase tracking-widest text-zinc-400 font-bold">Baseline</span>
                      </a>
                    )}
                    {newUrl && (
                      <a href={newUrl} target="_blank" rel="noreferrer" className="flex-1 bg-zinc-900 border border-zinc-800 p-3 rounded-lg flex flex-col items-center hover:bg-zinc-800 transition-all">
                        <span className="material-symbols-outlined text-zinc-500 text-lg mb-1">picture_as_pdf</span>
                        <span className="text-[8px] uppercase tracking-widest text-zinc-400 font-bold">Update</span>
                      </a>
                    )}
                  </div>
                </div>
              )}

              {/* System Status Segment */}
              <div className="border-t border-zinc-800/80 pt-8">
                <h3 className="font-bold text-xs tracking-widest text-zinc-400 uppercase mb-6 flex items-center gap-2">
                  <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.5)]"></span> System Status
                </h3>
                
                <div className="grid grid-cols-2 gap-4 mb-8">
                  <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 flex flex-col justify-center items-center">
                    <span className="material-symbols-outlined text-zinc-500 mb-2">dns</span>
                    <span className="text-2xl font-bold text-zinc-100">{sources.filter(s=>s.live).length}</span>
                    <span className="text-[9px] text-zinc-500 uppercase tracking-widest mt-1 font-semibold">Live Nodes</span>
                  </div>
                  <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 flex flex-col justify-center items-center relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-6 h-6 bg-emerald-500/10 rounded-bl-full flex items-center justify-center"><div className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></div></div>
                    <span className="material-symbols-outlined text-zinc-500 mb-2">security</span>
                    <span className="text-2xl font-bold text-zinc-100">{integrityPercent}%</span>
                    <span className="text-[9px] text-zinc-500 uppercase tracking-widest mt-1 font-semibold">Integrity</span>
                  </div>
                </div>

                <div className="space-y-3">
                  {sources.map(src => (
                    <div key={src.name} className="flex justify-between items-center text-[11px] border-b border-zinc-800/50 pb-2">
                      <span className="text-zinc-400 font-medium">{src.name}</span>
                      <span className={`${src.live ? 'text-emerald-500' : 'text-zinc-600'} font-bold tracking-wider text-[9px] uppercase`}>{src.live ? 'Connected' : 'Offline'}</span>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </div>

          {/* Column 2: Intelligence Feed */}
          <div className="col-span-12 lg:col-span-5 flex flex-col space-y-6 max-h-[calc(100vh-120px)] overflow-hidden">
             {/* Feed Header with Graph */}
             <div className="flex justify-between items-end mb-2 pb-5 border-b border-zinc-800/80">
               <div>
                 <h2 className="text-xl font-bold text-zinc-50 tracking-tight">Intelligence Stream</h2>
                 <p className="text-xs text-zinc-400 mt-1 font-medium">AI-parsed regulatory divergence</p>
               </div>
               <div className="flex flex-col items-end gap-3">
                 {/* Visual Graph Mock */}
                 <div className="flex items-end gap-1 h-8 opacity-90 mx-1">
                   {[40, 70, 45, 90, 65, 85, 30, 60, 100, 50, 75, 40].map((h, i) => (
                     <div key={i} className="w-1.5 bg-indigo-500/60 hover:bg-indigo-400 rounded-t-sm transition-all duration-300" style={{ height: `${h}%` }}></div>
                   ))}
                 </div>
                 {/* Metrics */}
                 {results && (
                   <div className="flex gap-2 items-center">
                     <div className="bg-red-500/10 text-red-500 px-2 py-0.5 rounded text-[10px] font-bold tracking-widest"><span className="animate-pulse mr-1">•</span>{nCrit} CRT</div>
                     <div className="bg-amber-500/10 text-amber-500 px-2 py-0.5 rounded text-[10px] font-bold tracking-widest">{nMod} MOD</div>
                     <div className="bg-zinc-800 text-zinc-300 px-2 py-0.5 rounded text-[10px] font-bold tracking-widest">{nLow} LOW</div>
                   </div>
                 )}
               </div>
             </div>

            <div className="flex-1 overflow-y-auto pr-2 space-y-3 pb-12 scrollbar-hide">
              {!results && !loading && !trackResult ? (
                <div className="glass-panel h-full min-h-[400px] rounded-xl flex flex-col items-center justify-center opacity-70">
                    <span className="material-symbols-outlined text-4xl text-zinc-500 mb-4 animate-bounce">query_stats</span>
                    <p className="text-center tracking-widest text-zinc-400 uppercase text-xs font-semibold">Awaiting Data Streams</p>
                </div>
              ) : loading ? (
                 <div className="glass-panel h-full min-h-[400px] rounded-xl flex flex-col items-center justify-center text-zinc-300">
                    <span className="material-symbols-outlined text-4xl animate-spin mb-4 duration-1000 text-indigo-500">sync</span>
                    <p className="tracking-widest uppercase text-xs animate-pulse font-bold text-zinc-400">Parsing Document Matrices...</p>
                 </div>
              ) : trackResult && !results ? (
                 <div className="bg-zinc-900 border border-zinc-800 p-5 rounded-xl relative shadow-sm">
                   <div className="absolute top-0 right-0 px-3 py-1 bg-emerald-500/10 text-emerald-500 rounded-bl-xl font-bold tracking-widest text-[9px] uppercase border-l border-b border-emerald-500/20">Intercept Success</div>
                   <div className="flex gap-4 items-center">
                     <div className="w-10 h-10 rounded-full bg-indigo-500/10 flex items-center justify-center">
                       <span className="material-symbols-outlined text-indigo-400">rss_feed</span>
                     </div>
                     <div>
                       <h4 className="text-zinc-100 font-bold uppercase tracking-wider text-sm mb-0.5">Live Feed Captured</h4>
                       <p className="text-xs text-zinc-400">Captured {trackResult.found} documents from sources.</p>
                       <p className="text-[10px] text-zinc-300 mt-2 p-2 bg-zinc-950 rounded border border-zinc-800 italic">{trackResult.circulars?.join(", ")}</p>
                     </div>
                   </div>
                   <button onClick={analyzeLive} className="w-full mt-5 py-2.5 bg-zinc-100 text-black hover:bg-white font-bold uppercase tracking-widest text-[10px] rounded-lg transition-all flex items-center justify-center gap-2 shadow-sm">
                     <span className="material-symbols-outlined text-[14px]">psychology</span> Force AI Analysis
                   </button>
                 </div>
              ) : (
                <AnimatePresence>
                  {changes.length === 0 && (
                     <div className="glass-panel p-8 rounded-xl flex flex-col items-center text-emerald-500">
                       <span className="material-symbols-outlined text-5xl mb-4">verified</span>
                       <h3 className="tracking-widest uppercase font-bold text-xs">Systems Normal</h3>
                     </div>
                  )}
                  {changes.map((c, i) => {
                    const isSevere = c.severity === 'CRITICAL';
                    const isMod = c.severity === 'MODERATE';
                    const accentColor = isSevere ? 'red' : isMod ? 'amber' : 'zinc';
                    const isSelected = i === selectedIdx;
                    const borderCls = isSelected ? `border-l-4 border-l-${accentColor}-500 border-zinc-700 bg-zinc-800/80` : `border-l-4 border-l-transparent border-zinc-800/40 bg-zinc-900/40 hover:bg-zinc-800/60 hover:border-zinc-700`;

                    return (
                    <motion.div key={i} onClick={() => setSelectedIdx(i)}
                      whileHover={{ x: 3 }} transition={{ type: "spring", stiffness: 300, damping: 20 }}
                      className={`p-5 rounded-r-xl border-y border-r transition-all duration-200 cursor-pointer relative ${borderCls}`}>
                      
                      <div className="absolute top-4 right-4">
                        <span className={`px-2 py-0.5 bg-${accentColor}-500/10 text-${accentColor}-400 text-[8px] font-bold rounded-sm uppercase tracking-widest`}>
                          {c.severity}
                        </span>
                      </div>
                      
                      <div className="flex gap-4 items-start relative z-10">
                        <div className={`mt-0.5 w-8 h-8 rounded bg-zinc-950 flex items-center justify-center border border-zinc-800 text-${accentColor}-400 shadow-sm`}>
                          <span className="material-symbols-outlined text-[16px]">{isSevere ? 'warning' : 'info'}</span>
                        </div>
                        <div className="flex-1 pr-10">
                          <div className="flex items-center gap-2 mb-1.5">
                            <span className="text-[10px] tracking-widest text-zinc-400 uppercase font-bold">{c.section_id}</span>
                            <span className="text-[10px] text-zinc-500 font-medium">• MATCH {(c.similarity_score * 100).toFixed(0)}%</span>
                          </div>
                          <h4 className="text-[13px] font-medium text-zinc-200 leading-relaxed line-clamp-3">
                            {clean(c.new_text)}
                          </h4>
                        </div>
                      </div>
                    </motion.div>
                  )})}
                </AnimatePresence>
              )}
            </div>
          </div>

          {/* Column 3: Action Panel */}
          <div className="col-span-12 lg:col-span-4 max-h-[calc(100vh-120px)] flex flex-col space-y-6">
            <section className="glass-panel flex-1 flex flex-col p-6 rounded-xl relative overflow-hidden overflow-y-auto">
              <div className="flex items-center justify-between mb-6 shrink-0 border-b border-zinc-800/60 pb-5">
                <h3 className="font-bold text-sm tracking-widest text-zinc-100 uppercase">Impact Frame</h3>
                <span className={`material-symbols-outlined text-[16px] ${results ? 'text-indigo-400' : 'text-zinc-600'} opacity-80`}>insights</span>
              </div>

              {!results || !selCard ? (
                <div className="flex flex-col items-center justify-center h-full opacity-40">
                  <span className="material-symbols-outlined text-4xl mb-3 text-zinc-500">account_tree</span>
                  <p className="text-[10px] uppercase tracking-widest text-center px-4 w-2/3 leading-relaxed text-zinc-400 font-semibold">Select an active node sequence to query sub-system impact.</p>
                </div>
              ) : (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col flex-1">
                  
                  {/* Policies Affected */}
                  <div className="mb-8 shrink-0">
                    <h4 className="text-[10px] text-zinc-400 uppercase tracking-widest border-b border-zinc-800/40 pb-2 mb-4 font-bold">Affected Sub-Systems</h4>
                    {sImpacts.length === 0 ? (
                      <p className="text-[11px] text-zinc-500 italic bg-zinc-900/40 p-3 border border-zinc-800/50 rounded-lg">No critical subsystems explicitly registered.</p>
                    ) : ( 
                      <div className="space-y-3">
                        {sImpacts.map((imp, idx) => (
                           <div key={idx} className="bg-zinc-900/60 border border-zinc-800 p-3.5 rounded-lg border-l-2 border-l-red-500 shadow-sm">
                             <p className="text-zinc-200 font-semibold text-[11px] tracking-wider uppercase mb-1.5">{imp.policy_name}</p>
                             <p className="text-[11px] text-zinc-400 line-clamp-2 leading-relaxed">{clean(imp.matched_text)}</p>
                           </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* AI Amendment Proposal */}
                  <div className="mb-auto flex-1 flex flex-col shrink-0">
                    <h4 className="text-[10px] text-zinc-400 uppercase tracking-widest border-b border-zinc-800/40 pb-2 mb-4 flex justify-between items-center font-bold">
                      <span>Provisional Amendment</span>
                      <span className="text-[8px] bg-indigo-500/10 text-indigo-400 px-1.5 py-0.5 rounded border border-indigo-500/20">AI SYNTHESIS</span>
                    </h4>
                    {sAmends.length === 0 ? (
                      <div className="text-[11px] text-zinc-500 italic bg-zinc-900/40 p-3 border border-zinc-800/50 rounded-lg">No autonomous intervention available.</div>
                    ) : (
                      <div className="flex flex-col h-full space-y-4">
                        <div className="w-full text-[12px] leading-relaxed bg-zinc-900 border border-zinc-800 text-zinc-300 p-4 rounded-lg overflow-y-auto custom-scrollbar shadow-inner">
                          <span className="font-semibold text-zinc-100 text-[10px] uppercase tracking-widest mb-2 block border-b border-zinc-800 pb-2">Revised Text:</span>
                          {clean(sAmends[0].proposed_text)}
                        </div>
                        <div className="bg-indigo-900/10 border border-indigo-500/20 p-4 rounded-lg">
                            <p className="text-[10px] uppercase tracking-widest text-indigo-400 mb-2 font-bold flex items-center gap-1.5"><span className="material-symbols-outlined text-[13px]">psychology</span> Reasoning Trace</p>
                            <p className="text-[11px] text-zinc-400 leading-relaxed max-h-24 overflow-y-auto custom-scrollbar">{sAmends[0].justification}</p>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="pt-6 mt-6 shrink-0 flex gap-3 border-t border-zinc-800/80">
                    <button className="flex-1 bg-zinc-900 text-zinc-300 border border-zinc-700 py-2.5 rounded-lg font-bold text-[10px] uppercase tracking-widest hover:bg-zinc-800 hover:text-white transition-all">
                       Dismiss
                    </button>
                    <button className="flex-1 bg-white text-black py-2.5 rounded-lg font-bold text-[10px] uppercase tracking-widest shadow-sm hover:bg-zinc-200 transition-all flex justify-center items-center gap-1.5">
                       Execute Merge <span className="material-symbols-outlined text-[14px]">done_all</span>
                    </button>
                  </div>

                </motion.div>
              )}
            </section>
          </div>

        </div>
      </main>

      <AnimatePresence>
        {showSettings && (
          <motion.div initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}} className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-md flex items-center justify-center p-4">
            <motion.div initial={{scale: 0.95, y: 10}} animate={{scale: 1, y: 0}} exit={{scale: 0.95, y: -10}} className="bg-zinc-950 w-full max-w-sm p-6 rounded-2xl border border-zinc-800 shadow-2xl relative">
              <button onClick={() => setShowSettings(false)} className="absolute top-4 right-4 w-8 h-8 rounded-full bg-zinc-900 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"><span className="material-symbols-outlined text-sm">close</span></button>
              <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2 tracking-tight"><span className="material-symbols-outlined text-indigo-400">tune</span> Configuration</h2>
              
              <div className="space-y-5">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-[13px] text-zinc-100 font-semibold">Auto-Scrape Interval</h4>
                    <p className="text-[11px] text-zinc-500 mt-0.5">Poll nodes every 5 m</p>
                  </div>
                  <div onClick={() => setAutoScrape(!autoScrape)} className={`w-11 h-6 rounded-full border flex items-center p-0.5 cursor-pointer custom-switch ${autoScrape ? 'bg-indigo-500 border-indigo-400' : 'bg-zinc-800 border-zinc-700'}`}>
                    <div className={`w-4 h-4 rounded-full shadow-sm custom-switch-knob ${autoScrape ? 'bg-white translate-x-5' : 'bg-zinc-400 translate-x-0.5'}`}></div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-[13px] text-zinc-100 font-semibold">High Contrast Layout</h4>
                    <p className="text-[11px] text-zinc-500 mt-0.5">Pitch black background</p>
                  </div>
                  <div onClick={() => setHighContrast(!highContrast)} className={`w-11 h-6 rounded-full border flex items-center p-0.5 cursor-pointer custom-switch ${highContrast ? 'bg-indigo-500 border-indigo-400' : 'bg-zinc-800 border-zinc-700'}`}>
                    <div className={`w-4 h-4 rounded-full shadow-sm custom-switch-knob ${highContrast ? 'bg-white translate-x-5' : 'bg-zinc-400 translate-x-0.5'}`}></div>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-[13px] text-zinc-100 font-semibold">Auditory Feedback</h4>
                    <p className="text-[11px] text-zinc-500 mt-0.5">Alerts on critical thresholds</p>
                  </div>
                  <div onClick={() => setAudibleAlerts(!audibleAlerts)} className={`w-11 h-6 rounded-full border flex items-center p-0.5 cursor-pointer custom-switch ${audibleAlerts ? 'bg-indigo-500 border-indigo-400' : 'bg-zinc-800 border-zinc-700'}`}>
                    <div className={`w-4 h-4 rounded-full shadow-sm custom-switch-knob ${audibleAlerts ? 'bg-white translate-x-5' : 'bg-zinc-400 translate-x-0.5'}`}></div>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
        
        {showProfile && (
          <motion.div initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}} className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-md flex items-center justify-center p-4">
            <motion.div initial={{scale: 0.95, y: 10}} animate={{scale: 1, y: 0}} exit={{scale: 0.95, y: -10}} className="bg-zinc-950 w-full max-w-sm p-6 rounded-2xl border border-zinc-800 shadow-2xl relative text-center">
              <button onClick={() => setShowProfile(false)} className="absolute top-4 right-4 w-8 h-8 rounded-full bg-zinc-900 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"><span className="material-symbols-outlined text-sm">close</span></button>
              
              <div className="w-20 h-20 mx-auto rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center mb-5 mt-2">
                <span className="material-symbols-outlined text-4xl text-zinc-400">person</span>
              </div>
              <h2 className="text-xl font-bold text-zinc-100 tracking-tight">{user?.user_metadata?.full_name || 'Agent Operator'}</h2>
              <p className="text-[10px] text-emerald-500 font-mono mt-2 uppercase tracking-widest bg-emerald-500/10 inline-block px-3 py-1 rounded-full">Level 5 Access</p>
              
              <div className="mt-6 text-left bg-zinc-900 p-4 rounded-xl border border-zinc-800">
                  <p className="text-[11px] text-zinc-500 uppercase tracking-widest border-b border-zinc-800/80 pb-2.5 mb-2.5 flex justify-between items-center"><span className="font-semibold">Terminal ID:</span> <span className="text-zinc-300 font-mono lowercase">{user?.email}</span></p>
                  <p className="text-[11px] text-zinc-500 uppercase tracking-widest flex justify-between items-center"><span className="font-semibold">Organization:</span> <span className="text-zinc-300 font-mono">{user?.user_metadata?.company || 'RESTRICTED'}</span></p>
              </div>
              
              <button onClick={handleLogout} className="mt-6 w-full py-2.5 bg-red-500/10 text-red-500 font-bold uppercase text-[11px] tracking-widest rounded-lg hover:bg-red-500 hover:text-white transition-all flex items-center justify-center gap-2 shadow-sm">
                Terminate Session
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
