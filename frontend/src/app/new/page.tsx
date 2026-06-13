"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Fingerprint, Upload, Database, FileText, Play, CheckCircle2, Loader2, PlayCircle } from "lucide-react";
import Link from "next/link";

const PIPELINE_STAGES = [
  "Parsing Job Description",
  "Extracting Signals",
  "BM25 Retrieval",
  "Semantic Search",
  "Affinity Ranking",
  "Shortlist Construction",
];

export default function NewInvestigationPage() {
  const router = useRouter();
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentStage, setCurrentStage] = useState(-1);
  const [jdText, setJdText] = useState("Role: Senior Search Engineer\nSkills: FAISS, Qdrant, Learning-to-Rank, Python\nExperience: Production ML infrastructure");

  const handleRun = async () => {
    setIsExecuting(true);
    setCurrentStage(0);

    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

    // 1. Start Investigation via API
    try {
      const startUrl = new URL(`${API_BASE}/jobs`);
      const formData = new FormData();
      formData.append("title", "Senior Search Engineer");
      formData.append("file", new Blob([jdText], { type: "text/plain" }), "jd.txt");

      const response = await fetch(startUrl.toString(), {
        method: "POST",
        body: formData
      });
      const data = await response.json();
      const jobId = data.id;

      // Start Ranking
      const rankUrl = new URL(`${API_BASE}/rankings/${jobId}`);
      await fetch(rankUrl.toString(), { method: "POST" });

      // 2. Poll Status
      setCurrentStage(1);
      
      const poll = setInterval(async () => {
        try {
          const statusUrl = new URL(`${API_BASE}/rankings/${jobId}/latest`);
          const statusRes = await fetch(statusUrl.toString());
          const statusData = await statusRes.json();
          
          if (statusData.status === "completed") {
            clearInterval(poll);
            setCurrentStage(PIPELINE_STAGES.length - 1);
            setTimeout(() => {
              router.push(`/workspace?id=${jobId}`);
            }, 800);
          } else if (statusData.status === "failed") {
            clearInterval(poll);
            alert("Investigation failed!");
            setIsExecuting(false);
          } else {
            setCurrentStage(prev => Math.min(prev + 1, PIPELINE_STAGES.length - 2));
          }
        } catch (e) {
          console.error("Polling error", e);
        }
      }, 1500);

    } catch (e) {
      console.error("Error starting investigation", e);
      alert("Failed to start backend. Is FastAPI running on port 8000?");
      setIsExecuting(false);
    }
  };

  return (
    <div className="h-screen bg-[#0A0A0A] text-[#e5e2e1] font-sans selection:bg-white selection:text-black flex flex-col">
      {/* Top Navigation */}
      <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-4 md:px-10 h-14 bg-[#141313] border-b border-[#262626]">
        <Link href="/" className="flex items-center gap-3">
          <Fingerprint className="text-white w-5 h-5" />
          <span className="text-base font-semibold text-white tracking-tight">SignalHire</span>
        </Link>
        <div className="hidden md:flex items-center gap-6">
          <Link className="text-white font-bold text-xs bg-[#353434] px-3 py-1 rounded" href="/new">New Investigation</Link>
          <Link className="text-[#c4c7c8] text-xs hover:bg-[#353434] transition-colors px-3 py-1 rounded" href="/workspace">Workspace</Link>
          <Link className="text-[#c4c7c8] text-xs hover:bg-[#353434] transition-colors px-3 py-1 rounded" href="/analytics">Analytics</Link>
          <Link className="text-[#c4c7c8] text-xs hover:bg-[#353434] transition-colors px-3 py-1 rounded" href="/reports">Reports</Link>
        </div>
      </nav>

      <main className="pt-24 px-4 md:px-10 max-w-4xl mx-auto w-full flex-1 flex flex-col">
        {!isExecuting ? (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="w-full">
            <h1 className="text-3xl font-semibold text-white mb-2">New Investigation</h1>
            <p className="text-sm text-[#A3A3A3] mb-10">Configure the ranking pipeline for a new requisition.</p>

            <div className="space-y-8">
              {/* JD Input */}
              <div className="border border-[#262626] bg-[#111111] p-6 rounded-lg">
                <div className="flex items-center gap-3 mb-4">
                  <FileText className="w-5 h-5 text-white" />
                  <h2 className="text-sm font-semibold text-white uppercase tracking-widest">Target Profile</h2>
                </div>
                <textarea 
                  className="w-full h-32 bg-[#141313] border border-[#262626] rounded p-4 text-xs font-mono text-[#c4c7c8] focus:border-[#404040] focus:outline-none resize-none"
                  placeholder="Paste Job Description or Target Signals here..."
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                />
              </div>

              {/* Candidates Input */}
              <div className="border border-[#262626] bg-[#111111] p-6 rounded-lg">
                <div className="flex items-center gap-3 mb-4">
                  <Database className="w-5 h-5 text-white" />
                  <h2 className="text-sm font-semibold text-white uppercase tracking-widest">Candidate Data</h2>
                </div>
                <div className="border-2 border-dashed border-[#262626] rounded-lg p-8 flex flex-col items-center justify-center text-center hover:bg-[#141313] transition-colors cursor-pointer">
                  <Upload className="w-6 h-6 text-[#A3A3A3] mb-3" />
                  <p className="text-sm text-white font-medium">Upload candidates.jsonl or submission.csv</p>
                  <p className="text-[10px] text-[#A3A3A3] mt-1 uppercase tracking-widest">Or drag and drop</p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-4 pt-4">
                <button 
                  onClick={() => handleRun()}
                  className="flex-1 border border-[#262626] bg-[#111111] text-white py-4 rounded font-bold text-xs uppercase tracking-widest flex items-center justify-center gap-2 hover:bg-[#141313] transition-colors"
                >
                  <PlayCircle className="w-4 h-4 text-[#EF4444]" />
                  Run Live Pipeline
                </button>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex-1 flex items-center justify-center">
            <div className="w-full max-w-lg border border-[#262626] bg-[#111111] p-8 rounded-lg shadow-2xl">
              <div className="mb-8 flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-bold text-white uppercase tracking-widest mb-1">
                    LIVE PIPELINE EXECUTION
                  </h2>
                  <p className="text-[10px] text-[#A3A3A3] font-mono">REQ_ID: 2026-001</p>
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
          </motion.div>
        )}
      </main>
    </div>
  );
}
