"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Upload, Database, FileText, Play, CheckCircle2, Loader2, PlayCircle,
  Zap, XCircle, ChevronDown, BarChart2, Shield, Users, Clock, Cpu,
  TrendingUp, AlertTriangle, Search
} from "lucide-react";
import Link from "next/link";
import { AppNav } from "@/components/AppNav";
import { getApiBase } from "@/lib/api-base";
import {
  waitForTasks,
  waitForJobCandidates,
  startRanking,
  waitForRankingComplete,
  runHackathonDemo,
} from "@/lib/pipeline";
import { run100kPipeline, get100kStatus, get100kResults } from "@/lib/api-client";

// ── Types for 100k Pipeline ──────────────────────────────────────────────────
type PipelineStatus = {
  status: "idle" | "running" | "completed" | "failed";
  progress: number;
  stage: string;
  error: string | null;
  has_results: boolean;
  elapsed_seconds: number | null;
};

type TopCandidate = {
  rank: number;
  candidate_id: string;
  full_name: string;
  title: string;
  final_score: number;
  reasoning: string;
  matched_skills: string[];
  missing_skills: string[];
  years_of_experience: number;
  feature_scores?: Record<string, number>;
  decisionPath: {
    penalizedBecause: string[];
  };
};

type Analytics = {
  totalEvaluated: number;
  retrieved: number;
  ranked: number;
  shortlisted: number;
  model: string;
  skills: Record<string, number>;
  signals: Array<{ name: string; count: number; avgRank: number; avgScore: number }>;
  rejections: Array<{ reason: string; count: number }>;
};

type Results = {
  status: string;
  analytics?: Analytics;
  results?: TopCandidate[];
  elapsed_seconds?: number;
  model?: string;
  scoring_method?: string;
  used_lgbm?: boolean;
};

const PIPELINE_STAGES = [
  "Parsing job description",
  "Extracting requirements",
  "Indexing candidates",
  "Scoring skill fit",
  "Ranking by relevance",
  "Building shortlist",
];

const PIPELINE_100K_STAGES = [
  { label: "Load embeddings", icon: Cpu },
  { label: "Encode JD (MiniLM)", icon: Search },
  { label: "Semantic top-5000", icon: TrendingUp },
  { label: "BM25 over 100k corpus", icon: BarChart2 },
  { label: "Hybrid union retrieval", icon: Users },
  { label: "8-feature extraction", icon: Zap },
  { label: "LightGBM LambdaRank scoring", icon: TrendingUp },
  { label: "Top-100 selection", icon: CheckCircle2 },
];

export default function NewInvestigationPage() {
  const router = useRouter();
  const [searchMode, setSearchMode] = useState<"standard" | "100k">("standard");

  // ── Standard Search State ───────────────────────────────────────────────
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentStage, setCurrentStage] = useState(-1);
  const [jdText, setJdText] = useState("Role: Senior Search Engineer\nSkills: FAISS, Qdrant, Learning-to-Rank, Python\nExperience: Production ML infrastructure");
  const [files, setFiles] = useState<File[]>([]);
  const [jdFile, setJdFile] = useState<File | null>(null);

  // ── 100k Pipeline State ─────────────────────────────────────────────────
  const [status, setStatus] = useState<PipelineStatus>({
    status: "idle", progress: 0, stage: "", error: null,
    has_results: false, elapsed_seconds: null,
  });
  const [results, setResults] = useState<Results | null>(null);
  const [triggering, setTriggering] = useState(false);
  const [expandedCandidate, setExpandedCandidate] = useState<number | null>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  // ── 100k Pipeline Methods ───────────────────────────────────────────────
  const stopPolling = () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  };

  const fetchResults = async () => {
    try {
      const res = await get100kResults();
      setResults(res as unknown as Results);
    } catch { /* silent */ }
  };

  const startPolling = useCallback(() => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const s = await get100kStatus();
        setStatus(s as PipelineStatus);
        if (s.status === "completed" && s.has_results) {
          stopPolling();
          fetchResults();
        } else if (s.status === "failed") {
          stopPolling();
        }
      } catch { /* ignore transient errors */ }
    }, 1500);
  }, []);

  useEffect(() => {
    get100kStatus().then(async (s) => {
      setStatus(s as PipelineStatus);
      if (s.status === "running") {
        startPolling();
      } else if (s.status === "completed" && s.has_results) {
        fetchResults();
      }
    }).catch(() => {});
    return stopPolling;
  }, [startPolling]);

  const handleRun100k = async () => {
    setTriggering(true);
    try {
      await run100kPipeline();
      setStatus(s => ({ ...s, status: "running", progress: 0, stage: "Initialising…" }));
      setResults(null);
      startPolling();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to start pipeline");
    } finally {
      setTriggering(false);
    }
  };

  const is100kIdle      = status.status === "idle";
  const is100kRunning   = status.status === "running";
  const is100kCompleted = status.status === "completed";
  const is100kFailed    = status.status === "failed";
  const analytics       = results?.analytics;
  const candidates      = results?.results?.slice(0, 10) ?? [];

  // ── Standard Search Methods ─────────────────────────────────────────────
  const runPipeline = async (jobId: string, taskIds: string[], resumeCount = 1) => {
    const API_BASE = getApiBase();
    const parseTimeout = Math.max(120_000, resumeCount * 5_000);
    const candidateTimeout = Math.max(60_000, resumeCount * 3_000);

    if (taskIds.length > 0) {
      await waitForTasks(API_BASE, taskIds, parseTimeout);
      await waitForJobCandidates(API_BASE, jobId, candidateTimeout);
    }

    await startRanking(API_BASE, jobId);
    await waitForRankingComplete(API_BASE, jobId);

    setCurrentStage(PIPELINE_STAGES.length - 1);
    setTimeout(() => {
      router.push(`/workspace?id=${jobId}`);
    }, 800);
  };

  const handleHackathonDemo = async () => {
    setIsExecuting(true);
    setCurrentStage(0);

    try {
      const API_BASE = getApiBase();
      const demo = await runHackathonDemo(API_BASE);
      setCurrentStage(1);
      await runPipeline(demo.job_id, demo.task_ids, demo.resume_count);
    } catch (e) {
      console.error("Hackathon demo failed", e);
      const message = e instanceof Error ? e.message : "Failed to run hackathon demo";
      alert(message);
      setIsExecuting(false);
    }
  };

  const handleRunStandard = async () => {
    if (files.length === 0) {
      alert("Please upload at least one resume PDF before running the pipeline.");
      return;
    }

    setIsExecuting(true);
    setCurrentStage(0);

    const API_BASE = getApiBase();

    try {
      const startUrl = new URL(`${API_BASE}/jobs`);
      const formData = new FormData();
      formData.append("title", "Senior Search Engineer");
      
      if (jdFile) {
        formData.append("file", jdFile);
      } else {
        formData.append("file", new Blob([jdText], { type: "text/plain" }), "jd.txt");
      }

      const response = await fetch(startUrl.toString(), {
        method: "POST",
        body: formData
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Failed to create job");
      }
      const jobId = data.id;

      const taskIds: string[] = [];
      if (files && files.length > 0) {
        for (const file of files) {
          const uploadData = new FormData();
          uploadData.append("file", file);
          uploadData.append("job_id", jobId);
          const uploadRes = await fetch(`${API_BASE}/candidates/upload`, {
            method: "POST",
            body: uploadData,
          });
          if (!uploadRes.ok) {
            const err = await uploadRes.json().catch(() => ({}));
            throw new Error(err.detail || `Failed to upload ${file.name}`);
          }
          const uploadResult = await uploadRes.json();
          if (uploadResult.task_id) {
            taskIds.push(uploadResult.task_id);
          }
        }
        await waitForTasks(API_BASE, taskIds);
        await waitForJobCandidates(API_BASE, jobId);
      } else {
        throw new Error("Please upload at least one resume PDF.");
      }

      setCurrentStage(1);
      await startRanking(API_BASE, jobId);
      await waitForRankingComplete(API_BASE, jobId);

      setCurrentStage(PIPELINE_STAGES.length - 1);
      setTimeout(() => {
        router.push(`/workspace?id=${jobId}`);
      }, 800);

    } catch (e) {
      console.error("Error starting investigation", e);
      const message = e instanceof Error ? e.message : "Failed to start backend. Is FastAPI running on port 8000?";
      alert(message);
      setIsExecuting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-[#e5e2e1] font-sans selection:bg-white selection:text-black flex flex-col">
      <AppNav active="new" />

      <main className="pt-24 px-4 md:px-10 max-w-5xl mx-auto w-full flex-1 flex flex-col pb-24">
        {/* Tab Toggle */}
        <div className="flex items-center justify-center mb-10 w-full">
          <div className="bg-[#111111] border border-[#262626] rounded-lg p-1 flex">
            <button
              onClick={() => setSearchMode("standard")}
              className={`px-6 py-2 rounded-md text-sm font-semibold transition-colors ${
                searchMode === "standard"
                  ? "bg-[#262626] text-white shadow"
                  : "text-[#A3A3A3] hover:text-white hover:bg-[#1a1a1a]"
              }`}
            >
              Standard Search
            </button>
            <button
              onClick={() => setSearchMode("100k")}
              className={`px-6 py-2 rounded-md text-sm font-semibold transition-colors flex items-center gap-2 ${
                searchMode === "100k"
                  ? "bg-[#262626] text-white shadow"
                  : "text-[#A3A3A3] hover:text-white hover:bg-[#1a1a1a]"
              }`}
            >
              <Zap className="w-4 h-4" />
              100k Pipeline
            </button>
          </div>
        </div>

        {searchMode === "standard" && (
          <motion.div
            key="standard"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-4xl mx-auto"
          >
            {!isExecuting ? (
              <>
                <h1 className="text-3xl font-semibold text-white mb-2">New candidate search</h1>
                <p className="text-sm text-[#A3A3A3] mb-6">
                  Upload a job description and resume pool. SignalHire will parse, score, and rank candidates against your requirements.
                </p>
                <Link
                  href="/workspace"
                  className="inline-flex items-center gap-2 text-xs text-[#22C55E] hover:text-white transition-colors mb-10"
                >
                  <PlayCircle className="w-3.5 h-3.5" />
                  View sample shortlist (Senior Search Engineer)
                </Link>

                <div className="space-y-8">
                  {/* JD Input */}
                  <div className="border border-[#262626] bg-[#111111] p-6 rounded-lg">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <FileText className="w-5 h-5 text-white" />
                        <h2 className="text-sm font-semibold text-white uppercase tracking-widest">Target Profile</h2>
                      </div>
                      <label className="cursor-pointer bg-[#171717] hover:bg-[#262626] border border-[#262626] px-3 py-1 rounded text-xs text-white transition-colors">
                        <input type="file" className="hidden" accept=".pdf,.txt" onChange={(e) => {
                          if (e.target.files && e.target.files.length > 0) {
                            setJdFile(e.target.files[0]);
                          }
                        }} />
                        {jdFile ? `Selected: ${jdFile.name}` : "Upload JD File"}
                      </label>
                    </div>
                    {!jdFile && (
                      <textarea 
                        className="w-full h-32 bg-[#141313] border border-[#262626] rounded p-4 text-xs font-mono text-[#c4c7c8] focus:border-[#404040] focus:outline-none resize-none"
                        placeholder="Paste Job Description or Target Signals here..."
                        value={jdText}
                        onChange={(e) => setJdText(e.target.value)}
                      />
                    )}
                  </div>

                  {/* Candidates Input */}
                  <div className="border border-[#262626] bg-[#111111] p-6 rounded-lg">
                    <div className="flex items-center gap-3 mb-4">
                      <Database className="w-5 h-5 text-white" />
                      <h2 className="text-sm font-semibold text-white uppercase tracking-widest">Candidate Data</h2>
                    </div>
                    <label className="border-2 border-dashed border-[#262626] rounded-lg p-8 flex flex-col items-center justify-center text-center hover:bg-[#141313] transition-colors cursor-pointer relative block">
                      <input type="file" multiple className="hidden" onChange={(e) => {
                        if (e.target.files) {
                          setFiles(Array.from(e.target.files));
                        }
                      }} />
                      <Upload className="w-6 h-6 text-[#A3A3A3] mb-3" />
                      <p className="text-sm text-white font-medium">Upload candidate resumes (PDFs)</p>
                      <p className="text-[10px] text-[#A3A3A3] mt-1 uppercase tracking-widest">
                        {files.length > 0 ? `${files.length} file(s) selected` : "PDF resumes supported"}
                      </p>
                    </label>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col sm:flex-row items-stretch gap-4 pt-4">
                    <button 
                      onClick={() => handleRunStandard()}
                      disabled={files.length === 0}
                      className="flex-1 border border-[#262626] bg-[#111111] text-white py-4 rounded font-bold text-xs uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-[#141313] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <PlayCircle className="w-4 h-4 text-[#EF4444]" />
                      Run search
                    </button>
                    <button
                      onClick={() => handleHackathonDemo()}
                      className="flex-1 border border-[#404040] bg-[#171717] text-white py-4 rounded font-bold text-xs uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-[#262626] transition-colors"
                    >
                      <Database className="w-4 h-4 text-[#22C55E]" />
                      Benchmark full resume library
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center mt-12">
                <div className="w-full max-w-lg border border-[#262626] bg-[#111111] p-8 rounded-lg shadow-2xl">
                  <div className="mb-8 flex items-center justify-between">
                    <div>
                      <h2 className="text-sm font-bold text-white uppercase tracking-widest mb-1">
                        Running search
                      </h2>
                      <p className="text-[10px] text-[#A3A3A3] font-mono">This usually takes under a minute</p>
                    </div>
                    <div className="w-2 h-2 rounded-full bg-[#22C55E] animate-pulse" />
                  </div>

                  <div className="space-y-4">
                    {PIPELINE_STAGES.map((stage, idx) => {
                      const isCompleted = currentStage > idx;
                      const isActive = currentStage === idx;
                      const isPending = currentStage < idx;

                      return (
                        <div key={stage} className={`flex items-center justify-between p-3 border rounded ${isActive ? 'bg-[#141313] border-[#404040]' : isCompleted ? 'border-[#262626] bg-transparent' : 'border-transparent opacity-40'}`}>
                          <div className="flex items-center gap-3">
                            {isCompleted ? (
                              <CheckCircle2 className="w-4 h-4 text-[#22C55E]" />
                            ) : isActive ? (
                              <Loader2 className="w-4 h-4 text-[#F59E0B] animate-spin" />
                            ) : (
                              <div className="w-4 h-4 border border-[#262626] rounded-full" />
                            )}
                            <span className={`text-xs font-mono ${isActive ? 'text-white' : isCompleted ? 'text-[#c4c7c8]' : 'text-[#8e9192]'}`}>
                              {stage}
                            </span>
                          </div>
                          {isCompleted && <span className="text-[10px] text-[#22C55E] font-mono">OK</span>}
                          {isActive && <span className="text-[10px] text-[#F59E0B] font-mono animate-pulse">Running</span>}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}

        {searchMode === "100k" && (
          <motion.div
            key="100k"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full"
          >
            {/* ── Hero header ───────────────────────────────────────────────── */}
            <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-5 h-5 text-[#F59E0B]" />
                  <span className="text-[10px] font-mono uppercase tracking-widest text-[#F59E0B]">
                    Scale Intelligence Engine
                  </span>
                </div>
                <h1 className="text-3xl font-semibold text-white mb-2">100k Candidate Pipeline</h1>
                <p className="text-sm text-[#A3A3A3] max-w-xl">
                  Hybrid BM25 + Semantic retrieval → 8-feature extraction →{" "}
                  <span className="text-white font-medium">LightGBM LambdaRank</span> scoring across the full
                  competition dataset.
                </p>
              </div>

              <button
                onClick={handleRun100k}
                disabled={is100kRunning || triggering}
                className={`flex items-center gap-2.5 px-6 py-3 rounded font-bold text-sm uppercase tracking-widest transition-all shadow-lg ${
                  is100kRunning || triggering
                    ? "bg-[#1a1a1a] border border-[#333] text-[#666] cursor-not-allowed"
                    : is100kCompleted
                    ? "bg-[#111] border border-[#22C55E]/50 text-[#22C55E] hover:bg-[#22C55E]/10"
                    : "bg-white text-black hover:bg-gray-100 active:scale-95"
                }`}
              >
                {is100kRunning || triggering
                  ? <Loader2 className="w-4 h-4 animate-spin" />
                  : <Play className="w-4 h-4" />}
                {is100kRunning ? "Running…"
                  : triggering ? "Starting…"
                  : is100kCompleted ? "Re-run Pipeline"
                  : "Run 100k Pipeline"}
              </button>
            </header>

            {/* ── Pipeline architecture cards ────────────────────────────────── */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
              {[
                { label: "Stage 1", desc: "Hybrid Retrieval", sub: "Semantic ∪ BM25 Top-5000", color: "border-[#3b82f6]/30 bg-[#3b82f6]/5" },
                { label: "Stage 2", desc: "Feature Extraction", sub: "8 JD-relative signals", color: "border-[#8b5cf6]/30 bg-[#8b5cf6]/5" },
                { label: "Stage 3", desc: "LightGBM Score", sub: "LambdaRank trained model", color: "border-[#F59E0B]/30 bg-[#F59E0B]/5" },
                { label: "Stage 4", desc: "Top-100 Shortlist", sub: "Normalised + reasoned", color: "border-[#22C55E]/30 bg-[#22C55E]/5" },
              ].map(card => (
                <div key={card.label} className={`border ${card.color} rounded-lg p-4`}>
                  <p className="text-[10px] font-mono text-[#A3A3A3] mb-1">{card.label}</p>
                  <p className="text-sm font-semibold text-white">{card.desc}</p>
                  <p className="text-[10px] text-[#666] mt-1">{card.sub}</p>
                </div>
              ))}
            </div>

            {/* ── Status / progress panel ────────────────────────────────────── */}
            {(is100kRunning || is100kFailed || is100kCompleted) && (
              <div className={`mb-8 border rounded-lg p-6 ${
                is100kRunning   ? "border-[#F59E0B]/30 bg-[#F59E0B]/5"
                : is100kCompleted ? "border-[#22C55E]/20 bg-[#22C55E]/5"
                : "border-[#EF4444]/20 bg-[#EF4444]/5"
              }`}>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    {is100kRunning && <Loader2 className="w-5 h-5 text-[#F59E0B] animate-spin" />}
                    {is100kCompleted && <CheckCircle2 className="w-5 h-5 text-[#22C55E]" />}
                    {is100kFailed && <XCircle className="w-5 h-5 text-[#EF4444]" />}
                    <div>
                      <p className="text-sm font-semibold text-white">
                        {is100kRunning ? "Pipeline running…"
                          : is100kCompleted ? "Pipeline completed"
                          : "Pipeline failed"}
                      </p>
                      <p className="text-xs text-[#A3A3A3] mt-0.5">
                        {is100kRunning ? status.stage
                          : is100kCompleted ? `Finished in ${status.elapsed_seconds ?? results?.elapsed_seconds}s — ${results?.model ?? ""}`
                          : status.error}
                      </p>
                    </div>
                  </div>
                  {is100kCompleted && results?.used_lgbm !== undefined && (
                    <span className={`text-[10px] font-mono px-2 py-1 rounded border ${
                      results.used_lgbm
                        ? "text-[#F59E0B] border-[#F59E0B]/30 bg-[#F59E0B]/10"
                        : "text-[#A3A3A3] border-[#333]"
                    }`}>
                      {results.used_lgbm ? "⚡ LightGBM" : "∑ Heuristic"}
                    </span>
                  )}
                </div>

                {is100kRunning && (
                  <>
                    <div className="w-full h-2 bg-[#1a1a1a] rounded-full overflow-hidden mb-2">
                      <div
                        className="h-full bg-gradient-to-r from-[#F59E0B] to-[#ef4444] transition-all duration-700 rounded-full"
                        style={{ width: `${status.progress}%` }}
                      />
                    </div>
                    <p className="text-[10px] text-[#F59E0B] font-mono">{status.progress}% — {status.stage}</p>

                    {/* Stage checklist */}
                    <div className="mt-5 grid grid-cols-2 gap-2">
                      {PIPELINE_100K_STAGES.map((stg, i) => {
                        const done    = status.progress > ((i + 1) / PIPELINE_100K_STAGES.length) * 100;
                        const active  = !done && status.progress > (i / PIPELINE_100K_STAGES.length) * 100;
                        return (
                          <div key={stg.label} className={`flex items-center gap-2 text-[11px] font-mono ${
                            done ? "text-[#22C55E]" : active ? "text-[#F59E0B]" : "text-[#333]"
                          }`}>
                            {done ? <CheckCircle2 className="w-3 h-3" />
                              : active ? <Loader2 className="w-3 h-3 animate-spin" />
                              : <div className="w-3 h-3 border border-[#333] rounded-full" />}
                            {stg.label}
                          </div>
                        );
                      })}
                    </div>
                  </>
                )}
              </div>
            )}

            {/* ── Results section ─────────────────────────────────────────────── */}
            {is100kCompleted && analytics && (
              <div className="space-y-6">

                {/* Summary stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { label: "Candidates Evaluated", value: analytics.totalEvaluated.toLocaleString(), color: "text-white" },
                    { label: "Hybrid Retrieved",      value: analytics.retrieved.toLocaleString(),      color: "text-[#3b82f6]" },
                    { label: "Ranked",                value: analytics.ranked.toLocaleString(),          color: "text-[#8b5cf6]" },
                    { label: "Final Shortlist",       value: analytics.shortlisted.toString(),           color: "text-[#22C55E]" },
                  ].map(stat => (
                    <div key={stat.label} className="border border-[#262626] bg-[#111111] rounded-lg p-5">
                      <p className="text-[10px] text-[#A3A3A3] font-mono mb-2 uppercase">{stat.label}</p>
                      <p className={`text-2xl font-semibold ${stat.color}`}>{stat.value}</p>
                    </div>
                  ))}
                </div>

                {/* Two-column: rejections + skill distribution */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Rejection reasons */}
                  <div className="border border-[#262626] bg-[#111111] rounded-lg p-5">
                    <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                      <Shield className="w-4 h-4 text-[#EF4444]" /> Rejection Breakdown
                    </h3>
                    <div className="space-y-3">
                      {analytics.rejections.map(r => (
                        <div key={r.reason} className="flex items-start justify-between gap-3">
                          <div className="flex items-start gap-2">
                            <AlertTriangle className="w-3.5 h-3.5 text-[#EF4444] mt-0.5 shrink-0" />
                            <span className="text-xs text-[#c4c7c8]">{r.reason}</span>
                          </div>
                          <span className="text-xs font-mono text-[#EF4444] bg-[#EF4444]/10 px-2 py-0.5 rounded shrink-0">
                            {r.count.toLocaleString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Skill distribution */}
                  <div className="border border-[#262626] bg-[#111111] rounded-lg p-5">
                    <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                      <Users className="w-4 h-4" /> Top Skill Coverage (Top-100)
                    </h3>
                    <div className="space-y-2">
                      {Object.entries(analytics.skills).slice(0, 10).map(([sk, cnt]) => {
                        const max = Math.max(...Object.values(analytics.skills));
                        return (
                          <div key={sk} className="flex items-center gap-3">
                            <span className="text-xs text-[#c4c7c8] capitalize w-32 truncate">{sk}</span>
                            <div className="flex-1 h-1.5 bg-[#1a1a1a] rounded-full overflow-hidden">
                              <div className="h-full bg-[#22C55E]" style={{ width: `${(cnt / max) * 100}%` }} />
                            </div>
                            <span className="text-xs font-mono text-white w-8 text-right">{cnt}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Top 10 candidates */}
                <div className="border border-[#262626] bg-[#111111] rounded-lg p-5">
                  <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-5 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-[#22C55E]" /> Top-10 Ranked Candidates
                  </h3>
                  <div className="space-y-3">
                    {candidates.map((c) => (
                      <div key={c.candidate_id} className="border border-[#262626] rounded-lg overflow-hidden">
                        {/* Row header */}
                        <button
                          onClick={() => setExpandedCandidate(expandedCandidate === c.rank ? null : c.rank)}
                          className="w-full flex items-center justify-between p-4 hover:bg-[#141313] transition-colors text-left"
                        >
                          <div className="flex items-center gap-4">
                            <span className="font-mono text-lg font-bold text-white w-8">#{c.rank}</span>
                            <div>
                              <p className="text-sm font-semibold text-white">{c.full_name}</p>
                              <p className="text-xs text-[#A3A3A3]">{c.title} · {c.years_of_experience}yrs</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="text-right">
                              <p className="text-lg font-bold text-[#22C55E]">{c.final_score}%</p>
                              <p className="text-[10px] text-[#A3A3A3] font-mono">match score</p>
                            </div>
                            <ChevronDown className={`w-4 h-4 text-[#A3A3A3] transition-transform ${expandedCandidate === c.rank ? "rotate-180" : ""}`} />
                          </div>
                        </button>

                        {/* Expanded detail */}
                        {expandedCandidate === c.rank && (
                          <div className="px-4 pb-4 border-t border-[#262626] pt-4 bg-[#0d0d0d]">
                            <p className="text-xs text-[#c4c7c8] mb-4 leading-relaxed">{c.reasoning}</p>

                            {/* Feature score bars */}
                            {c.feature_scores && (
                              <div className="mb-4">
                                <p className="text-[10px] font-mono text-[#A3A3A3] uppercase mb-2">Feature Contributions</p>
                                <div className="grid grid-cols-2 gap-x-6 gap-y-1.5">
                                  {Object.entries(c.feature_scores).map(([feat, score]) => {
                                    const isNeg = feat.includes("penalty") || feat.includes("risk");
                                    return (
                                      <div key={feat} className="flex items-center gap-2">
                                        <span className="text-[10px] text-[#666] w-36 truncate capitalize">
                                          {feat.replace(/_/g, " ")}
                                        </span>
                                        <div className="flex-1 h-1 bg-[#1a1a1a] rounded-full overflow-hidden">
                                          <div
                                            className={`h-full rounded-full ${isNeg ? "bg-[#EF4444]" : "bg-[#22C55E]"}`}
                                            style={{ width: `${Math.min(Math.abs(score), 100)}%` }}
                                          />
                                        </div>
                                        <span className={`text-[10px] font-mono w-8 text-right ${isNeg ? "text-[#EF4444]" : "text-white"}`}>
                                          {score.toFixed(0)}
                                        </span>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            )}

                            {/* Skills */}
                            <div className="flex flex-wrap gap-1.5">
                              {c.matched_skills.map(sk => (
                                <span key={sk} className="text-[10px] bg-[#22C55E]/10 text-[#22C55E] border border-[#22C55E]/20 px-2 py-0.5 rounded capitalize">
                                  {sk}
                                </span>
                              ))}
                              {c.missing_skills.map(sk => (
                                <span key={sk} className="text-[10px] bg-[#EF4444]/10 text-[#EF4444] border border-[#EF4444]/20 px-2 py-0.5 rounded capitalize">
                                  ✗ {sk}
                                </span>
                              ))}
                              {c.decisionPath.penalizedBecause.map(p => (
                                <span key={p} className="text-[10px] bg-[#F59E0B]/10 text-[#F59E0B] border border-[#F59E0B]/20 px-2 py-0.5 rounded">
                                  ⚠ {p}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

              </div>
            )}

            {/* ── Idle state ─────────────────────────────────────────────────── */}
            {is100kIdle && (
              <div className="border border-dashed border-[#262626] rounded-xl p-16 flex flex-col items-center justify-center text-center">
                <Zap className="w-10 h-10 text-[#333] mb-4" />
                <h2 className="text-lg font-semibold text-white mb-2">Ready to rank 100,000 candidates</h2>
                <p className="text-sm text-[#A3A3A3] max-w-md mb-6">
                  Click <strong className="text-white">Run 100k Pipeline</strong> to start.
                  The pipeline runs entirely in the background — no browser timeout, no terminal needed.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left w-full max-w-lg">
                  {[
                    { icon: Clock, label: "~2–5 min", desc: "Typical runtime for full corpus" },
                    { icon: Cpu,   label: "LightGBM", desc: "LambdaRank trained model" },
                    { icon: Shield, label: "8 Features", desc: "incl. anti-skill + trap penalties" },
                  ].map(item => (
                    <div key={item.label} className="border border-[#222] rounded-lg p-4 bg-[#0d0d0d]">
                      <item.icon className="w-4 h-4 text-[#A3A3A3] mb-2" />
                      <p className="text-sm font-semibold text-white">{item.label}</p>
                      <p className="text-[11px] text-[#666]">{item.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </main>
    </div>
  );
}
