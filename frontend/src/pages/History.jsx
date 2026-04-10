import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster, toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

export default function History() {
  const [circulars, setCirculars] = useState([]);
  const [selectedCirc, setSelectedCirc] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const [compareV1, setCompareV1] = useState(null);
  const [compareV2, setCompareV2] = useState(null);
  const [diffReport, setDiffReport] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/history/circulars");
      const data = await res.json();
      if (data.circulars) {
        setCirculars(data.circulars);
      }
    } catch (e) {
      toast.error("Failed to load timeline history.");
    } finally {
      setLoading(false);
    }
  };

  const runDiff = async () => {
    if (!selectedCirc || !compareV1 || !compareV2) return;
    setAnalyzing(true);
    setDiffReport(null);
    try {
      const res = await fetch(`http://localhost:8000/api/history/diff/${selectedCirc.circular_id}?v1=${compareV1}&v2=${compareV2}`);
      const data = await res.json();
      if (data.diff_report) {
         setDiffReport(data.diff_report);
         toast.success("Historical Diff computed!");
      } else {
         toast.error(data.message || "Failed to compute diff.");
      }
    } catch (e) {
      toast.error("Analysis server crashed.");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleVersionClick = (vnum) => {
    // Logic to select two versions for diff
    if (compareV1 === vnum) {
      setCompareV1(null);
    } else if (compareV2 === vnum) {
      setCompareV2(null);
    } else if (!compareV1) {
      setCompareV1(vnum);
    } else if (!compareV2) {
      setCompareV2(vnum);
    } else {
      setCompareV1(compareV2);
      setCompareV2(vnum);
    }
    setDiffReport(null);
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50 font-sans selection:bg-indigo-500/30">
      <Toaster position="bottom-right" theme="dark" />
      
      {/* Header */}
      <header className="h-20 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-xl flex items-center px-10 sticky top-0 z-40">
        <div className="flex items-center gap-6">
          <div onClick={() => navigate('/dashboard')} className="w-10 h-10 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center cursor-pointer hover:bg-white hover:text-black hover:border-white transition-all text-zinc-400">
             <span className="material-symbols-outlined text-[18px]">arrow_back</span>
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
              Version Timeline <span className="px-2 py-0.5 bg-zinc-800 text-[10px] uppercase font-semibold rounded text-zinc-300 tracking-widest">{circulars.length} Tracked Documents</span>
            </h1>
          </div>
        </div>
      </header>

      <main className="p-10 max-w-7xl mx-auto grid grid-cols-12 gap-10">
        {/* Left Side: Circular Selection */}
        <div className="col-span-12 lg:col-span-4 space-y-4">
          <h3 className="text-xs uppercase tracking-widest text-zinc-500 font-bold mb-6">Regulator Databases</h3>
          {loading ? (
             <div className="animate-pulse flex gap-3 h-20 bg-zinc-900/50 rounded-xl"></div>
          ) : circulars.map(c => (
            <div 
              key={c.circular_id} 
              onClick={() => {
                 setSelectedCirc(c);
                 setCompareV1(null); setCompareV2(null); setDiffReport(null);
              }}
              className={`p-5 rounded-xl border cursor-pointer transition-all ${selectedCirc?.circular_id === c.circular_id ? 'border-indigo-500/50 bg-indigo-500/5 shadow-[0_0_15px_rgba(99,102,241,0.1)]' : 'border-zinc-800 bg-zinc-900/40 hover:bg-zinc-800/60 hover:border-zinc-700'}`}
            >
               <div className="text-[10px] text-zinc-400 uppercase tracking-widest font-semibold mb-2">{c.source} Document</div>
               <div className="font-bold text-base truncate pr-4" title={c.circular_id}>{c.circular_id}</div>
               <div className="mt-4 flex items-center gap-2">
                 <span className="px-2 py-0.5 bg-white/10 text-white rounded text-[10px] font-bold">{c.versions.length} Versions</span>
               </div>
            </div>
          ))}
        </div>

        {/* Right Side: Timeline & Diff */}
        <div className="col-span-12 lg:col-span-8">
           {selectedCirc ? (
              <div className="glass-panel p-8 rounded-2xl border border-zinc-800/80 relative overflow-hidden bg-zinc-900/20">
                <h2 className="text-xl font-bold mb-8 flex flex-col gap-2">
                   <span>Lifecycle: {selectedCirc.circular_id}</span>
                   <span className="text-xs text-zinc-500 font-medium tracking-wide">Select up to two sequential versions to actively generate an AI Differential scan.</span>
                </h2>

                {/* Timeline Axis */}
                <div className="relative pl-6 border-l-2 border-zinc-800 space-y-12 mb-12">
                   {selectedCirc.versions.map((ver, idx) => (
                      <div key={idx} className="relative">
                         <div 
                            onClick={() => handleVersionClick(ver.version_number)}
                            className={`absolute -left-[33px] w-4 h-4 rounded-full border-4 cursor-pointer transition-colors z-10 
                                ${compareV1 === ver.version_number || compareV2 === ver.version_number ? 'bg-indigo-500 border-zinc-900 shadow-[0_0_10px_rgba(99,102,241,0.8)]' : 'bg-zinc-600 border-zinc-950 hover:bg-zinc-400'}`}
                         ></div>
                         <div className={`p-4 rounded-xl border transition-all ${compareV1 === ver.version_number || compareV2 === ver.version_number ? 'border-indigo-500/30 bg-indigo-500/5' : 'border-zinc-800/50 bg-zinc-900/30'}`}>
                           <div className="flex justify-between items-start">
                             <div className="flex items-center gap-3">
                               <span className="font-bold text-lg text-white">v{ver.version_number}</span>
                               <span className="text-[10px] px-2 py-0.5 bg-emerald-500/10 text-emerald-400 rounded border border-emerald-500/20 uppercase tracking-widest font-bold">Immutable Archive</span>
                             </div>
                             <span className="text-xs text-zinc-500 font-semibold">{new Date(ver.ingested_at).toLocaleString()}</span>
                           </div>
                         </div>
                      </div>
                   ))}
                </div>

                {compareV1 && compareV2 && !diffReport && (
                   <button 
                     onClick={runDiff} 
                     disabled={analyzing}
                     className="w-full py-4 rounded-xl bg-white text-black font-bold uppercase tracking-widest text-sm hover:bg-zinc-200 transition-all disabled:opacity-50 disabled:cursor-wait"
                   >
                     {analyzing ? 'Engaging Agents for Scanning...' : `Compare v${Math.min(compareV1, compareV2)} vs v${Math.max(compareV1, compareV2)}`}
                   </button>
                )}

                {diffReport && (
                   <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mt-8 border-t border-zinc-800 pt-8">
                     <h3 className="text-sm uppercase tracking-widest text-zinc-300 font-bold mb-6 flex items-center gap-2">
                       <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></span> Regulatory Divergence Report
                     </h3>
                     {diffReport.length === 0 ? (
                       <p className="text-zinc-500 font-medium">No significant regulatory changes discovered between these two archived versions.</p>
                     ) : (
                       <div className="space-y-4">
                         {diffReport.map((c, i) => (
                           <div key={i} className="p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl">
                             <div className="flex items-center justify-between mb-3">
                                <span className="text-[10px] px-2 py-0.5 bg-indigo-500/10 text-indigo-400 rounded uppercase tracking-widest font-bold">{c.section_id}</span>
                                <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider ${c.severity === 'CRITICAL' ? 'bg-red-500/10 text-red-500' : 'bg-amber-500/10 text-amber-500'}`}>{c.severity}</span>
                             </div>
                             <p className="text-sm text-zinc-300 leading-relaxed font-medium">{c.change_summary}</p>
                           </div>
                         ))}
                       </div>
                     )}
                   </motion.div>
                )}
              </div>
           ) : (
              <div className="h-full border border-zinc-800 border-dashed rounded-2xl flex flex-col items-center justify-center text-zinc-600 bg-zinc-900/10 p-10 text-center">
                 <span className="material-symbols-outlined text-4xl mb-4 opacity-50">timeline</span>
                 <p className="text-lg font-medium text-zinc-400 mb-2">Select a framework tracking ID.</p>
                 <p className="text-sm max-w-sm">Dive deep into the historical archival chain of any regulatory document. Select any two immutably logged versions to trigger an automated differential scan.</p>
              </div>
           )}
        </div>
      </main>
    </div>
  );
}
