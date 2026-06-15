"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Upload, Database, FileText, Play, CheckCircle2, Loader2, PlayCircle } from "lucide-react";
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

const PIPELINE_STAGES = [
  "Parsing job description",
  "Extracting requirements",
  "Indexing candidates",
  "Scoring skill fit",
  "Ranking by relevance",
  "Building shortlist",
];

export default function NewInvestigationPage() {
  const router = useRouter();
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentStage, setCurrentStage] = useState(-1);
  const [jdText, setJdText] = useState("Role: Senior Search Engineer\nSkills: FAISS, Qdrant, Learning-to-Rank, Python\nExperience: Production ML infrastructure");
  const [files, setFiles] = useState<File[]>([]);

  const [jdFile, setJdFile] = useState<File | null>(null);

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

  const handleRun = async () => {
    if (files.length === 0) {
      alert("Please upload at least one resume PDF before running the pipeline.");
      return;
    }

    setIsExecuting(true);
    setCurrentStage(0);

    const API_BASE = getApiBase();

    // 1. Start Investigation via API
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

      // Upload candidates and collect parse task IDs
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
    <div className="h-screen bg-[#0A0A0A] text-[#e5e2e1] font-sans selection:bg-white selection:text-black flex flex-col">
      <AppNav active="new" />

      <main className="pt-24 px-4 md:px-10 max-w-4xl mx-auto w-full flex-1 flex flex-col">
        {!isExecuting ? (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="w-full">
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
                  onClick={() => handleRun()}
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
          </motion.div>
        ) : (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex-1 flex items-center justify-center">
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
          </motion.div>
        )}
      </main>
    </div>
  );
}
