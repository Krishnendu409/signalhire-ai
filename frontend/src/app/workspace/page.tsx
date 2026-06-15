"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Users, Search } from "lucide-react";
import { useWorkspaceStore } from "@/store/workspace";
import { ComparisonView } from "@/components/ComparisonView";
import { AppNav } from "@/components/AppNav";
import {
  fetchDefaultJobId,
  fetchLatestJobId,
  fetchWorkspaceData,
  pollWorkspaceData,
} from "@/lib/workspace-client";

function WorkspaceContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const invId = searchParams.get("id");
  const [searchQuery, setSearchQuery] = useState("");
  const [minScore, setMinScore] = useState<number>(0);
  const [minExperience, setMinExperience] = useState<number>(0);
  const [minDomainAuth, setMinDomainAuth] = useState<number>(0);
  const [reqAvailability, setReqAvailability] = useState<boolean>(false);
  const [queueTab, setQueueTab] = useState<"shortlist" | "rejected">("shortlist");
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const {
    candidates,
    selectedCandidate,
    comparisonCandidate,
    setCandidates,
    setSelectedCandidate,
    setComparisonCandidate,
    rankingMetadata,
    setRankingMetadata,
    clearComparison,
  } = useWorkspaceStore();

  const rankedCandidates = candidates
    .filter((c) => !c.isLowMatch)
    .sort((a, b) => a.rank - b.rank);
  const unrankedCandidates = candidates
    .filter((c) => c.isLowMatch)
    .sort((a, b) => a.rank - b.rank);
  const displayCandidates = candidates.filter(c => {
    if (searchQuery && !c.name.toLowerCase().includes(searchQuery.toLowerCase()) && !c.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    if (minScore > 0 && c.matchScore < minScore) return false;
    if (minExperience > 0 && (c.scores?.experience_affinity || 0) < minExperience) return false;
    if (minDomainAuth > 0 && (c.scores?.domain_authenticity || 0) < minDomainAuth) return false;
    if (reqAvailability && (c.scores?.availability_affinity || 0) < 1.0) return false;
    return true;
  });
  const queueCandidates = [...displayCandidates]
    .filter((c) => (queueTab === "shortlist" ? !c.isLowMatch : c.isLowMatch))
    .sort((a, b) => a.rank - b.rank);

  // Redirect to latest investigation when opened without an id
  useEffect(() => {
    if (invId) return;
    let active = true;
    setIsLoading(true);
    fetchLatestJobId().then((latestId) => {
      if (!active) return;
      if (latestId) {
        router.replace(`/workspace?id=${latestId}`);
      } else {
        setIsLoading(false);
        setLoadError("No investigations yet. Run one from New Investigation.");
      }
    }).catch(() => {
      if (active) {
        setIsLoading(false);
        setLoadError("Cannot reach backend. Start the API on port 8000.");
      }
    });
    return () => { active = false; };
  }, [invId, router]);

  // Load data from backend on mount or when invId changes
  useEffect(() => {
    if (!invId) return;

    let active = true;

    async function loadData() {
      setIsLoading(true);
      setLoadError(null);

      try {
        let data = await fetchWorkspaceData(invId);

        if (!active) return;

        if (data.status === 'not_found' || data.status === 'failed') {
          const fallbackId = await fetchDefaultJobId();
          if (fallbackId && fallbackId !== invId) {
            router.replace(`/workspace?id=${fallbackId}`);
            return;
          }
          setLoadError(data.error || 'Failed to load investigation.');
          setIsLoading(false);
          return;
        }

        if (data.status !== 'completed' || data.candidates.length === 0) {
          data = await pollWorkspaceData(invId);
          if (!active) return;
        }

        if (data.candidates.length === 0) {
          setLoadError('No ranked candidates yet. Run an investigation from New Investigation.');
          setCandidates([]);
          setIsLoading(false);
          return;
        }

        setCandidates(data.candidates);
        setRankingMetadata({
          totalEvaluated: data.metadata.totalEvaluated,
          retrieved: data.metadata.totalEvaluated,
          ranked: data.metadata.ranked,
          shortlisted: data.metadata.shortlisted,
          featuresExtracted: 22,
          model: 'SignalHire Rank v1',
          jdTitle: data.metadata.jdTitle,
          skills: {},
          signals: [],
          rejections: [],
        });
        setSelectedCandidate(null);
        setIsLoading(false);
      } catch (err) {
        if (!active) return;
        setLoadError(err instanceof Error ? err.message : 'Failed to load results');
        setIsLoading(false);
      }
    }

    loadData();

    return () => { active = false; };
  }, [invId, router, setCandidates, setRankingMetadata, setSelectedCandidate]);

  // Select first shortlisted candidate by default
  useEffect(() => {
    if (!selectedCandidate && rankedCandidates.length > 0) {
      setSelectedCandidate(rankedCandidates[0]);
    }
  }, [rankedCandidates, selectedCandidate, setSelectedCandidate]);

  return (
    <div className="h-screen bg-[#0A0A0A] text-[#e5e2e1] font-sans selection:bg-white selection:text-black flex flex-col overflow-hidden">
      
      <AppNav active="workspace" />

      {/* Context bar */}
      <div className="fixed top-14 w-full z-40 bg-[#0A0A0A] border-b border-[#262626] px-4 md:px-10 h-10 flex items-center justify-between text-[10px] font-mono text-[#c4c7c8] uppercase tracking-wider">
        <div className="flex items-center gap-6 min-w-0">
          <span className="font-bold text-white shrink-0">Active search</span>
          <span className="truncate"><span className="text-[#A3A3A3]">Role:</span> {rankingMetadata?.jdTitle || "Loading…"}</span>
        </div>
        <div className="flex items-center gap-4 md:gap-6 shrink-0">
          <span><span className="text-[#A3A3A3]">Pool:</span> {rankingMetadata?.totalEvaluated?.toLocaleString() || "--"}</span>
          <span><span className="text-[#A3A3A3]">Ranked:</span> {rankingMetadata?.ranked?.toLocaleString() || "--"}</span>
          <span className="text-[#22C55E] font-bold">Shortlisted: {rankingMetadata?.shortlisted?.toLocaleString() || "--"}</span>
        </div>
      </div>

      {/* Main Workspace */}
      <main className="pt-24 h-screen flex flex-col md:flex-row overflow-hidden">
        {(isLoading || loadError) && (
          <div className="absolute top-24 left-0 right-0 z-30 px-4 md:px-10 py-3 bg-[#171717] border-b border-[#262626] text-xs text-[#c4c7c8] flex items-center justify-between gap-4">
            {loadError ? (
              <>
                <span className="text-[#EF4444]">{loadError}</span>
                <Link href="/new" className="text-white bg-[#353434] px-3 py-1 rounded shrink-0">New Investigation</Link>
              </>
            ) : (
              <span className="flex items-center gap-2">
                <Loader2 className="w-3 h-3 animate-spin" />
                Loading ranking results{invId ? ` for ${invId.slice(0, 8)}…` : ""}…
              </span>
            )}
          </div>
        )}
        
        {/* Column 1: Candidate Queue */}
        <aside className="w-full md:w-80 bg-[#0A0A0A] border-r border-[#262626] flex flex-col h-full shrink-0">
          <div className="p-4 border-b border-[#262626] flex-shrink-0">
            <h2 className="text-xs font-bold text-white uppercase tracking-widest flex items-center gap-2 mb-3">
              <Users className="w-4 h-4" />
              Candidates
            </h2>
            <div className="flex gap-2 text-[10px] uppercase font-mono mb-3">
              <button
                onClick={() => setQueueTab("shortlist")}
                className={`flex-1 py-1 rounded font-bold transition-colors ${queueTab === "shortlist" ? "bg-white text-black" : "text-[#A3A3A3] hover:text-white"}`}
              >
                Shortlist ({rankedCandidates.length})
              </button>
              <button
                onClick={() => setQueueTab("rejected")}
                className={`flex-1 py-1 rounded font-bold transition-colors ${queueTab === "rejected" ? "bg-[#EF4444] text-white" : "text-[#A3A3A3] hover:text-white"}`}
              >
                Rejected ({unrankedCandidates.length})
              </button>
            </div>
            
            {/* Filters */}
            <div className="space-y-2">
              <div className="relative">
                <Search className="w-3 h-3 absolute left-2 top-2 text-[#A3A3A3]" />
                <input 
                  type="text" 
                  placeholder="Search by name or title..." 
                  className="w-full bg-[#141313] border border-[#262626] rounded text-xs px-7 py-1.5 text-white placeholder:text-[#A3A3A3] focus:outline-none focus:border-[#22C55E]"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[#A3A3A3]">Min Score: {minScore}%</span>
                <input 
                  type="range" 
                  min="0" max="100" 
                  className="w-24 accent-[#22C55E]"
                  value={minScore}
                  onChange={(e) => setMinScore(parseInt(e.target.value))}
                />
              </div>
              <div className="flex items-center justify-between mt-2">
                <span className="text-[10px] text-[#A3A3A3]">Min Experience: {minExperience.toFixed(1)}</span>
                <input 
                  type="range" 
                  min="0" max="2" step="0.1"
                  className="w-24 accent-[#22C55E]"
                  value={minExperience}
                  onChange={(e) => setMinExperience(parseFloat(e.target.value))}
                />
              </div>
              <div className="flex items-center justify-between mt-2">
                <span className="text-[10px] text-[#A3A3A3]">Domain Auth: {minDomainAuth.toFixed(1)}</span>
                <input 
                  type="range" 
                  min="0" max="2" step="0.1"
                  className="w-24 accent-[#22C55E]"
                  value={minDomainAuth}
                  onChange={(e) => setMinDomainAuth(parseFloat(e.target.value))}
                />
              </div>
              <div className="flex items-center justify-between mt-2">
                <span className="text-[10px] text-[#A3A3A3]">Req Availability</span>
                <input 
                  type="checkbox"
                  className="accent-[#22C55E]"
                  checked={reqAvailability}
                  onChange={(e) => setReqAvailability(e.target.checked)}
                />
              </div>
            </div>
          </div>
          <div className="flex-1 overflow-y-auto p-2 gap-2 flex flex-col scrollbar-thin scrollbar-thumb-[#262626]">
            {queueCandidates.length === 0 && !isLoading && (
              <p className="text-xs text-[#A3A3A3] p-3 text-center">
                {invId ? "No candidates yet. Run an investigation from New Investigation." : "Loading latest investigation…"}
              </p>
            )}
            {queueCandidates.map(candidate => {
              const isSelected = selectedCandidate?.id === candidate.id;
              const scoreColor = candidate.isLowMatch
                ? "text-[#EF4444] bg-[#EF4444]/10"
                : candidate.matchScore >= 70
                  ? "text-[#22C55E] bg-[#22C55E]/10"
                  : "text-[#F59E0B] bg-[#F59E0B]/10";
              return (
                <div
                  key={candidate.id}
                  onClick={() => setSelectedCandidate(candidate)}
                  className={`w-full p-3 border rounded-lg cursor-pointer transition-all ${
                    isSelected ? "bg-[#171717] border-[#404040]" : "border-transparent hover:border-[#262626] hover:bg-[#141313]"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={`font-mono text-[10px] px-1.5 py-0.5 rounded font-bold ${scoreColor}`}>
                      {candidate.matchScore}%
                    </span>
                    <div className="flex items-center gap-2">
                      {!isSelected && selectedCandidate && queueTab === "shortlist" && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setComparisonCandidate(candidate);
                          }}
                          className="text-[9px] font-bold bg-[#353434] px-1.5 py-0.5 rounded text-[#A3A3A3] hover:text-white hover:bg-[#404040] transition-colors"
                        >
                          Compare
                        </button>
                      )}
                      {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-[#22C55E]"></span>}
                    </div>
                  </div>
                  <h3 className={`text-sm font-semibold truncate ${isSelected ? "text-white" : "text-[#c4c7c8]"}`}>
                    {candidate.name}
                  </h3>
                  <p className="text-[11px] text-[#8e9192] mt-1 truncate">{candidate.title}</p>
                  <p className="text-[10px] text-[#A3A3A3] mt-1 font-mono">
                    Rank #{candidate.rank} · {candidate.company}
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
                  <span className={`${selectedCandidate.isLowMatch ? 'bg-[#EF4444]/20 text-[#EF4444]' : 'bg-[#22C55E]/20 text-[#22C55E]'} font-mono text-[10px] px-2 py-0.5 rounded uppercase font-bold tracking-tighter`}>
                    {selectedCandidate.isLowMatch ? "Below threshold" : "Shortlisted"}
                  </span>
                  <span className="text-[10px] text-[#A3A3A3] font-mono">{selectedCandidate.matchScore}% match</span>
                </div>
                <h1 className="text-3xl font-semibold text-white mb-1">{selectedCandidate.name}</h1>
                <p className="text-base text-[#c4c7c8] mb-2">
                  {selectedCandidate.title} · {selectedCandidate.company}
                </p>
                <p className="text-sm text-[#8e9192]">
                  Evidence-backed profile review across skills, experience, and recruiter signals.
                </p>
              </header>

              <div className="space-y-6">
                
                {/* Transferable Skills Evidence */}
                <div className="border border-[#262626] bg-[#111111] rounded-lg overflow-hidden transition-colors hover:border-[#404040]">
                  <div className="p-4 border-b border-[#262626] flex items-center justify-between bg-[#171717]">
                    <span className="text-xs font-bold text-white flex items-center gap-2 uppercase tracking-widest">
                      Transferable Skills Evidence
                    </span>
                  </div>
                  <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#262626]">
                    <div className="p-4">
                      <h4 className="text-[10px] text-[#c4c7c8] mb-2 uppercase font-semibold">Adjacent Skills</h4>
                      <p className="text-sm text-white">
                        {(selectedCandidate.adjacent_skills?.length ?? 0) > 0 ? selectedCandidate.adjacent_skills!.join(", ") : "No evidence available."}
                      </p>
                    </div>
                    <div className="p-4 bg-[#141313]">
                      <h4 className="text-[10px] text-[#c4c7c8] mb-2 uppercase font-semibold">Evidence</h4>
                      <div className="space-y-2">
                        {(selectedCandidate.transferability_evidence?.length ?? 0) > 0 ? selectedCandidate.transferability_evidence!.map((item, i) => (
                          <p key={i} className="text-sm text-[#c4c7c8]">{item}</p>
                        )) : <p className="text-sm text-[#c4c7c8]">No evidence available.</p>}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Extracted Evidence */}
                <div className="border border-[#262626] bg-[#111111] rounded-lg overflow-hidden transition-colors hover:border-[#404040]">
                  <div className="p-4 border-b border-[#262626] flex items-center justify-between bg-[#171717]">
                    <span className="text-xs font-bold text-white flex items-center gap-2 uppercase tracking-widest">
                      Candidate Evidence
                    </span>
                  </div>
                  <div className="grid md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#262626]">
                    <div className="p-4">
                      <h4 className="text-[10px] text-[#c4c7c8] mb-2 uppercase font-semibold">Matched Skills</h4>
                      <p className="text-sm text-[#22C55E]">
                        {(selectedCandidate.matched_skills?.length ?? 0) > 0 ? selectedCandidate.matched_skills!.join(", ") : "No evidence available."}
                      </p>
                    </div>
                    <div className="p-4 bg-[#141313]">
                      <h4 className="text-[10px] text-[#EF4444] mb-2 uppercase font-semibold">Missing Skills</h4>
                      <p className="text-sm text-[#c4c7c8]">
                        {(selectedCandidate.missing_skills?.length ?? 0) > 0 ? selectedCandidate.missing_skills!.join(", ") : "No evidence available."}
                      </p>
                    </div>
                  </div>
                  <div className="p-4 border-t border-[#262626]">
                    <h4 className="text-[10px] text-[#c4c7c8] mb-2 uppercase font-semibold">Explanation</h4>
                    <p className="text-sm text-[#c4c7c8] whitespace-pre-wrap">
                      {selectedCandidate.explanation || "No evidence available."}
                    </p>
                  </div>
                </div>

                {/* Score Decomposition */}
                <div className="border border-[#262626] bg-[#111111] rounded-lg overflow-hidden transition-colors hover:border-[#404040]">
                  <div className="p-4 border-b border-[#262626] flex items-center justify-between bg-[#171717]">
                    <span className="text-xs font-bold text-white flex items-center gap-2 uppercase tracking-widest">
                      Match breakdown
                    </span>
                    <span className="text-[10px] font-mono text-[#c4c7c8]">Overall: {selectedCandidate.matchScore}%</span>
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
                      <div className="text-[10px] text-[#A3A3A3] uppercase tracking-wider mb-1">Exp. Affinity</div>
                      <div className="text-sm font-mono text-white">{selectedCandidate.finalScores?.experienceAffinity?.toFixed(3) || 0}</div>
                    </div>
                    <div className="bg-[#141313] p-3 rounded border border-[#262626]">
                      <div className="text-[10px] text-[#A3A3A3] uppercase tracking-wider mb-1">Skill Depth</div>
                      <div className="text-sm font-mono text-white">{selectedCandidate.finalScores?.skillDepth?.toFixed(3) || 0}</div>
                    </div>
                    <div className="bg-[#141313] p-3 rounded border border-[#262626]">
                      <div className="text-[10px] text-[#A3A3A3] uppercase tracking-wider mb-1">Authenticity</div>
                      <div className="text-sm font-mono text-white">{selectedCandidate.finalScores?.domainAuthenticity?.toFixed(3) || 0}</div>
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
                      Career trajectory
                    </span>
                  </div>
                  <div className="p-4">
                    <p className="text-sm text-[#c4c7c8] whitespace-pre-wrap">{selectedCandidate.narrative}</p>
                  </div>
                </div>

              </div>
            </div>
          ) : (
            <div className="flex h-full items-center justify-center text-[#c4c7c8] text-sm">
              Select a candidate to review their profile and match evidence.
            </div>
          )}
        </section>

        {/* Column 3: Summary & Verdict */}
        <aside className="w-full md:w-[320px] shrink-0 bg-[#111111] border-l border-[#262626] flex flex-col p-6 gap-8 overflow-y-auto">
          {selectedCandidate && (
            <>
              <div>
                <h3 className="text-xs text-[#c4c7c8] uppercase tracking-widest mb-4 font-semibold">Recommendation</h3>
                <div className="space-y-4">
                  <div className="p-4 border border-[#262626] bg-[#171717] rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-bold uppercase tracking-widest">Match score</span>
                      <span className={`font-mono text-[11px] uppercase ${selectedCandidate.isLowMatch ? 'text-[#EF4444]' : 'text-[#22C55E]'}`}>
                        {selectedCandidate.matchScore}%
                      </span>
                    </div>
                    <p className="text-sm text-[#c4c7c8]">
                      {selectedCandidate.isLowMatch
                        ? `Below the 30% shortlist threshold. ${selectedCandidate.missing_skills?.slice(0, 3).join(', ') || 'Key requirements'} not sufficiently represented.`
                        : `Meets shortlist criteria with strong alignment on ${selectedCandidate.matched_skills?.slice(0, 3).join(', ') || 'core skills'}.`}
                    </p>
                  </div>

                  <div className={`p-4 border bg-[#171717] rounded-lg ${selectedCandidate.isLowMatch ? 'border-[#EF4444]/30' : 'border-[#22C55E]/30'}`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-bold uppercase tracking-widest text-white">Recruiter signals</span>
                    </div>
                    <div className="space-y-1">
                      {selectedCandidate.evidence.recruiter.map((line) => (
                        <p key={line} className="text-sm text-[#c4c7c8]">{line}</p>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-auto pt-8 border-t border-[#262626]">
                <h3 className="text-xs text-[#c4c7c8] uppercase tracking-widest mb-6 font-semibold">Decision</h3>
                <div className={`flex flex-col items-center justify-center p-8 rounded-lg shadow-2xl relative overflow-hidden ${selectedCandidate.isLowMatch ? 'bg-[#141313] border border-[#EF4444]/30' : 'bg-white text-black'}`}>
                  <span className={`font-mono text-[10px] uppercase font-bold mb-2 ${selectedCandidate.isLowMatch ? 'text-[#EF4444]' : 'text-black/60'}`}>
                    SignalHire recommendation
                  </span>

                  <div className={`text-2xl font-extrabold uppercase tracking-tighter transform -rotate-2 border-2 px-4 py-1 ${selectedCandidate.isLowMatch ? 'text-[#EF4444] border-[#EF4444]' : 'text-black border-black'}`}>
                    {selectedCandidate.isLowMatch ? 'Not shortlisted' : 'Shortlist'}
                  </div>

                  <p className={`text-[10px] mt-4 italic ${selectedCandidate.isLowMatch ? 'text-[#EF4444]/70' : 'text-black/70'}`}>
                    Rank #{selectedCandidate.rank} of {candidates.length}
                  </p>
                </div>

                <div className="mt-6 space-y-2">
                  <button
                    onClick={() => { setSelectedCandidate(null); clearComparison(); }}
                    className="w-full py-2 bg-white text-black text-xs font-bold rounded hover:opacity-90 transition-opacity uppercase tracking-widest"
                  >
                    {selectedCandidate.isLowMatch ? 'Dismiss' : 'Move to outreach'}
                  </button>
                  <button className="w-full py-2 border border-[#262626] text-white text-xs font-bold rounded hover:bg-[#171717] transition-colors uppercase tracking-widest">
                    Share with hiring manager
                  </button>
                  <button 
                    disabled={candidates.length === 0} 
                    title={candidates.length === 0 ? "No ranking results available." : "Export to CSV"} 
                    onClick={() => {
                      const csvContent = "data:text/csv;charset=utf-8," + 
                        "Rank,Name,Match Score,Status\n" + 
                        candidates.map(c => `${c.rank},"${c.name}",${c.matchScore},${c.isLowMatch ? 'REJECTED' : 'RECOMMENDED'}`).join("\n");
                      const encodedUri = encodeURI(csvContent);
                      const link = document.createElement("a");
                      link.setAttribute("href", encodedUri);
                      link.setAttribute("download", `signalhire_export_${invId}.csv`);
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                    }}
                    className="w-full py-2 border border-[#262626] text-white text-xs font-bold rounded hover:bg-[#171717] transition-colors uppercase tracking-widest disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Export Results
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
