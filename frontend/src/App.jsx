import React, { useState } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, ShieldAlert, FileDown, Search, ArrowRight, RefreshCw, BarChart, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import './index.css';

export default function App() {
  const [oldFile, setOldFile] = useState(null);
  const [newFile, setNewFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [tracking, setTracking] = useState(false);
  const [trackResult, setTrackResult] = useState(null);

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

  const handleAnalyze = async () => {
    if (!oldFile || !newFile) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("old_pdf", oldFile);
      formData.append("new_pdf", newFile);
      
      const res = await fetch("http://localhost:8000/api/analyze", {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      setResults(data);
      setSelectedIdx(0);
    } catch (e) {
      alert("Error: " + e.message);
    }
    setLoading(false);
  };

  const triggerScraper = async () => {
    setTracking(true);
    setTrackResult(null);
    try {
      const res = await fetch("http://localhost:8000/api/monitor/check-once/live");
      const data = await res.json();
      setTrackResult(data);
    } catch(e) {
      alert("Scraper Error: " + e.message);
    }
    setTracking(false);
  };

  const analyzeLive = async () => {
    setLoading(true);
    setResults(null);
    try {
      const res = await fetch("http://localhost:8000/api/analyze/live", { method: "POST" });
      const data = await res.json();
      if(data.message) {
        alert(data.message);
      } else {
        setResults(data);
        setSelectedIdx(0);
      }
    } catch (e) {
      alert("Error: " + e.message);
    }
    setLoading(false);
  };

  const downloadReport = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/report", {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(results)
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = "RegulaIntel_Report.pdf";
      a.click();
    } catch (e) {
      alert("Failed to download PDF.");
    }
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

  // Animation variants
  const staggerContainer = { hidden: { opacity: 0 }, show: { opacity: 1, transition: { staggerChildren: 0.1 } } };
  const cardAnim = { hidden: { opacity: 0, y: 15 }, show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } } };
  const panelAnim = { hidden: { opacity: 0, scale: 0.98 }, show: { opacity: 1, scale: 1, transition: { duration: 0.4, ease: "easeOut" } } };

  return (
    <div className="h-screen w-full flex flex-col pt-3 pb-6 px-6 max-w-7xl mx-auto overflow-hidden relative z-10">
      
      {/* Topnav */}
      <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="flex justify-between items-center pb-4 mb-4 border-b border-slate-200/50">
        <div className="flex items-center gap-3">
          <motion.div whileHover={{ rotate: 15 }} className="bg-blue-600 p-2 rounded-xl shadow-lg shadow-blue-600/30">
            <ShieldAlert className="text-white" size={24}/>
          </motion.div>
          <div>
            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-600 tracking-tight">RegulaIntel</span>
            <span className="ml-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-[10px] uppercase font-bold py-1 px-2.5 rounded-full tracking-wider shadow-sm">AI-Powered</span>
          </div>
        </div>
        <div className="text-sm font-medium text-slate-500 bg-white/50 px-3 py-1.5 rounded-full backdrop-blur-sm border border-white/50 shadow-sm">
          Autonomous Regulatory Compliance &bull; Financial Sector
        </div>
      </motion.div>

      <div className="flex gap-6 flex-1 min-h-0">
        
        {/* LEFT COLUMN - Sources & Uploads */}
        <motion.div variants={panelAnim} initial="hidden" animate="show" className="flex-1 flex flex-col min-w-[280px]">
          <div className="glass-panel flex-1 p-6 overflow-y-auto">
            <div className="section-label flex items-center gap-1.5"><Activity size={14} className="text-blue-500"/> Intelligence Sources</div>
            
            <div className="flex flex-col gap-2.5 mb-8">
              {sources.map(src => (
                <motion.div whileHover={{ scale: 1.02 }} key={src.name} className="flex justify-between items-center p-3 rounded-xl border border-white/60 bg-white/40 shadow-sm transition-colors hover:bg-white/60 cursor-default">
                  <div>
                    <div className="font-bold text-sm text-slate-800 tracking-wide">{src.name}</div>
                    <div className="text-[11px] text-slate-500 font-medium">{src.full}</div>
                  </div>
                  <div className="flex items-center">
                    <div className={src.live ? "live-dot" : "off-dot"} />
                    <span className={`text-[10px] font-bold ${src.live ? 'text-emerald-600' : 'text-slate-400'}`}>
                      {src.live ? "LIVE" : "OFFLINE"}
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>

            <div className="section-label flex items-center gap-1.5 mt-2"><Activity size={14} className="text-emerald-500"/> Live Scraper</div>
            <motion.button 
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={triggerScraper} 
              disabled={tracking}
              className="w-full py-2.5 mb-3 flex justify-center items-center gap-2 rounded-xl font-bold tracking-wide text-[13px] transition-colors border border-emerald-500/30 bg-emerald-50 hover:bg-emerald-100 text-emerald-700"
            >
              {tracking ? <RefreshCw className="animate-spin" size={16}/> : <Activity size={16}/>}
              {tracking ? "Scraping Regulators..." : "Trigger Live Scraper"}
            </motion.button>
            <AnimatePresence>
              {trackResult && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="mb-6 overflow-hidden">
                  <div className="p-3 rounded-xl bg-white border border-emerald-200 shadow-sm relative">
                    <div className="absolute -top-1 -right-1 flex h-3 w-3">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
                    </div>
                    <div className="flex items-center gap-2 mb-1.5">
                      <CheckCircle2 size={16} className="text-emerald-500"/>
                      <span className="text-[12px] font-bold text-slate-800 tracking-wide uppercase">Scrape Success</span>
                    </div>
                    <div className="text-[11px] text-slate-500 font-medium ml-6 leading-relaxed mb-3">
                      Captured <span className="text-slate-700 font-bold">{trackResult.found}</span> new records:<br/>
                      <span className="text-blue-500 max-w-full truncate inline-block mt-0.5">{trackResult.circulars?.join(", ")}</span>
                    </div>
                    <motion.button 
                      whileHover={{ scale: 1.02, boxShadow: "0 4px 15px -3px rgba(16, 185, 129, 0.3)" }}
                      whileTap={{ scale: 0.98 }}
                      onClick={analyzeLive}
                      className="w-full py-2 mt-1 rounded-lg text-[11px] font-bold tracking-wider text-white bg-gradient-to-r from-emerald-500 to-teal-500 shadow-md flex justify-center items-center gap-1.5 border border-emerald-400"
                    >
                      <RefreshCw size={12} className={loading ? "animate-spin" : ""}/> 
                      AUTO-ANALYZE INTERCEPT
                    </motion.button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>


            <div className="section-label flex items-center gap-1.5 mt-6"><Search size={14} className="text-indigo-500"/> Analyze Circulars</div>
            
            <div className="mb-4 group">
              <label className="block text-xs font-bold text-slate-700 mb-1.5 ml-1 transition-colors group-hover:text-blue-600">Old Circular (Baseline)</label>
              <input type="file" accept=".pdf" onChange={e => setOldFile(e.target.files[0])} 
                     className="block w-full text-sm text-slate-600
                     file:mr-3 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:tracking-wide
                     file:bg-white file:text-blue-600 file:shadow-sm hover:file:bg-blue-50 transition-all border border-slate-200/60 rounded-xl p-1 bg-slate-50/50 backdrop-blur-sm cursor-pointer"/>
            </div>
            
            <div className="mb-8 group">
              <label className="block text-xs font-bold text-slate-700 mb-1.5 ml-1 transition-colors group-hover:text-blue-600">New Circular (Latest)</label>
              <input type="file" accept=".pdf" onChange={e => setNewFile(e.target.files[0])}
                     className="block w-full text-sm text-slate-600
                     file:mr-3 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:tracking-wide
                     file:bg-white file:text-blue-600 file:shadow-sm hover:file:bg-blue-50 transition-all border border-slate-200/60 rounded-xl p-1 bg-slate-50/50 backdrop-blur-sm cursor-pointer"/>
            </div>

            <motion.button 
              whileHover={{ scale: 1.02, boxShadow: "0 10px 25px -5px rgba(37, 99, 235, 0.4)" }}
              whileTap={{ scale: 0.98 }}
              onClick={handleAnalyze} 
              disabled={!oldFile || !newFile || loading}
              className={`w-full py-3.5 flex justify-center items-center gap-2 rounded-xl font-bold tracking-wide text-sm transition-all shadow-md
                          ${(!oldFile || !newFile || loading) ? 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none' : 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white hover:from-blue-500 hover:to-indigo-500'}`}
            >
              {loading ? <RefreshCw className="animate-spin" size={18}/> : <Search size={18}/>}
              {loading ? "Analyzing Context..." : "Run Analysis"}
            </motion.button>
          </div>
        </motion.div>

        {/* CENTER COLUMN - Feed */}
        <motion.div variants={panelAnim} initial="hidden" animate="show" transition={{ delay: 0.1 }} className="flex-[2] flex flex-col min-w-[420px]">
          <div className="glass-panel flex-1 p-6 overflow-y-auto relative">
            <div className="flex justify-between items-end mb-5">
              <div className="section-label flex items-center gap-1.5 m-0"><FileText size={14} className="text-emerald-500"/> Intelligence Feed</div>
            </div>

            <AnimatePresence mode="wait">
              {!results && !loading ? (
                <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full flex flex-col items-center justify-center text-slate-400 mt-10">
                  <motion.div animate={{ y: [0, -10, 0] }} transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}>
                    <div className="bg-slate-100 p-6 rounded-3xl mb-5 shadow-inner">
                      <Search size={48} className="text-slate-300"/>
                    </div>
                  </motion.div>
                  <div className="font-bold text-slate-600 text-lg mb-1 tracking-tight">No analysis yet</div>
                  <div className="text-sm font-medium">Upload two PDF circulars and tap Analyze to begin.</div>
                </motion.div>
              ) : loading ? (
                <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full flex flex-col items-center pt-20 mt-10 text-blue-600">
                  <RefreshCw size={40} className="animate-spin mb-4"/>
                  <div className="font-bold text-lg animate-pulse tracking-wide">Processing Regulatory Nodes...</div>
                </motion.div>
              ) : (
                <motion.div key="results" initial="hidden" animate="show" variants={staggerContainer} className="pb-4">
                  
                  <motion.div variants={cardAnim} className="flex gap-2.5 mb-6 bg-white/60 p-3 border border-white/80 rounded-2xl shadow-sm backdrop-blur-md">
                    <div className="badge badge-critical px-3 py-1">{nCrit} Critical</div>
                    <div className="badge badge-moderate px-3 py-1">{nMod} Moderate</div>
                    <div className="badge badge-low px-3 py-1">{nLow} Low</div>
                    <div className="ml-auto text-xs font-bold text-slate-500 self-center tracking-wide pr-2">
                      {changes.length} changes &bull; {impacts.length} policies &bull; {amends.length} drafts
                    </div>
                  </motion.div>

                  {changes.length === 0 ? (
                    <motion.div variants={cardAnim} className="bg-gradient-to-r from-emerald-50 to-teal-50 text-emerald-800 p-5 rounded-2xl border border-emerald-100 shadow-sm flex items-center gap-3 font-bold tracking-wide">
                      <CheckCircle2 size={24} className="text-emerald-500"/> No regulatory changes found. Systems aligned.
                    </motion.div>
                  ) : (
                    <div className="flex flex-col gap-3.5">
                      {changes.map((c, i) => (
                        <motion.div variants={cardAnim} whileHover={{ scale: 1.01, zIndex: 10 }} key={i} onClick={() => setSelectedIdx(i)}
                             className={`p-4 border rounded-2xl cursor-pointer transition-all duration-200
                                         ${selectedIdx === i ? 'border-blue-400 bg-blue-50/50 shadow-[0_4px_20px_-5px_rgba(59,130,246,0.25)] ring-2 ring-blue-500/20' : 'glass-card hover:border-slate-300 hover:shadow-md'}`}>
                          <div className="flex items-start justify-between mb-3">
                            <div>
                              <div className="font-bold text-slate-900 text-[16px] tracking-tight leading-tight mb-1">{c.section_id}</div>
                              <div className="text-xs text-slate-500 font-semibold tracking-wide flex items-center gap-1.5">
                                <span className="bg-slate-100 px-2 py-0.5 rounded-md">Page {(c.page_number === '?' ? '-' : c.page_number) || i+1}</span> 
                                <span className="text-slate-300">&bull;</span> 
                                <span className="text-blue-600/80">Match: {(c.similarity_score * 100).toFixed(0)}%</span>
                              </div>
                            </div>
                            <div className={`badge badge-${(c.severity || 'low').toLowerCase()}`}>{c.severity || 'LOW'}</div>
                          </div>
                          <div className="text-[13.5px] text-slate-600 line-clamp-2 leading-relaxed font-medium">
                            {clean(c.new_text)}
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* RIGHT COLUMN - Impact */}
        <motion.div variants={panelAnim} initial="hidden" animate="show" transition={{ delay: 0.2 }} className="flex-[1.5] flex flex-col min-w-[340px]">
          <div className="glass-panel flex-1 p-6 overflow-y-auto">
            <div className="section-label flex items-center gap-1.5"><AlertTriangle size={14} className="text-amber-500"/> Action & Impact</div>

            {!results || !selCard ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 opacity-60">
                <ArrowRight size={32} className="mb-4"/>
                <div className="text-sm font-medium text-center px-6 leading-relaxed">Select a change card from the feed to view policy impacts and amendments.</div>
              </div>
            ) : (
              <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} key={selectedIdx} className="flex flex-col h-full">
                
                <div className="bg-white/60 p-4 rounded-2xl border border-white/80 shadow-sm mb-6 backdrop-blur-md">
                  <div className="font-bold text-slate-800 text-lg tracking-tight leading-tight mb-2">{selCard.section_id}</div>
                  <div className="flex items-center gap-2">
                    <div className={`badge badge-${(selCard.severity || 'low').toLowerCase()}`}>{selCard.severity || 'LOW'}</div>
                    <span className="text-xs text-slate-500 font-bold bg-slate-100 px-2 py-0.5 rounded-md">Sim: {(selCard.similarity_score * 100).toFixed(1)}%</span>
                  </div>
                </div>

                <div className="section-label"><span className="text-indigo-500 mr-1">🏛️</span> Impacted Internal Policies</div>
                {sImpacts.length === 0 ? (
                  <div className="text-xs text-slate-500 font-medium italic mb-6 p-4 bg-slate-50/50 rounded-xl border border-slate-100">No internal policies matched this regulatory change.</div>
                ) : (
                  <div className="flex flex-col gap-2.5 mb-7">
                    {sImpacts.slice(0,3).map((imp, i) => (
                      <motion.div whileHover={{ scale: 1.02 }} key={i} className="flex gap-3 p-3.5 glass-card shadow-sm">
                        <div className="w-2.5 h-2.5 mt-1 rounded-full bg-red-500 shrink-0 shadow-[0_0_8px_rgba(239,68,68,0.5)]"/>
                        <div>
                          <div className="font-bold text-[13px] text-slate-900 leading-tight tracking-wide mb-1.5">{imp.policy_name}</div>
                          <div className="text-[11px] font-medium text-slate-500 leading-relaxed line-clamp-3">{clean(imp.matched_text)}</div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}

                <div className="section-label"><span className="text-amber-500 mr-1">✏️</span> Proposed AI Amendment</div>
                {sAmends.length === 0 ? (
                  <div className="text-xs text-slate-500 font-medium italic mb-4 p-4 bg-slate-50/50 rounded-xl border border-slate-100">No drafts prepared for this section internally.</div>
                ) : (
                  <div className="flex flex-col gap-2 mb-auto">
                    <div className="text-xs font-black tracking-wide text-slate-800 ml-1">{sAmends[0].policy_name}</div>
                    <textarea 
                      className="w-full h-28 p-3 text-sm font-medium border border-slate-200/80 rounded-xl focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 text-slate-700 bg-white shadow-inner resize-none transition-all"
                      defaultValue={clean(sAmends[0].proposed_text)}
                    />
                    <div className="text-[11.5px] font-medium text-amber-800 bg-gradient-to-r from-amber-50 to-amber-100/50 p-3 rounded-xl border border-amber-200/60 flex items-start gap-2 mt-2 shadow-sm">
                      <span className="mt-0.5 text-base">💡</span> <span className="leading-relaxed">{sAmends[0].justification}</span>
                    </div>
                  </div>
                )}

                <div className="mt-7 border-t border-slate-200/60 pt-5">
                  <div className="section-label flex items-center gap-1.5"><FileDown size={14} className="text-slate-500"/> Export Report</div>
                  <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }} onClick={downloadReport} 
                    className="w-full flex justify-center items-center gap-2 bg-slate-900 border border-slate-800 text-white font-bold tracking-wide text-sm py-3 rounded-xl hover:bg-slate-800 transition-colors shadow-lg shadow-slate-900/20">
                    Generate Professional PDF
                  </motion.button>
                </div>
              </motion.div>
            )}
          </div>
        </motion.div>

      </div>
    </div>
  );
}
