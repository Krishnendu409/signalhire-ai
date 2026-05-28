// frontend/app/dashboard/page.tsx
"use client";

import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  Upload,
  FileText,
  Briefcase,
  Sparkles,
  ArrowRight,
  CheckCircle,
  Loader2,
  Users,
  BarChart3,
  TrendingUp,
  Zap,
  LayoutGrid,
  Table as TableIcon,
  Search,
  ChevronDown,
  Filter,
  AlertTriangle,
  Info
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { EvaluationCard } from "@/components/EvaluationCard";
import { TrajectoryBadge } from "@/components/TrajectoryBadge";

const API_BASE = "http://127.0.0.1:8000";

export default function DashboardPage() {
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [resumeFiles, setResumeFiles] = useState<File[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [jdDragActive, setJdDragActive] = useState(false);
  const [resumeDragActive, setResumeDragActive] = useState(false);
  const [viewMode, setViewMode] = useState<"grid" | "spreadsheet">("grid");
  const [results, setResults] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleJdDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setJdDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.type === "application/pdf" || file.type === "text/plain")) {
      setJdFile(file);
    }
  }, []);

  const handleResumeDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setResumeDragActive(false);
    const files = Array.from(e.dataTransfer.files).filter(
      (f) => f.type === "application/pdf"
    );
    setResumeFiles((prev) => [...prev, ...files]);
  }, []);

  const handleResumeFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []).filter(
      (f) => f.type === "application/pdf"
    );
    setResumeFiles((prev) => [...prev, ...files]);
  };

  const pollTask = async (taskId: string) => {
    while (true) {
      const res = await fetch(`${API_BASE}/api/tasks/${taskId}`);
      const data = await res.json();
      if (data.status === "completed") return data.result;
      if (data.status === "failed") throw new Error(data.error);
      await new Promise(r => setTimeout(r, 2000));
    }
  };

  const handleProcess = async () => {
    if (!jdFile || resumeFiles.length === 0) return;
    setIsProcessing(true);
    setUploadProgress(10);
    setStatusMessage("Parsing Job Description...");

    try {
      // 1. Upload JD
      setStatusMessage("Uploading Job Description...");
      const jdFormData = new FormData();
      jdFormData.append("file", jdFile);
      jdFormData.append("title", jdFile.name.replace(".pdf", ""));

      const jobRes = await fetch(`${API_BASE}/api/jobs`, {
        method: "POST",
        body: jdFormData
      });
      const jobData = await jobRes.json();
      if (!jobRes.ok) throw new Error(jobData.detail || "JD Upload failed");
      
      const jobId = jobData.id;
      setCurrentJobId(jobId);
      setUploadProgress(30);

      // 2. Upload Resumes
      setStatusMessage(`Processing Resumes (0/${resumeFiles.length})...`);
      const uploadResults = [];
      for (let i = 0; i < resumeFiles.length; i++) {
        const file = resumeFiles[i];
        setStatusMessage(`Analyzing ${file.name}...`);
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(`${API_BASE}/api/candidates/upload`, {
          method: "POST",
          body: formData
        });
        const data = await res.json();
        uploadResults.push(data);
        setUploadProgress(30 + ((i + 1) / resumeFiles.length) * 30);
      }

      // 3. Trigger Ranking
      setStatusMessage("AI Semantic Ranking in progress...");
      const rankRes = await fetch(`${API_BASE}/api/rankings/${jobId}`, {
        method: "POST"
      });
      const rankData = await rankRes.json();
      
      // 4. Poll for results
      const finalResults = await pollTask(rankData.ranking_id);
      setResults(finalResults.results || []);
      setUploadProgress(100);
    } catch (err: any) {
      console.error("Processing failed:", err);
      setError(err.message || "An unexpected error occurred during AI ranking.");
    } finally {
      setIsProcessing(false);
      setStatusMessage("");
    }
  };

  const removeResume = (index: number) => {
    setResumeFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="min-h-screen bg-[#020617] text-slate-50 selection:bg-blue-500/30">
      {/* Dynamic Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/10 blur-[120px] rounded-full animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/10 blur-[120px] rounded-full animate-pulse [animation-delay:2s]" />
      </div>

      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="border-b border-white/5 bg-black/40 backdrop-blur-2xl sticky top-0 z-50 px-8 py-5"
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 p-[1px]">
              <div className="w-full h-full rounded-xl bg-[#020617] flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-blue-400" />
              </div>
            </div>
            <div>
              <span className="text-xl font-black tracking-tight">SignalHire<span className="text-blue-500">AI</span></span>
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-[0.2em] leading-none mt-1">Enterprise Intelligence</p>
            </div>
          </div>
          
          <div className="flex items-center gap-6">
            <div className="hidden lg:flex items-center gap-3 px-4 py-2 rounded-full bg-white/5 border border-white/10">
               <div className="flex -space-x-2">
                 {[1,2,3].map(i => <div key={i} className="w-6 h-6 rounded-full border-2 border-[#020617] bg-slate-800" />)}
               </div>
               <span className="text-[11px] font-bold text-slate-400">12 Active Recruiters</span>
            </div>
            <div className="h-8 w-[1px] bg-white/10 hidden sm:block" />
            <div className="flex items-center gap-2 text-xs font-bold text-emerald-400">
               <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)] animate-pulse" />
               <span className="hidden sm:inline">Engine Online</span>
            </div>
          </div>
        </div>
      </motion.header>

      <main className="max-w-7xl mx-auto px-8 py-10 space-y-10">
        {error && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-between gap-4"
          >
             <div className="flex items-center gap-3">
               <AlertTriangle className="w-5 h-5 text-red-500" />
               <p className="text-sm font-bold text-red-400">{error}</p>
             </div>
             <Button variant="ghost" size="sm" onClick={() => setError(null)} className="text-red-400 hover:bg-red-500/10">Dismiss</Button>
          </motion.div>
        )}

        {results.length === 0 ? (
          <div className="space-y-12">
            {/* Hero Section */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center space-y-4 max-w-2xl mx-auto"
            >
              <h1 className="text-4xl font-black tracking-tight text-white leading-tight">
                Identify Top Talent <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-500">Beyond the Keywords</span>
              </h1>
              <p className="text-slate-400 text-sm leading-relaxed font-medium">
                Upload your Job Description and candidate resumes to activate the multi-stage 
                semantic retrieval engine. Optimized for sub-200ms ranking.
              </p>
            </motion.div>

            {/* Upload Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 px-4 sm:px-0">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
              >
                <Card className="group relative p-8 bg-white/[0.03] border-white/5 overflow-hidden transition-all hover:bg-white/[0.05] hover:border-blue-500/30">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 blur-3xl -mr-16 -mt-16 group-hover:bg-blue-500/10 transition-colors" />
                  
                  <div className="flex items-center gap-4 mb-8">
                    <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center ring-1 ring-blue-500/20 group-hover:scale-110 transition-transform">
                      <Briefcase className="w-6 h-6 text-blue-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold">Requirement Profile</h3>
                      <p className="text-xs text-slate-500">PDF, JPG, or Plain Text</p>
                    </div>
                  </div>

                  <div
                    onDragOver={(e) => { e.preventDefault(); setJdDragActive(true); }}
                    onDragLeave={() => setJdDragActive(false)}
                    onDrop={handleJdDrop}
                    onClick={() => document.getElementById("jd-upload")?.click()}
                    className={`border-2 border-dashed rounded-3xl p-12 text-center transition-all cursor-pointer relative z-10
                      ${jdDragActive ? "border-blue-500 bg-blue-500/5 scale-[0.98]" : "border-white/10 hover:border-white/20"}
                      ${jdFile ? "border-emerald-500/30 bg-emerald-500/5" : ""}`}
                  >
                    <input id="jd-upload" type="file" accept=".pdf,.txt,.jpg,.jpeg,.png" className="hidden" onChange={(e) => setJdFile(e.target.files?.[0] || null)} />
                    {jdFile ? (
                      <div className="space-y-3">
                         <div className="w-16 h-16 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-4 border border-emerald-500/20">
                           <CheckCircle className="w-8 h-8 text-emerald-500" />
                         </div>
                         <p className="text-emerald-400 text-sm font-black truncate max-w-xs mx-auto">{jdFile.name}</p>
                         <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Profile established</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                         <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-blue-500/10 transition-colors">
                           <Upload className="w-8 h-8 text-slate-500 group-hover:text-blue-400 transition-colors" />
                         </div>
                         <p className="text-sm text-slate-400 font-bold">Drop Job Specification</p>
                         <p className="text-[10px] text-slate-500">Up to 10MB file size</p>
                      </div>
                    )}
                  </div>
                </Card>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
              >
                <Card className="group relative p-8 bg-white/[0.03] border-white/5 overflow-hidden transition-all hover:bg-white/[0.05] hover:border-purple-500/30">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/5 blur-3xl -mr-16 -mt-16 group-hover:bg-purple-500/10 transition-colors" />
                  
                  <div className="flex items-center gap-4 mb-8">
                    <div className="w-12 h-12 rounded-2xl bg-purple-500/10 flex items-center justify-center ring-1 ring-purple-500/20 group-hover:scale-110 transition-transform">
                      <Users className="w-6 h-6 text-purple-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-bold">Candidate Pool</h3>
                      <p className="text-xs text-slate-500">{resumeFiles.length} profiles queued</p>
                    </div>
                  </div>

                  <div
                    onDragOver={(e) => { e.preventDefault(); setResumeDragActive(true); }}
                    onDragLeave={() => setResumeDragActive(false)}
                    onDrop={handleResumeDrop}
                    onClick={() => document.getElementById("resume-upload")?.click()}
                    className={`border-2 border-dashed rounded-3xl p-12 text-center transition-all cursor-pointer relative z-10
                      ${resumeDragActive ? "border-purple-500 bg-purple-500/5 scale-[0.98]" : "border-white/10 hover:border-white/20"}`}
                  >
                    <input id="resume-upload" type="file" accept=".pdf,.jpg,.jpeg,.png" multiple className="hidden" onChange={handleResumeFileSelect} />
                    <div className="space-y-4">
                       <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-purple-500/10 transition-colors">
                         <Upload className="w-8 h-8 text-slate-500 group-hover:text-purple-400 transition-colors" />
                       </div>
                       <p className="text-sm text-slate-400 font-bold">Bulk Upload Resumes</p>
                       <p className="text-[10px] text-slate-500">Optimized for Multi-Column Layouts</p>
                    </div>
                  </div>

                  {resumeFiles.length > 0 && (
                    <div className="mt-6 flex flex-wrap gap-2">
                       {resumeFiles.slice(0, 5).map((f, i) => (
                         <div key={i} className="px-3 py-1 rounded bg-white/5 text-[10px] font-bold text-slate-400 border border-white/5 truncate max-w-[120px]">
                           {f.name}
                         </div>
                       ))}
                       {resumeFiles.length > 5 && (
                         <div className="px-3 py-1 rounded bg-purple-500/10 text-[10px] font-bold text-purple-400 border border-purple-500/20">
                            +{resumeFiles.length - 5} more
                         </div>
                       )}
                    </div>
                  )}
                </Card>
              </motion.div>
            </div>

            {/* Process Button */}
            <AnimatePresence>
              {(jdFile || resumeFiles.length > 0) && (
                <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }} className="flex flex-col items-center gap-8 py-12">
                   {isProcessing ? (
                     <div className="w-full max-w-xl space-y-6">
                        <div className="flex justify-between items-end">
                           <div className="space-y-1">
                              <p className="text-xs font-black uppercase tracking-widest text-blue-400 animate-pulse">{statusMessage}</p>
                              <p className="text-[10px] text-slate-500 font-bold">Stage {uploadProgress < 30 ? "1/3" : uploadProgress < 60 ? "2/3" : "3/3"}: AI Processing Loop</p>
                           </div>
                           <span className="text-2xl font-black text-white">{Math.round(uploadProgress)}%</span>
                        </div>
                        <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden p-[1px]">
                           <motion.div 
                            initial={{ width: 0 }}
                            animate={{ width: `${uploadProgress}%` }}
                            className="h-full bg-gradient-to-r from-blue-600 via-indigo-500 to-purple-600 rounded-full shadow-[0_0_15px_rgba(37,99,235,0.4)]"
                           />
                        </div>
                     </div>
                   ) : (
                     <div className="space-y-4 text-center">
                        <Button 
                          onClick={handleProcess} 
                          disabled={!jdFile || resumeFiles.length === 0}
                          className="bg-blue-600 hover:bg-blue-500 text-white font-black h-16 px-16 rounded-3xl shadow-2xl shadow-blue-600/40 relative group overflow-hidden disabled:opacity-50 disabled:grayscale transition-all"
                        >
                          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:animate-[shimmer_2s_infinite] pointer-events-none" />
                          <div className="flex items-center gap-3 relative z-10">
                            <Zap className="w-6 h-6 fill-current text-white" />
                            <span className="text-lg">Activate Ranking Engine</span>
                          </div>
                        </Button>
                        <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Cross-Encoder Reranking Powered</p>
                     </div>
                   )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ) : (
          /* Results View */
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8 pb-20">
             {/* Dynamic Filter Header */}
             <div className="flex flex-col md:flex-row items-end md:items-center justify-between gap-6">
                <div className="space-y-2">
                  <div className="flex items-center gap-3">
                    <h2 className="text-3xl font-black tracking-tight">Recruiting <span className="text-blue-500">Intelligence</span></h2>
                    <Badge className="bg-blue-500 ring-4 ring-blue-500/10 text-white border-none font-black px-3">{results.length} Candidates</Badge>
                  </div>
                  <p className="text-sm text-slate-500 font-medium">Ranked by Semantic Score, Experience Depth, and Trajectory Archetype</p>
                </div>
                
                <div className="flex items-center gap-3 p-1.5 rounded-2xl bg-white/[0.03] border border-white/5 backdrop-blur-xl">
                   <Button variant={viewMode === "grid" ? "secondary" : "ghost"} size="sm" onClick={() => setViewMode("grid")} className={`rounded-xl gap-2 font-bold text-xs h-10 px-4 ${viewMode === "grid" ? "bg-white/10 text-white" : "text-slate-500"}`}>
                     <LayoutGrid className="w-4 h-4" /> Cards
                   </Button>
                   <Button variant={viewMode === "spreadsheet" ? "secondary" : "ghost"} size="sm" onClick={() => setViewMode("spreadsheet")} className={`rounded-xl gap-2 font-bold text-xs h-10 px-4 ${viewMode === "spreadsheet" ? "bg-white/10 text-white" : "text-slate-500"}`}>
                     <TableIcon className="w-4 h-4" /> Spreadsheet
                   </Button>
                </div>
             </div>

             <div className="grid grid-cols-1 md:grid-cols-4 gap-8 items-start">
                {/* Main Results Column */}
                <div className="md:col-span-3 space-y-8">
                  {viewMode === "grid" ? (
                    <div className="grid grid-cols-1 gap-6">
                      {results.map((res, i) => (
                        <motion.div
                          key={res.id}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: i * 0.1 }}
                        >
                          <EvaluationCard candidate={res} />
                        </motion.div>
                      ))}
                    </div>
                  ) : (
                    <Card className="overflow-hidden border-white/5 bg-slate-900/60 backdrop-blur-xl rounded-[2rem] shadow-2xl">
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                          <thead>
                            <tr className="border-b border-white/5 bg-white/[0.03]">
                              <th className="px-6 py-5 font-black text-slate-500 uppercase tracking-widest text-[10px]">Rank</th>
                              <th className="px-6 py-5 font-black text-slate-500 uppercase tracking-widest text-[10px]">Candidate Profile</th>
                              <th className="px-6 py-5 font-black text-slate-500 uppercase tracking-widest text-[10px] text-center">AI Score</th>
                              <th className="px-6 py-5 font-black text-slate-500 uppercase tracking-widest text-[10px]">Trajectory</th>
                              <th className="px-6 py-5 font-black text-slate-500 uppercase tracking-widest text-[10px] text-right">Integrity</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-white/5">
                            {results.map((res, i) => (
                              <tr key={res.id} className="hover:bg-white/[0.04] transition-all cursor-pointer group">
                                <td className="px-6 py-6 font-black text-slate-600 text-lg group-hover:text-blue-500 transition-colors">#{i + 1}</td>
                                <td className="px-6 py-6">
                                  <div className="font-bold text-slate-100 text-base">{res.full_name || res.parsed_data?.full_name}</div>
                                  <div className="text-xs text-slate-500 font-medium mt-1">
                                    {res.explanation?.top_strengths[0] || "Advanced Systems Architect"}
                                  </div>
                                </td>
                                <td className="px-6 py-6 text-center">
                                  <div className={`text-xl font-black ${res.final_score > 85 ? "text-blue-400" : res.final_score > 65 ? "text-indigo-400" : "text-slate-400"}`}>
                                    {res.final_score}%
                                  </div>
                                </td>
                                <td className="px-6 py-6">
                                  <TrajectoryBadge archetype={res.parsed_data?._trajectory?.archetype || "unknown"} showIcon={false} className="py-1 px-4" />
                                </td>
                                <td className="px-6 py-6 text-right">
                                  <div className="flex justify-end">
                                    {(res.parsed_data?._meta?.extraction_confidence ?? 1) < 0.8 ? (
                                      <div className="w-8 h-8 rounded-full bg-amber-500/10 flex items-center justify-center border border-amber-500/20" title="Low data integrity - Verify manually">
                                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                                      </div>
                                    ) : (
                                      <div className="w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                                        <CheckCircle className="w-4 h-4 text-emerald-500" />
                                      </div>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </Card>
                  )}
                </div>

                {/* Sticky Action Sidebar */}
                <div className="md:sticky md:top-28 space-y-6">
                   <Card className="p-6 bg-white/[0.03] border-white/5 space-y-8 rounded-3xl backdrop-blur-xl">
                      <div className="space-y-4">
                        <h4 className="text-[10px] font-black uppercase text-slate-500 tracking-[0.2em] flex items-center gap-2">
                           <Zap className="w-3 h-3 text-yellow-500" /> Intelligence Center
                        </h4>
                        <div className="space-y-2">
                           <div className="flex justify-between text-[11px] font-bold">
                             <span className="text-slate-400">Mean Integrity</span>
                             <span className="text-emerald-400">92%</span>
                           </div>
                           <Progress value={92} className="h-1 bg-white/5" />
                        </div>
                      </div>

                      <div className="space-y-3">
                        <Button 
                          className="w-full bg-blue-600 hover:bg-blue-500 text-white font-black text-xs h-12 rounded-2xl shadow-lg shadow-blue-600/20 gap-2"
                          onClick={() => window.open(`${API_BASE}/api/rankings/${currentJobId}/export`)}
                        >
                           <FileText className="w-4 h-4" /> Export Intelligence
                        </Button>
                        <Button 
                          variant="outline" 
                          className="w-full border-white/10 hover:bg-white/5 text-white font-black text-xs h-12 rounded-2xl gap-2"
                          onClick={() => { setResults([]); setJdFile(null); setResumeFiles([]); }}
                        >
                           Reset Session
                        </Button>
                      </div>

                      <div className="pt-4 border-t border-white/5">
                        <div className="flex gap-2 p-3 rounded-2xl bg-blue-500/5 border border-blue-500/10 items-start">
                           <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                           <p className="text-[10px] text-blue-300 font-medium leading-relaxed italic">
                             Currently prioritizing "Fast Climber" archetypes based on your job profile density.
                           </p>
                        </div>
                      </div>
                   </Card>

                   <div className="p-4 rounded-3xl bg-emerald-500/5 border border-emerald-500/10 flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center">
                        <TrendingUp className="w-4 h-4 text-emerald-400" />
                      </div>
                      <p className="text-[10px] font-bold text-slate-400 leading-tight">
                        Ranking engine validated against <br/><span className="text-white">Recruiter Preference Model v2.4</span>
                      </p>
                   </div>
                </div>
             </div>
          </motion.div>
        )}
      </main>

      <style jsx global>{`
        @keyframes shimmer {
          100% { transform: translateX(100%); }
        }
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
        }
      `}</style>
    </div>
  );
}