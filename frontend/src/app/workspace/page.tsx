"use client";

import { useState, useEffect, useCallback, useRef, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Fingerprint, Play, Square, FileSearch, Database, BookOpen, AlertTriangle, CheckCircle } from "lucide-react";
import { useWorkspaceStore } from "@/store/workspace";
import { ComparisonView } from "@/components/ComparisonView";
import { getCombinedShortlist, getRankingMetadata } from "@/lib/api";

function WorkspaceContent() {
  const searchParams = useSearchParams();
  const invId = searchParams.get("id");

  const {
    candidates,
    selectedCandidate,
    comparisonCandidate,
    setCandidates,
    setSelectedCandidate,
    setComparisonCandidate,
    setRankingMetadata,
    clearComparison,
  } = useWorkspaceStore();

  const [demoRunning, setDemoRunning] = useState(false);
  const [demoStep, setDemoStep] = useState(0);
  const demoTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const rankedCandidates = candidates.filter((c) => c.rank <= 100).sort((a, b) => a.rank - b.rank);
  const unrankedCandidates = candidates.filter((c) => c.rank > 100).sort((a, b) => b.rank - a.rank);
  const displayCandidates = [...rankedCandidates, ...unrankedCandidates];

  // Load data from backend on mount
  useEffect(() => {
    async function loadData() {
      const metadata = await getRankingMetadata();
      setRankingMetadata(metadata);
      
      const realCandidates = await getCombinedShortlist(invId || undefined);
      setCandidates(realCandidates);
    }
    if (candidates.length === 0) {
      loadData();
    }
  }, [invId, candidates.length, setCandidates, setRankingMetadata]);

  // Set initial selected candidate if none
  useEffect(() => {
    if (!selectedCandidate && displayCandidates.length > 0) {
      setSelectedCandidate(displayCandidates[0]);
    }
  }, [displayCandidates, selectedCandidate, setSelectedCandidate]);

  const startDemo = useCallback(() => {
    setDemoRunning(true);
    setDemoStep(0);

    const keywordTrap = unrankedCandidates.find(c => c.id === "CAND_0000004") || unrankedCandidates[0];
    const searchEngineer = rankedCandidates.find(c => c.id === "CAND_0005260") || rankedCandidates[0];
    const atsWinner = unrankedCandidates.find(c => c.id === "CAND_0000014") || unrankedCandidates[1];

    setSelectedCandidate(keywordTrap);
    clearComparison();

    demoTimerRef.current = setTimeout(() => {
      setDemoStep(1);
      setSelectedCandidate(searchEngineer);

      demoTimerRef.current = setTimeout(() => {
        setDemoStep(2);
        setComparisonCandidate(atsWinner);

        demoTimerRef.current = setTimeout(() => {
          setDemoStep(3);
          clearComparison();
          setSelectedCandidate(rankedCandidates[0]);

          demoTimerRef.current = setTimeout(() => {
            setDemoRunning(false);
            setDemoStep(0);
          }, 10000);
        }, 30000);
      }, 15000);
    }, 15000);
  }, [rankedCandidates, unrankedCandidates, setSelectedCandidate, setComparisonCandidate, clearComparison]);

  const stopDemo = useCallback(() => {
    setDemoRunning(false);
    setDemoStep(0);
    if (demoTimerRef.current) {
      clearTimeout(demoTimerRef.current);
      demoTimerRef.current = null;
    }
    clearComparison();
  }, [clearComparison]);

  useEffect(() => {
    return () => {
      if (demoTimerRef.current) clearTimeout(demoTimerRef.current);
    };
  }, []);

  return (
    <div className="h-screen bg-[#0A0A0A] text-[#e5e2e1] font-sans selection:bg-white selection:text-black flex flex-col overflow-hidden">
      
      {/* Top Navigation */}
      <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-4 md:px-10 h-14 bg-[#141313] border-b border-[#262626]">
        <div className="flex items-center gap-3">
          <Fingerprint className="text-white w-5 h-5" />
          <span className="text-base font-semibold text-white tracking-tight">
            Case Study: {selectedCandidate?.id || "None"}
          </span>
        </div>
        <div className="hidden md:flex items-center gap-6">
          <Link className="text-[#c4c7c8] text-xs hover:bg-[#353434] transition-colors px-3 py-1 rounded" href="/new">New Investigation</Link>
          <Link className="text-white font-bold text-xs bg-[#353434] px-3 py-1 rounded" href="/workspace">Workspace</Link>
          <Link className="text-[#c4c7c8] text-xs hover:bg-[#353434] transition-colors px-3 py-1 rounded" href="/analytics">Analytics</Link>
          <Link className="text-[#c4c7c8] text-xs hover:bg-[#353434] transition-colors px-3 py-1 rounded" href="/reports">Reports</Link>
        </div>
        <div className="flex items-center gap-4">
          {!demoRunning ? (
            <button
              onClick={startDemo}
              className="flex items-center gap-2 px-3 py-1.5 text-[10px] font-bold tracking-wider uppercase rounded border border-[#22C55E]/30 bg-[#22C55E]/10 text-[#22C55E] hover:bg-[#22C55E]/20 transition-all"
            >
              <Play className="w-3 h-3" />
              Demo Sequence
            </button>
          ) : (
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-[#F59E0B]/10 border border-[#F59E0B]/20">
                <motion.div
                  animate={{ opacity: [1, 0.3, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="w-1.5 h-1.5 rounded-full bg-[#F59E0B]"
                />
                <span className="text-[10px] font-mono text-[#F59E0B] tracking-wider">
                  DEMO RUNNING
                  {demoStep === 0 && " — 1. Keyword Trap"}
                  {demoStep === 1 && " — 2. True Search Engineer"}
                  {demoStep === 2 && " — 3. Head to Head"}
                  {demoStep === 3 && " — 4. Final Shortlist"}
                </span>
              </div>
              <button
                onClick={stopDemo}
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-[10px] font-bold tracking-wider uppercase rounded border border-[#EF4444]/30 bg-[#EF4444]/10 text-[#EF4444] hover:bg-[#EF4444]/20 transition-all"
              >
                <Square className="w-3 h-3" />
                Stop
              </button>
            </div>
          )}
        </div>
      </nav>

      {/* Secondary Nav: Investigation Summary */}
      <div className="fixed top-14 w-full z-40 bg-[#0A0A0A] border-b border-[#262626] px-4 md:px-10 h-10 flex items-center justify-between text-[10px] font-mono text-[#c4c7c8] uppercase tracking-wider">
        <div className="flex items-center gap-6">
          <span className="font-bold text-white">INV #2026-001</span>
          <span><span className="text-[#A3A3A3]">JD:</span> Senior Search Engineer</span>
        </div>
        <div className="flex items-center gap-6">
          <span><span className="text-[#A3A3A3]">Analyzed:</span> 100,000</span>
          <span><span className="text-[#A3A3A3]">Retrieved:</span> 5,000</span>
          <span><span className="text-[#A3A3A3]">Ranked:</span> 1,000</span>
          <span className="text-[#22C55E] font-bold">Shortlisted: 100</span>
        </div>
      </div>

      {/* Main Workspace */}
      <main className="pt-24 h-screen flex flex-col md:flex-row overflow-hidden">
        
        {/* Column 1: Candidate Queue */}
        <aside className="w-full md:w-[280px] shrink-0 bg-[#111111] border-r border-[#262626] flex flex-col overflow-hidden">
          
          {/* Shortlisted Section */}
          <div className="p-4 border-b border-[#262626] flex justify-between items-center bg-[#141313]">
            <span className="text-xs text-[#c4c7c8] uppercase tracking-widest font-semibold flex items-center gap-2">
              <CheckCircle className="w-3 h-3 text-[#22C55E]" /> Shortlisted
            </span>
            <span className="bg-[#353434] px-2 py-0.5 rounded text-[10px] font-mono">{rankedCandidates.length}</span>
          </div>
          <div className="flex-1 overflow-y-auto p-2 gap-2 flex flex-col scrollbar-thin scrollbar-thumb-[#262626]">
            {rankedCandidates.map(candidate => {
              const isSelected = selectedCandidate?.id === candidate.id;
              return (
                <div
                  key={candidate.id}
                  onClick={() => setSelectedCandidate(candidate)}
                  className={`w-full p-3 border rounded-lg cursor-pointer transition-all ${
                    isSelected ? "bg-[#171717] border-[#404040]" : "border-transparent hover:border-[#262626] hover:bg-[#141313]"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={`font-mono text-[10px] ${isSelected ? "text-white" : "text-[#c4c7c8]"} opacity-60`}>
                      ID: {candidate.id.split('_')[1]}
                    </span>
                    {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-[#22C55E]"></span>}
                  </div>
                  <h3 className={`text-sm font-semibold truncate ${isSelected ? "text-white" : "text-[#c4c7c8]"}`}>
                    {candidate.name}
                  </h3>
                  <p className="text-[11px] text-[#8e9192] mt-1">{candidate.title}</p>
                </div>
              );
            })}
          </div>

          {/* Rejected Section */}
          <div className="p-4 border-y border-[#262626] flex justify-between items-center bg-[#141313]">
            <span className="text-xs text-[#EF4444] uppercase tracking-widest font-semibold flex items-center gap-2">
              <AlertTriangle className="w-3 h-3" /> Rejected Cases
            </span>
            <span className="bg-[#EF4444]/10 text-[#EF4444] px-2 py-0.5 rounded text-[10px] font-mono">{unrankedCandidates.length}</span>
          </div>
          <div className="h-[250px] overflow-y-auto p-2 gap-2 flex flex-col scrollbar-thin scrollbar-thumb-[#262626] bg-[#0A0A0A]">
            {unrankedCandidates.map(candidate => {
              const isSelected = selectedCandidate?.id === candidate.id;
              return (
                <div
                  key={candidate.id}
                  onClick={() => setSelectedCandidate(candidate)}
                  className={`w-full p-3 border rounded-lg cursor-pointer transition-all ${
                    isSelected ? "bg-[#171717] border-[#EF4444]/50" : "border-[#262626] bg-[#111111] hover:border-[#404040]"
                  }`}
                >
                  <h3 className={`text-sm font-semibold truncate ${isSelected ? "text-white" : "text-[#c4c7c8]"}`}>
                    {candidate.name}
                  </h3>
                  <p className="text-[10px] text-[#EF4444] mt-1 line-clamp-2 leading-snug">
                    Rejected: {candidate.decisionPath.penalizedBecause[0] || 'Generic keyword profile'}
                  </p>
                </div>
              );
            })}
          </div>
        </aside>

        {/* Column 2: Evidence Review */}
        <section className="flex-1 overflow-y-auto bg-[#0A0A0A] p-4 md:p-8 scrollbar-thin scrollbar-thumb-[#262626]">
          {selectedCandidate ? (
            <div className="max-w-[800px] mx-auto">
              <header className="mb-10">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`${selectedCandidate.rank > 100 ? 'bg-[#EF4444]/20 text-[#EF4444]' : 'bg-[#22C55E]/20 text-[#22C55E]'} font-mono text-[10px] px-2 py-0.5 rounded uppercase font-bold tracking-tighter`}>
                    {selectedCandidate.rank > 100 ? "Investigation High Priority" : "Verified Profile"}
                  </span>
                </div>
                <h1 className="text-3xl font-semibold text-white mb-2">Evidence Review</h1>
                <p className="text-base text-[#c4c7c8]">
                  Comparative analysis of self-reported claims against verified repository data and third-party audits.
                </p>
              </header>

              <div className="space-y-6">
                
                {/* Retrieval Evidence */}
                <div className="border border-[#262626] bg-[#111111] rounded-lg overflow-hidden transition-colors hover:border-[#404040]">
                  <div className="p-4 border-b border-[#262626] flex items-center justify-between bg-[#171717]">
                    <span className="text-xs font-bold text-white flex items-center gap-2 uppercase tracking-widest">
                      Claim 01: Retrieval Architecture
                    </span>
                    <span className="text-[10px] font-mono text-[#c4c7c8]">Source: GitHub / Audit</span>
                  </div>
                  <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#262626]">
                    <div className="p-4">
                      <h4 className="text-[10px] text-[#c4c7c8] mb-2 uppercase font-semibold">Self-Reported Focus</h4>
                      <div className="space-y-2">
                        {selectedCandidate.whyHere.slice(0, 2).map((item, i) => (
                          <p key={i} className="text-sm text-white">"{item}"</p>
                        ))}
                      </div>
                    </div>
                    <div className="p-4 bg-[#141313]">
                      <h4 className={`text-[10px] mb-2 uppercase font-semibold flex items-center gap-1 ${selectedCandidate.rank > 100 ? 'text-[#EF4444]' : 'text-[#22C55E]'}`}>
                        {selectedCandidate.rank > 100 ? 'Audit Finding (Warning)' : 'Verification (Passed)'}
                      </h4>
                      <div className="space-y-2">
                        {selectedCandidate.evidence.retrieval.map((item, i) => (
                          <p key={i} className="text-sm text-[#c4c7c8]">{item}</p>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Ranking Evidence */}
                <div className="border border-[#262626] bg-[#111111] rounded-lg overflow-hidden transition-colors hover:border-[#404040]">
                  <div className="p-4 border-b border-[#262626] flex items-center justify-between bg-[#171717]">
                    <span className="text-xs font-bold text-white flex items-center gap-2 uppercase tracking-widest">
                      Claim 02: Ranking & Production ML
                    </span>
                    <span className="text-[10px] font-mono text-[#c4c7c8]">Source: Technical Interview</span>
                  </div>
                  <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#262626]">
                    <div className="p-4">
                      <h4 className="text-[10px] text-[#c4c7c8] mb-2 uppercase font-semibold">Self-Reported Claim</h4>
                      <p className="text-sm text-white">Production scaling and ranking model deployment.</p>
                    </div>
                    <div className="p-4 bg-[#141313]">
                      <h4 className={`text-[10px] mb-2 uppercase font-semibold flex items-center gap-1 ${selectedCandidate.rank > 100 ? 'text-[#EF4444]' : 'text-[#22C55E]'}`}>
                        {selectedCandidate.rank > 100 ? 'Audit Finding (Failed)' : 'Verification (Passed)'}
                      </h4>
                      <div className="space-y-2">
                        {selectedCandidate.evidence.ranking.map((item, i) => (
                          <p key={i} className="text-sm text-[#c4c7c8]">{item}</p>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Score Decomposition */}
                <div className="border border-[#262626] bg-[#111111] rounded-lg overflow-hidden transition-colors hover:border-[#404040]">
                  <div className="p-4 border-b border-[#262626] flex items-center justify-between bg-[#171717]">
                    <span className="text-xs font-bold text-white flex items-center gap-2 uppercase tracking-widest">
                      Mathematical Ranking Breakdown
                    </span>
                    <span className="text-[10px] font-mono text-[#c4c7c8]">Final Score: {selectedCandidate.finalScores?.final.toFixed(3) || 0}</span>
                  </div>
                  <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-[#141313] p-3 rounded border border-[#262626]">
                      <div className="text-[10px] text-[#A3A3A3] uppercase tracking-wider mb-1">Title Affinity</div>
                      <div className="text-sm font-mono text-white">{selectedCandidate.finalScores?.titleAffinity.toFixed(3) || 0}</div>
                    </div>
                    <div className="bg-[#141313] p-3 rounded border border-[#262626]">
                      <div className="text-[10px] text-[#A3A3A3] uppercase tracking-wider mb-1">Skill Affinity</div>
                      <div className="text-sm font-mono text-white">{selectedCandidate.finalScores?.skillAffinity.toFixed(3) || 0}</div>
                    </div>
                    <div className="bg-[#141313] p-3 rounded border border-[#262626]">
                      <div className="text-[10px] text-[#A3A3A3] uppercase tracking-wider mb-1">Career Affinity</div>
                      <div className="text-sm font-mono text-white">{selectedCandidate.finalScores?.careerAffinity.toFixed(3) || 0}</div>
                    </div>
                    <div className="bg-[#141313] p-3 rounded border border-[#262626]">
                      <div className="text-[10px] text-[#A3A3A3] uppercase tracking-wider mb-1">Semantic Sim</div>
                      <div className="text-sm font-mono text-white">{selectedCandidate.finalScores?.semantic.toFixed(3) || 0}</div>
                    </div>
                    <div className="bg-[#141313] p-3 rounded border border-[#262626]">
                      <div className="text-[10px] text-[#A3A3A3] uppercase tracking-wider mb-1">BM25 Score</div>
                      <div className="text-sm font-mono text-white">{selectedCandidate.finalScores?.bm25.toFixed(3) || 0}</div>
                    </div>
                    <div className="bg-[#141313] p-3 rounded border border-[#262626]">
                      <div className="text-[10px] text-[#A3A3A3] uppercase tracking-wider mb-1">Quality Score</div>
                      <div className="text-sm font-mono text-white">{selectedCandidate.finalScores?.quality.toFixed(3) || 0}</div>
                    </div>
                    <div className={`bg-[#141313] p-3 rounded border ${(selectedCandidate.finalScores?.penalties || 0) < 0 ? 'border-[#EF4444]/30' : 'border-[#262626]'}`}>
                      <div className={`text-[10px] ${(selectedCandidate.finalScores?.penalties || 0) < 0 ? 'text-[#EF4444]' : 'text-[#A3A3A3]'} uppercase tracking-wider mb-1`}>Penalties</div>
                      <div className={`text-sm font-mono ${(selectedCandidate.finalScores?.penalties || 0) < 0 ? 'text-[#EF4444]' : 'text-white'}`}>{selectedCandidate.finalScores?.penalties.toFixed(3) || 0}</div>
                    </div>
                  </div>
                </div>

                {/* Narrative / Career */}
                <div className="border border-[#262626] bg-[#111111] rounded-lg overflow-hidden transition-colors hover:border-[#404040]">
                  <div className="p-4 border-b border-[#262626] flex items-center justify-between bg-[#171717]">
                    <span className="text-xs font-bold text-white flex items-center gap-2 uppercase tracking-widest">
                      Trajectory Analysis
                    </span>
                  </div>
                  <div className="p-4">
                    <p className="text-sm text-[#c4c7c8] whitespace-pre-wrap">{selectedCandidate.narrative}</p>
                  </div>
                </div>

              </div>
            </div>
          ) : (
            <div className="flex h-full items-center justify-center text-[#c4c7c8]">
              Select a case to begin investigation.
            </div>
          )}
        </section>

        {/* Column 3: Summary & Verdict */}
        <aside className="w-full md:w-[320px] shrink-0 bg-[#111111] border-l border-[#262626] flex flex-col p-6 gap-8 overflow-y-auto">
          {selectedCandidate && (
            <>
              <div>
                <h3 className="text-xs text-[#c4c7c8] uppercase tracking-widest mb-4 font-semibold">Decision Summary</h3>
                <div className="space-y-4">
                  {/* ATS Assessment */}
                  <div className="p-4 border border-[#262626] bg-[#171717] rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-bold uppercase tracking-widest">ATS ASSESSMENT</span>
                      <span className={`font-mono text-[11px] uppercase ${selectedCandidate.rank > 100 ? 'text-[#22C55E]' : 'text-[#EF4444]'}`}>
                        {selectedCandidate.rank > 100 ? 'ACCEPTED' : 'REJECTED'}
                      </span>
                    </div>
                    <p className="text-sm text-[#c4c7c8]">
                      {selectedCandidate.rank > 100 
                        ? `Automated scoring passed based on heavy keyword matches for generic ML concepts.` 
                        : `Automated scoring failed. Keyword density for generic skills did not meet threshold.`}
                    </p>
                  </div>
                  
                  {/* Recruiter Review */}
                  <div className={`p-4 border bg-[#171717] rounded-lg ${selectedCandidate.rank > 100 ? 'border-[#EF4444]/30' : 'border-[#22C55E]/30'}`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-bold uppercase tracking-widest text-white">RECRUITER REVIEW</span>
                      <span className={`font-mono text-[11px] uppercase ${selectedCandidate.rank > 100 ? 'text-[#EF4444]' : 'text-white'}`}>
                        OVERTURNED
                      </span>
                    </div>
                    <p className="text-sm text-[#c4c7c8]">
                      {selectedCandidate.decisionPath.penalizedBecause.join('. ')}
                      {selectedCandidate.rank <= 100 && " " + selectedCandidate.decisionPath.rankedBecause.join('. ')}
                    </p>
                  </div>
                </div>
              </div>

              {/* Final Verdict */}
              <div className="mt-auto pt-8 border-t border-[#262626]">
                <h3 className="text-xs text-[#c4c7c8] uppercase tracking-widest mb-6 font-semibold">Final Determination</h3>
                <div className={`flex flex-col items-center justify-center p-8 rounded-lg shadow-2xl relative overflow-hidden ${selectedCandidate.rank > 100 ? 'bg-[#141313] border border-[#EF4444]/30' : 'bg-white text-black'}`}>
                  <span className={`font-mono text-[10px] uppercase font-bold mb-2 ${selectedCandidate.rank > 100 ? 'text-[#EF4444]' : 'text-black/60'}`}>
                    Hiring Board Final Call
                  </span>
                  
                  <div className={`text-2xl font-extrabold uppercase tracking-tighter transform -rotate-2 border-2 px-4 py-1 ${selectedCandidate.rank > 100 ? 'text-[#EF4444] border-[#EF4444]' : 'text-black border-black'}`}>
                    {selectedCandidate.rank > 100 ? 'REJECTED' : 'RECOMMENDED'}
                  </div>
                  
                  <p className={`text-[10px] mt-4 italic ${selectedCandidate.rank > 100 ? 'text-[#EF4444]/70' : 'text-black/70'}`}>
                    Signed: Chief Investigation Officer
                  </p>
                </div>
                
                <div className="mt-6 space-y-2">
                  <button className="w-full py-2 bg-white text-black text-xs font-bold rounded hover:opacity-90 transition-opacity uppercase tracking-widest">
                    {selectedCandidate.rank > 100 ? 'Close Case' : 'Generate Offer Docs'}
                  </button>
                  <button className="w-full py-2 border border-[#262626] text-white text-xs font-bold rounded hover:bg-[#171717] transition-colors uppercase tracking-widest">
                    Request Second Audit
                  </button>
                </div>
              </div>
            </>
          )}
        </aside>

      </main>

      {/* Comparison Overlay */}
      <AnimatePresence>
        {selectedCandidate && comparisonCandidate && (
          <ComparisonView
            candidateA={selectedCandidate}
            candidateB={comparisonCandidate}
            onClose={clearComparison}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default function WorkspacePage() {
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center text-white">Loading Workspace...</div>}>
      <WorkspaceContent />
    </Suspense>
  );
}
