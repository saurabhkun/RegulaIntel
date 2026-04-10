import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster, toast } from 'sonner';
import { useAuth } from '../contexts/AuthContext';
import { supabase } from '../utils/supabaseClient';

export default function Dashboard() {
  const [oldFile, setOldFile] = useState(null);
  const [newFile, setNewFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [tracking, setTracking] = useState(false);
  const [trackResult, setTrackResult] = useState(null);
  const { user, signOut } = useAuth();

  const clean = (text) => {
    if (!text) return "";
    return text.replace(/[#*`_~]/g, '').replace(/\s+/g, ' ').trim();
  };

  const sources = [
    { name: "RBI", full: "Reserve Bank of India", live: true },
    { name: "SEBI", full: "Securities & Exchange Board", live: true },
    { name: "MCA", full: "Ministry of Corporate Affairs", live: false },
    { name: "IRDAI", full: "Insurance Regulatory Auth.", live: false },
  ];

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
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = "RegulaIntel_Report.pdf";
      a.click();
      toast.success("Professional Audit exported!");
    } catch (e) {
      toast.error("Failed to download PDF.");
    }
  };

  const handleLogout = async () => {
    await signOut();
    toast.success("Logged out successfully");
  };

  const changes = results?.changes || [];
  const impacts = results?.impacts || [];
  const amends = results?.amendments || [];

  const nCrit = changes.filter(c => c.severity === 'CRITICAL').length;
  const nMod = changes.filter(c => c.severity === 'MODERATE').length;
  const nLow = changes.length - nCrit - nMod;

  const selCard = changes[selectedIdx];
  const sImpacts = selCard ? impacts.filter(i => i.section_id === selCard.section_id) : [];
  const sAmends = selCard ? amends.filter(a => a.section_id === selCard.section_id) : [];

  const staggerContainer = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.1 } } };
  const cardAnim = { hidden: { opacity: 0, y: 15 }, show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } } };

  return (
    <div className="text-on-background min-h-screen bg-background relative selection:bg-cyan-500/30">
      <Toaster position="bottom-right" theme="dark" toastOptions={{ style: { background: '#191f2f', border: '1px solid rgba(0,242,255,0.2)', color: '#dce2f8' } }} />

      {/* Side Navigation */}
      <aside className="fixed left-0 top-0 h-screen w-64 border-r border-cyan-500/10 bg-[#070e1d]/80 backdrop-blur-2xl flex flex-col py-8 z-50">
        <div className="px-6 mb-12">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-cyan-500/20 rounded flex items-center justify-center border border-cyan-500/30">
              <span className="material-symbols-outlined text-cyan-400 text-lg">terminal</span>
            </div>
            <div>
              <h1 className="text-cyan-400 font-black font-[Space_Grotesk] tracking-widest text-lg leading-tight text-shadow shadow-cyan-500/50">RegulaIntel</h1>
              <p className="font-['Space_Grotesk'] uppercase tracking-widest text-[10px] text-slate-500">V.2.0 ACTIVE</p>
            </div>
          </div>
        </div>
        <nav className="flex-1 mt-4">
          <div className="bg-cyan-500/10 text-cyan-400 border-r-2 border-cyan-400 shadow-[inset_0_0_15px_rgba(0,242,255,0.05)] px-6 py-4 flex items-center gap-4 cursor-pointer relative overflow-hidden transition-all duration-300">
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-cyan-400 to-transparent"></div>
            <span className="material-symbols-outlined">hub</span>
            <span className="font-['Space_Grotesk'] uppercase tracking-widest text-[11px] font-bold">Intelligence Hub</span>
          </div>
        </nav>
        <div className="mt-auto px-6 space-y-4">
          <div className="pt-6 border-t border-cyan-500/10">
            <div className="flex items-center gap-4 text-slate-500 hover:text-cyan-400 cursor-pointer py-2">
              <span className="material-symbols-outlined text-sm">settings</span>
              <span className="text-[10px] uppercase tracking-widest font-['Space_Grotesk']">Settings</span>
            </div>
            <div onClick={handleLogout} className="flex items-center gap-4 text-slate-500 hover:text-red-400 cursor-pointer py-2 transition-colors">
              <span className="material-symbols-outlined text-sm">logout</span>
              <span className="text-[10px] uppercase tracking-widest font-['Space_Grotesk']">Logout</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Wrapper */}
      <main className="ml-64 min-h-screen flex flex-col relative z-10">
        
        {/* Top Header */}
        <header className="w-full top-0 sticky z-40 bg-[#070e1d]/80 backdrop-blur-xl border-b border-cyan-500/10 shadow-[0_4px_20px_rgba(0,242,255,0.02)] flex justify-between items-center px-8 py-4">
          <div className="flex items-center gap-8">
            <h2 className="text-xl font-bold tracking-tighter text-cyan-400 drop-shadow-[0_0_8px_rgba(0,242,255,0.3)] font-[Space_Grotesk]">RegulaIntel COMMAND</h2>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex gap-4">
              <button onClick={triggerScraper} disabled={tracking} className={`px-4 py-2 border border-cyan-500/30 font-['Space_Grotesk'] font-bold text-[10px] uppercase tracking-widest transition-all ${tracking ? 'bg-cyan-500/30 text-cyan-200' : 'bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500/20 shadow-[0_0_10px_rgba(0,242,255,0.15)] hover:shadow-[0_0_15px_rgba(0,242,255,0.3)]'}`}>
                {tracking ? 'Scraping...' : 'Live Scrape Sources'}
              </button>
              <button disabled={!results} onClick={downloadReport} className={`px-4 py-2 bg-surface-container-high border border-outline-variant/30 font-['Space_Grotesk'] font-bold text-[10px] uppercase tracking-widest transition-all ${!results ? 'opacity-50 cursor-not-allowed text-slate-500' : 'text-on-surface hover:bg-surface-bright active:scale-95'}`}>
                Generate PDF Report
              </button>
            </div>
            <div className="flex items-center gap-3 border-l border-cyan-500/10 pl-6">
              <div className="text-right">
                <p className="text-[10px] font-['Space_Grotesk'] text-cyan-400 font-bold uppercase">{user?.email?.split('@')[0] || 'AUTHORIZED USER'}</p>
                <p className="text-[9px] text-slate-500 tracking-widest">CLEARANCE: LEVEL 5</p>
              </div>
              <div className="w-10 h-10 rounded-full border border-cyan-500/40 bg-surface-container-high flex items-center justify-center overflow-hidden">
                <span className="material-symbols-outlined text-cyan-500">account_circle</span>
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Grid */}
        <div className="p-8 grid grid-cols-1 md:grid-cols-12 gap-8 flex-1">
          
          {/* Column 1: File Uploads & Radar */}
          <div className="col-span-12 md:col-span-3 xl:col-span-3 space-y-8">
            <section className="glass-panel p-6 rounded-xl relative overflow-hidden">
              <h3 className="font-['Space_Grotesk'] font-bold text-xs tracking-widest text-cyan-400 uppercase mb-6 flex items-center gap-2">
                <span className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></span> Active Radar
              </h3>
              <div className="relative w-full aspect-square flex items-center justify-center mb-8">
                <div className="absolute inset-0 border-[0.5px] border-cyan-500/20 rounded-full"></div>
                <div className="absolute inset-[25%] border-[0.5px] border-cyan-500/20 rounded-full"></div>
                <div className="absolute inset-[50%] border-[0.5px] border-cyan-500/20 rounded-full"></div>
                <div className="absolute inset-0 radar-scan rounded-full" style={{ background: 'conic-gradient(from 0deg at 50% 50%, transparent 0deg, rgba(0, 242, 255, 0.15) 60deg, transparent 65deg)', animation: 'radar-spin 4s linear infinite' }}></div>
                
                {/* Dots representing live sources */}
                <div className="absolute top-1/4 right-1/3 w-2 h-2 bg-secondary-container rounded-full shadow-[0_0_10px_#16ff9e] animate-pulse"></div>
                <div className="absolute bottom-1/3 left-1/4 w-1.5 h-1.5 bg-cyan-400 rounded-full shadow-[0_0_8px_#00f2ff]"></div>
                
                <div className="text-center z-10 bg-[#070e1d]/80 rounded-full h-20 w-20 flex flex-col items-center justify-center border border-cyan-500/30 backdrop-blur-sm">
                  <span className="block text-2xl font-['Space_Grotesk'] font-black text-cyan-400 glow-cyan leading-none">{sources.filter(s=>s.live).length}</span>
                  <span className="text-[8px] mt-1 font-['Space_Grotesk'] tracking-widest text-[#dce2f8]">LIVE NODES</span>
                </div>
              </div>
              
              <div className="space-y-3 mb-6">
                {sources.map(src => (
                  <div key={src.name} className="flex justify-between items-center text-[10px] font-[Inter] border-b border-cyan-500/5 pb-2">
                    <span className="text-slate-400 font-semibold">{src.name}</span>
                    <span className={`${src.live ? 'text-secondary-container' : 'text-slate-600'} font-bold tracking-wider`}>{src.live ? 'ACTIVE' : 'OFFLINE'}</span>
                  </div>
                ))}
              </div>

              {/* Upload Interface mapped here */}
              <div className="mt-6 border-t border-cyan-500/10 pt-4">
                 <h4 className="font-['Space_Grotesk'] text-[10px] text-cyan-300 uppercase tracking-widest mb-3">Load Parameters</h4>
                 <div className="space-y-3">
                   <div className="bg-surface-container-lowest border border-cyan-500/20 p-2 rounded-lg hover:border-cyan-500/50 transition-colors">
                     <label className="text-[9px] uppercase tracking-wider text-slate-500 mb-1 block px-2">Old Circular (Baseline)</label>
                     <input type="file" accept=".pdf" onChange={e => setOldFile(e.target.files[0])} 
                      className="text-[10px] w-full text-cyan-100 file:bg-cyan-500/10 file:text-cyan-400 file:border-none file:px-2 file:py-1 file:rounded file:cursor-pointer file:font-semibold" />
                   </div>
                   <div className="bg-surface-container-lowest border border-cyan-500/20 p-2 rounded-lg hover:border-cyan-500/50 transition-colors">
                     <label className="text-[9px] uppercase tracking-wider text-slate-500 mb-1 block px-2">New Circular (Update)</label>
                     <input type="file" accept=".pdf" onChange={e => setNewFile(e.target.files[0])} 
                      className="text-[10px] w-full text-cyan-100 file:bg-cyan-500/10 file:text-cyan-400 file:border-none file:px-2 file:py-1 file:rounded file:cursor-pointer file:font-semibold" />
                   </div>
                   <button 
                      onClick={handleAnalyze} 
                      disabled={!oldFile || !newFile || loading}
                      className={`w-full py-2.5 mt-2 rounded font-['Space_Grotesk'] font-bold text-[11px] uppercase tracking-widest transition-all ${loading ? 'bg-cyan-500/20 text-cyan-300 blur-[0.5px]' : (!oldFile || !newFile ? 'bg-surface-container text-slate-500 cursor-not-allowed' : 'bg-gradient-to-r from-primary-container to-cyan-500 text-on-primary shadow-[0_0_15px_rgba(0,242,255,0.3)] hover:scale-[1.02]')}`}>
                      {loading ? 'Initializing Neural Net...' : 'Initiate Analysis'}
                   </button>
                 </div>
              </div>
            </section>
          </div>

          {/* Column 2: Intelligence Feed (Middle area) */}
          <div className="col-span-12 md:col-span-5 xl:col-span-5 flex flex-col space-y-6 max-h-[calc(100vh-120px)] overflow-hidden">
            <div className="flex justify-between items-end mb-2">
               <div>
                 <h2 className="font-[Space_Grotesk] text-lg font-bold text-on-background tracking-wide">Intelligence Stream</h2>
                 <p className="text-xs text-outline font-medium tracking-wide">AI-parsed regulatory divergence</p>
               </div>
               {results && (
                 <div className="flex gap-2 items-center">
                   <div className="bg-error/10 text-error px-2 py-0.5 rounded border border-error/30 text-[9px] font-bold tracking-widest"><span className="animate-pulse mr-1">•</span>{nCrit} CRT</div>
                   <div className="bg-tertiary-container/10 text-tertiary-fixed-dim px-2 py-0.5 rounded border border-tertiary-container/30 text-[9px] font-bold tracking-widest">{nMod} MOD</div>
                   <div className="bg-secondary-container/10 text-secondary-container px-2 py-0.5 rounded border border-secondary-container/30 text-[9px] font-bold tracking-widest">{nLow} LOW</div>
                 </div>
               )}
            </div>

            <div className="flex-1 overflow-y-auto pr-2 space-y-4 pb-12 scrollbar-hide">
              {!results && !loading && !trackResult ? (
                <div className="glass-panel h-full min-h-[400px] rounded-xl flex flex-col items-center justify-center opacity-70">
                    <span className="material-symbols-outlined text-4xl text-cyan-500/50 mb-4 animate-bounce">query_stats</span>
                    <p className="text-center font-['Space_Grotesk'] tracking-widest text-[#b9cacb] uppercase">Awaiting Data Streams</p>
                </div>
              ) : loading ? (
                 <div className="glass-panel h-full min-h-[400px] rounded-xl flex flex-col items-center justify-center text-cyan-400">
                    <span className="material-symbols-outlined text-4xl animate-spin mb-4 duration-1000">sync</span>
                    <p className="font-['Space_Grotesk'] tracking-widest uppercase text-xs animate-pulse font-bold">Parsing Matrices...</p>
                 </div>
              ) : trackResult && !results ? (
                 <div className="glass-panel p-5 rounded-xl border border-secondary-container/30 relative">
                   <div className="absolute top-0 right-0 px-3 py-1 bg-secondary-container text-on-secondary rounded-bl-xl font-bold tracking-widest text-[9px] uppercase shadow-[0_0_10px_rgba(22,255,158,0.5)]">Intercept Success</div>
                   <div className="flex gap-4 items-center">
                     <span className="material-symbols-outlined text-secondary-container text-3xl">rss_feed</span>
                     <div>
                       <h4 className="text-cyan-100 font-['Space_Grotesk'] font-bold uppercase tracking-wider text-sm mb-1">Live Feed Captured</h4>
                       <p className="text-xs text-slate-400">Captured {trackResult.found} documents from sources.</p>
                       <p className="text-[10px] text-cyan-200 mt-2 p-2 bg-cyan-900/40 rounded italic font-mono">{trackResult.circulars?.join(", ")}</p>
                     </div>
                   </div>
                   <button onClick={analyzeLive} className="w-full mt-4 py-2 border border-secondary-container text-secondary-container hover:bg-secondary-container/10 font-bold uppercase tracking-widest text-[10px] rounded transition-all flex items-center justify-center gap-2">
                     <span className="material-symbols-outlined text-[14px]">psychology</span> Force AI Analysis
                   </button>
                 </div>
              ) : (
                <AnimatePresence>
                  {changes.length === 0 && (
                     <div className="glass-panel p-8 rounded-xl flex flex-col items-center text-secondary-container">
                       <span className="material-symbols-outlined text-5xl mb-4">verified</span>
                       <h3 className="font-['Space_Grotesk'] tracking-widest uppercase">Systems Normal</h3>
                     </div>
                  )}
                  {changes.map((c, i) => {
                    const isSevere = c.severity === 'CRITICAL';
                    const isMod = c.severity === 'MODERATE';
                    const glowColor = isSevere ? 'error' : isMod ? 'tertiary-container' : 'secondary-container';
                    const activeBg = i === selectedIdx ? 'bg-surface-container-highest backdrop-blur-3xl' : 'bg-surface-container-high/60';
                    const activeBorder = i === selectedIdx ? `border-l-4 border-cyan-400 border-y-[0.5px] border-r-[0.5px] border-y-cyan-500/20 border-r-cyan-500/20` : `border-l-4 border-${glowColor} border-y-[0.5px] border-r-[0.5px] border-y-transparent border-r-transparent hover:bg-surface-container-high hover:border-y-cyan-500/10 hover:border-r-cyan-500/10`;

                    return (
                    <motion.div key={i} onClick={() => setSelectedIdx(i)}
                      whileHover={{ x: 5 }} transition={{ type: "spring", stiffness: 300, damping: 20 }}
                      className={`p-4 rounded-r-xl ${activeBorder} ${activeBg} cursor-pointer group relative overflow-hidden transition-all duration-300`}>
                      
                      {i === selectedIdx && <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-transparent pointer-events-none"></div>}
                      
                      <div className="absolute top-4 right-4">
                        <span className={`px-2 py-0.5 bg-${glowColor}/10 text-${isMod ? 'tertiary-fixed-dim' : glowColor} text-[8px] font-bold rounded-sm border border-${glowColor}/30 uppercase tracking-widest`}>
                          {c.severity}
                        </span>
                      </div>
                      
                      <div className="flex gap-4 items-start z-10 relative">
                        <div className={`w-10 h-10 mt-1 bg-[#0c1322] rounded flex items-center justify-center border border-outline-variant text-${isMod ? 'tertiary-fixed-dim' : glowColor} group-hover:scale-105 transition-transform shadow-[0_0_15px_rgba(var(--${glowColor}),0.2)]`}>
                          <span className="material-symbols-outlined text-[18px]">{isSevere ? 'warning' : 'info'}</span>
                        </div>
                        <div className="flex-1 pr-10">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-[9px] font-['Space_Grotesk'] tracking-widest text-[#849495] uppercase font-bold">{c.section_id}</span>
                            <span className="text-[9px] text-[#4d5b6b]">• MATCH {(c.similarity_score * 100).toFixed(0)}%</span>
                          </div>
                          <h4 className="text-[13px] font-['Inter'] font-medium text-cyan-50/90 leading-snug line-clamp-3 2xl:line-clamp-4">
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

          {/* Column 3: Action & Impact Panel */}
          <div className="col-span-12 md:col-span-4 xl:col-span-4 max-h-[calc(100vh-120px)] flex flex-col space-y-6">
            <section className="glass-panel flex-1 flex flex-col p-6 rounded-xl border-t-[3px] border-t-cyan-500 relative overflow-hidden overflow-y-auto">
              <div className="flex items-center justify-between mb-6 shrink-0">
                <h3 className="font-['Space_Grotesk'] font-bold text-sm tracking-widest text-cyan-400 uppercase">Impact Resolution</h3>
                <span className="material-symbols-outlined text-cyan-400 animate-[spin_4s_linear_infinite] text-sm opacity-60">settings_input_component</span>
              </div>

              {!results || !selCard ? (
                <div className="flex flex-col items-center justify-center h-full opacity-40">
                  <span className="material-symbols-outlined text-4xl mb-3">account_tree</span>
                  <p className="text-[10px] uppercase font-['Space_Grotesk'] tracking-widest text-center px-4 w-2/3 leading-relaxed">System standby. Select active node to visualize impact topology.</p>
                </div>
              ) : (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col flex-1">
                  
                  {/* Policies Affected */}
                  <div className="mb-6 shrink-0">
                    <h4 className="text-[10px] font-['Space_Grotesk'] text-slate-400 uppercase tracking-widest border-b border-cyan-500/20 pb-1 mb-3">Affected Sub-Systems</h4>
                    {sImpacts.length === 0 ? (
                      <p className="text-[11px] text-[#849495] italic bg-[#000000]/20 p-2 border border-[#849495]/20 rounded">No critical subsystems affected.</p>
                    ) : ( 
                      <div className="space-y-2">
                        {sImpacts.map((imp, idx) => (
                           <div key={idx} className="bg-surface-container-lowest border border-error/20 p-3 rounded-lg relative overflow-hidden group">
                             <div className="absolute left-0 top-0 bottom-0 w-[2px] bg-error"></div>
                             <p className="text-error font-bold text-[11px] tracking-wider uppercase mb-1">{imp.policy_name}</p>
                             <p className="text-[10px] text-slate-400 line-clamp-2 leading-relaxed">{clean(imp.matched_text)}</p>
                           </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* AI Amendment Proposal */}
                  <div className="mb-auto flex-1 flex flex-col shrink-0">
                    <h4 className="text-[10px] font-['Space_Grotesk'] text-cyan-400 uppercase tracking-widest border-b border-cyan-500/40 pb-1 mb-3 flex justify-between items-center">
                      <span>Provisional Amendment</span>
                      <span className="text-[8px] bg-cyan-500/20 text-cyan-300 px-1.5 py-0.5 rounded border border-cyan-500/30">AI GENERATED</span>
                    </h4>
                    {sAmends.length === 0 ? (
                      <p className="text-[11px] text-[#849495] italic bg-[#000000]/20 p-2 border border-[#849495]/20 rounded">No autonomous intervention protocol available for this constraint.</p>
                    ) : (
                      <div className="flex flex-col h-full space-y-3">
                        <textarea 
                          readOnly
                          value={clean(sAmends[0].proposed_text)}
                          className="w-full flex-1 min-h-[140px] text-[12px] font-['Inter'] leading-relaxed bg-surface-container-lowest text-cyan-50 p-3 rounded border border-cyan-500/20 focus:outline-none resize-none custom-scrollbar"
                        />
                        <div className="bg-cyan-900/20 border border-cyan-500/30 p-3 rounded">
                            <p className="text-[9px] uppercase tracking-widest text-[#b9cacb] mb-1 font-bold">Execution Strategy</p>
                            <p className="text-[11px] text-cyan-300/80 leading-relaxed max-h-24 overflow-y-auto pr-1">{sAmends[0].justification}</p>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="pt-5 mt-4 shrink-0 flex gap-3">
                    <button className="flex-1 bg-cyan-500/10 text-cyan-400 border border-cyan-400 py-3 rounded font-['Space_Grotesk'] font-bold text-[10px] uppercase tracking-widest hover:bg-cyan-500/20 transition-all flex justify-center items-center gap-2">
                       Dismiss Alert
                    </button>
                    <button className="flex-1 bg-cyan-500 text-[#002022] py-3 rounded font-['Space_Grotesk'] font-bold text-[10px] uppercase tracking-widest shadow-[0_0_15px_rgba(0,242,255,0.2)] hover:shadow-[0_0_20px_rgba(0,242,255,0.5)] transition-all flex justify-center items-center gap-2">
                       Execute Merge <span className="material-symbols-outlined text-[14px]">done_all</span>
                    </button>
                  </div>

                </motion.div>
              )}
            </section>
          </div>

        </div>
      </main>
    </div>
  );
}
