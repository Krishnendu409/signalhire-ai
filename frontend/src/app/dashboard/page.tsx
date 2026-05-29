"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Upload, Briefcase, Sparkles, CheckCircle, Users,
  Zap, AlertTriangle, FileText
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { EvaluationCard } from "@/components/EvaluationCard";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type CandidateResult = {
  full_name: string;
  final_score: number;
  dimension_scores: {
    semantic_relevance?: { score?: number };
    career_trajectory?: { score?: number };
  };
  explanation?: {
    top_strengths: string[];
    missing_skills: string[];
    adjacent_skills: string[];
    risk_factors: string[];
    overall_assessment: string;
    extracted_evidence: { claim: string; evidence: string }[];
  };
  parsed_data: {
    _trajectory?: {
      archetype: "fast_climber" | "stable_performer" | "chaotic_hopper" | "mixed" | "unknown";
      score: number;
      details: string;
    };
    _meta?: {
      layout_complexity: number;
      extraction_confidence: number;
      parser_warnings: string[];
    };
  };
  id?: string | number;
};

type PollResult = {
  status?: string;
  error?: string;
  results?: CandidateResult[];
};

export default function DashboardPage() {
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [resumeFiles, setResumeFiles] = useState<File[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [results, setResults] = useState<CandidateResult[]>([]);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleProcess = async () => {
    if (!jdFile || resumeFiles.length === 0) return;
    setIsProcessing(true);
    setUploadProgress(5);
    setStatusMessage("Parsing Job Description...");
    setError(null);

    try {
      // 1. Upload JD (multipart/form-data with title + file)
      const jdFormData = new FormData();
      jdFormData.append("file", jdFile);
      jdFormData.append("title", jdFile.name.replace(/\.[^/.]+$/, ""));
      const jobRes = await fetch(`${API_BASE}/api/jobs`, {
        method: "POST",
        body: jdFormData,
        headers: { "Authorization": "Bearer demo-token-placeholder" }
      });
      const jobData = await jobRes.json();
      if (!jobRes.ok) throw new Error(jobData.detail || "JD upload failed");
      
      const jobId = jobData.id;
      setCurrentJobId(jobId);
      setUploadProgress(20);

      // 2. Upload Resumes
      setStatusMessage(`Uploading ${resumeFiles.length} resumes...`);
      for (let i = 0; i < resumeFiles.length; i++) {
        const file = resumeFiles[i];
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(`${API_BASE}/api/candidates/upload`, {
          method: "POST",
          body: formData,
          headers: { "Authorization": "Bearer demo-token-placeholder" }
        });
        const data = await res.json();
        if (!res.ok) throw new Error(`Resume upload failed: ${data.detail || "Unknown error"}`);
        setUploadProgress(20 + ((i + 1) / resumeFiles.length) * 40);
        setStatusMessage(`Uploaded ${file.name}`);
      }

      // 3. Wait briefly for async parsing to complete (simplified)
      setStatusMessage("Processing resumes (OCR + AI extraction)...");
      await new Promise(r => setTimeout(r, 3000));

      // 4. Trigger Ranking
      setStatusMessage("Starting ranking engine...");
      const rankRes = await fetch(`${API_BASE}/api/rankings/${jobId}`, {
        method: "POST",
        headers: { "Authorization": "Bearer demo-token-placeholder" }
      });
      const rankData = await rankRes.json();
      if (!rankRes.ok) throw new Error(rankData.detail || rankData.message || "Ranking trigger failed");

      // 5. Poll for completed ranking using job_id directly
      setStatusMessage("Analyzing profiles and generating explanations...");
      let finalResults: PollResult | null = null;
      let attempts = 0;
      while (attempts < 30) {
        await new Promise(r => setTimeout(r, 2000));
        const pollRes = await fetch(`${API_BASE}/api/rankings/${jobId}/latest`, {
          headers: { "Authorization": "Bearer demo-token-placeholder" }
        });
        const pollData = await pollRes.json();
        if (pollData.status === "completed") {
          finalResults = pollData;
          break;
        }
        if (pollData.status === "failed") {
          throw new Error(pollData.error || "Ranking failed");
        }
        attempts++;
        setUploadProgress(60 + (attempts / 30) * 35);
        setStatusMessage(`Ranking in progress... (attempt ${attempts})`);
      }
      if (!finalResults) throw new Error("Ranking timed out after 60 seconds");

      setResults(finalResults.results || []);
      setUploadProgress(100);
      setStatusMessage("Complete!");
    } catch (err: unknown) {
      console.error("Processing failed:", err);
      setError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setIsProcessing(false);
      setStatusMessage("");
    }
  };

  return (
    <div className="min-h-screen bg-[#020617] text-slate-50 selection:bg-blue-500/30">
      {/* Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 blur-[120px] rounded-full animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/10 blur-[120px] rounded-full animate-pulse" />
      </div>

      {/* Header */}
      <header className="border-b border-white/5 bg-black/40 backdrop-blur-2xl sticky top-0 z-50 px-8 py-5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-black tracking-tight">SignalHire<span className="text-blue-500">AI</span></span>
          </div>
          <div className="flex items-center gap-2 text-xs font-bold text-emerald-400">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Engine Online
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-10 space-y-10">
        {error && (
          <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <p className="text-sm font-bold text-red-400">{error}</p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setError(null)} className="text-red-400">Dismiss</Button>
          </div>
        )}

        {results.length === 0 ? (
          <div className="space-y-12">
            {/* Hero */}
            <div className="text-center space-y-4 max-w-2xl mx-auto">
              <h1 className="text-4xl font-black tracking-tight text-white leading-tight">
                Identify Top Talent <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-500">Beyond the Keywords</span>
              </h1>
              <p className="text-slate-400 text-sm leading-relaxed font-medium">
                Upload your Job Description and candidate resumes to activate the multi‑stage semantic retrieval engine.
              </p>
            </div>

            {/* Upload Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* JD Upload */}
              <Card className="group relative p-8 bg-white/[0.03] border-white/5 hover:border-blue-500/30 transition-all">
                <div className="flex items-center gap-4 mb-8">
                  <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center ring-1 ring-blue-500/20">
                    <Briefcase className="w-6 h-6 text-blue-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold">Requirement Profile</h3>
                    <p className="text-xs text-slate-500">PDF, JPG, or Plain Text</p>
                  </div>
                </div>
                <div
                  onClick={() => document.getElementById("jd-upload")?.click()}
                  className={`border-2 border-dashed rounded-3xl p-12 text-center cursor-pointer transition-all
                    ${jdFile ? "border-emerald-500/30 bg-emerald-500/5" : "border-white/10 hover:border-white/20"}`}
                >
                  <input id="jd-upload" type="file" accept=".pdf,.txt,.jpg,.jpeg,.png" className="hidden" onChange={(e) => setJdFile(e.target.files?.[0] || null)} />
                  {jdFile ? (
                    <div className="space-y-3">
                      <CheckCircle className="w-16 h-16 text-emerald-500 mx-auto" />
                      <p className="text-emerald-400 text-sm font-black truncate max-w-xs mx-auto">{jdFile.name}</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <Upload className="w-16 h-16 text-slate-500 mx-auto group-hover:text-blue-400 transition-colors" />
                      <p className="text-sm text-slate-400 font-bold">Drop Job Specification</p>
                      <p className="text-[10px] text-slate-500">Up to 10MB file size</p>
                    </div>
                  )}
                </div>
              </Card>

              {/* Resumes Upload */}
              <Card className="group relative p-8 bg-white/[0.03] border-white/5 hover:border-purple-500/30 transition-all">
                <div className="flex items-center gap-4 mb-8">
                  <div className="w-12 h-12 rounded-2xl bg-purple-500/10 flex items-center justify-center ring-1 ring-purple-500/20">
                    <Users className="w-6 h-6 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold">Candidate Pool</h3>
                    <p className="text-xs text-slate-500">{resumeFiles.length} profiles queued</p>
                  </div>
                </div>
                <div
                  onClick={() => document.getElementById("resume-upload")?.click()}
                  className={`border-2 border-dashed rounded-3xl p-12 text-center cursor-pointer transition-all
                    ${resumeFiles.length > 0 ? "border-emerald-500/30 bg-emerald-500/5" : "border-white/10 hover:border-white/20"}`}
                >
                  <input id="resume-upload" type="file" accept=".pdf,.jpg,.jpeg,.png" multiple className="hidden" onChange={(e) => {
                    const files = Array.from(e.target.files || []).filter(f => f.type === "application/pdf" || f.type.startsWith("image/"));
                    setResumeFiles(prev => [...prev, ...files]);
                  }} />
                  {resumeFiles.length > 0 ? (
                    <div className="space-y-3">
                      <CheckCircle className="w-16 h-16 text-emerald-500 mx-auto" />
                      <p className="text-emerald-400 text-sm font-black">{resumeFiles.length} file(s) selected</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <Upload className="w-16 h-16 text-slate-500 mx-auto group-hover:text-purple-400 transition-colors" />
                      <p className="text-sm text-slate-400 font-bold">Bulk Upload Resumes</p>
                      <p className="text-[10px] text-slate-500">Optimized for Multi-Column Layouts</p>
                    </div>
                  )}
                </div>
                {resumeFiles.length > 0 && (
                  <div className="mt-6 flex flex-wrap gap-2">
                    {resumeFiles.slice(0, 5).map((f, i) => (
                      <div key={i} className="px-3 py-1 rounded bg-white/5 text-[10px] font-bold text-slate-400 truncate max-w-[120px]">{f.name}</div>
                    ))}
                    {resumeFiles.length > 5 && <div className="px-3 py-1 rounded bg-purple-500/10 text-[10px] text-purple-400">+{resumeFiles.length - 5} more</div>}
                  </div>
                )}
              </Card>
            </div>

            {/* Process Button */}
            <div className="flex flex-col items-center gap-8 py-12">
              {isProcessing ? (
                <div className="w-full max-w-xl space-y-6">
                  <div className="flex justify-between items-end">
                    <div className="space-y-1">
                      <p className="text-xs font-black uppercase tracking-widest text-blue-400 animate-pulse">{statusMessage}</p>
                      <p className="text-[10px] text-slate-500 font-bold">AI Processing Loop</p>
                    </div>
                    <span className="text-2xl font-black text-white">{Math.round(uploadProgress)}%</span>
                  </div>
                  <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                    <motion.div initial={{ width: 0 }} animate={{ width: `${uploadProgress}%` }} className="h-full bg-gradient-to-r from-blue-600 to-purple-600 rounded-full shadow-[0_0_15px_rgba(37,99,235,0.4)]" />
                  </div>
                </div>
              ) : (
                <div className="space-y-4 text-center">
                  <Button onClick={handleProcess} disabled={!jdFile || resumeFiles.length === 0} className="bg-blue-600 hover:bg-blue-500 text-white font-black h-16 px-16 rounded-3xl shadow-2xl shadow-blue-600/40 disabled:opacity-50 disabled:grayscale">
                    <Zap className="w-6 h-6 mr-3" /> Activate Ranking Engine
                  </Button>
                  <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Cross-Encoder Reranking Powered</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Results View */
          <div className="space-y-8 pb-20">
            <div className="flex items-center justify-between">
              <h2 className="text-3xl font-black tracking-tight">Recruiting <span className="text-blue-500">Intelligence</span></h2>
              <Badge className="bg-blue-500 text-white font-black px-3">{results.length} Candidates</Badge>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
              <div className="md:col-span-3 space-y-6">
                {results.map((res, i) => (
                  <motion.div key={res.id || i} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
                    <EvaluationCard candidate={res} />
                  </motion.div>
                ))}
              </div>
              <div className="md:sticky md:top-28 space-y-6">
                <Card className="p-6 bg-white/[0.03] border-white/5 space-y-8 rounded-3xl backdrop-blur-xl">
                  <div className="space-y-4">
                    <h4 className="text-[10px] font-black uppercase text-slate-500 tracking-[0.2em]">Intelligence Center</h4>
                    <div className="space-y-2">
                      <div className="flex justify-between text-[11px] font-bold">
                        <span className="text-slate-400">Mean Integrity</span>
                        <span className="text-emerald-400">92%</span>
                      </div>
                      <Progress value={92} className="h-1 bg-white/5" />
                    </div>
                  </div>
                  <Button className="w-full bg-blue-600 hover:bg-blue-500 text-white font-black text-xs h-12 rounded-2xl" onClick={() => window.open(`${API_BASE}/api/rankings/${currentJobId}/export`)}>
                    <FileText className="w-4 h-4 mr-2" /> Export CSV
                  </Button>
                  <Button variant="outline" className="w-full border-white/10 hover:bg-white/5 text-white font-black text-xs h-12 rounded-2xl" onClick={() => { setResults([]); setJdFile(null); setResumeFiles([]); }}>
                    Reset Session
                  </Button>
                </Card>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}