"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Upload, Briefcase, Sparkles, CheckCircle, Users,
  Zap, AlertTriangle, FileText, ArrowLeft, TrendingUp,
  ShieldCheck, Target, Brain, Search, BarChart3
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

type DemoCandidate = {
  candidate_id: string;
  rank: number;
  score: number;
  reasoning: string;
};

// Demo data matching our hackathon submission format
const DEMO_CANDIDATES: DemoCandidate[] = [
  { candidate_id: "CAND_0097455", rank: 1, score: 0.98, reasoning: "Senior ML Engineer with 8.2 years of experience. Strong background in retrieval systems, ranking/recommendation, vector database infrastructure. Demonstrated ability to deploy and scale production ML systems. Exceptional recruiter engagement and hireability signals." },
  { candidate_id: "CAND_0097807", rank: 2, score: 0.95, reasoning: "ML Platform Engineer with 6.5 years of experience. Strong background in retrieval systems, vector database infrastructure, evaluation frameworks (NDCG/MRR). High startup readiness with cross-functional ownership." },
  { candidate_id: "CAND_0075261", rank: 3, score: 0.93, reasoning: "Senior Data Scientist with 7.1 years of experience. Strong background in retrieval systems, ranking/recommendation. Demonstrated ability to deploy and scale production ML systems. Good recruiter engagement signals." },
  { candidate_id: "CAND_0095463", rank: 4, score: 0.91, reasoning: "AI Engineer with 5.8 years of experience. Strong background in retrieval systems, vector database infrastructure. High startup readiness with cross-functional ownership. Leadership experience including team management." },
  { candidate_id: "CAND_0042187", rank: 5, score: 0.89, reasoning: "Search Engineer with 9.3 years of experience. Strong background in retrieval systems, ranking/recommendation, evaluation frameworks (NDCG/MRR). Demonstrated ability to deploy and scale production ML systems. Limitations: limited startup exposure." },
];

const featureBreakdown = [
  { name: "Retrieval Experience", value: 85, color: "bg-blue-500" },
  { name: "Vector DB Score", value: 72, color: "bg-purple-500" },
  { name: "Production ML", value: 90, color: "bg-emerald-500" },
  { name: "Hireability", value: 78, color: "bg-amber-500" },
  { name: "Career Consistency", value: 95, color: "bg-cyan-500" },
];

export default function DashboardPage() {
  const [jdFile, setJdFile] = useState<File | null>(null);
  const [resumeFiles, setResumeFiles] = useState<File[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [results, setResults] = useState<DemoCandidate[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedCandidate, setSelectedCandidate] = useState<DemoCandidate | null>(null);

  const handleProcess = async () => {
    if (!jdFile) return;
    setIsProcessing(true);
    setUploadProgress(5);
    setStatusMessage("Parsing Job Description...");
    setError(null);

    try {
      // Simulate the pipeline stages
      await new Promise(r => setTimeout(r, 800));
      setUploadProgress(15);
      setStatusMessage("Loading 100,000 candidate embeddings...");

      await new Promise(r => setTimeout(r, 1000));
      setUploadProgress(30);
      setStatusMessage("Hybrid Retrieval: Semantic Top 5k ∪ BM25 Top 5k...");

      await new Promise(r => setTimeout(r, 1200));
      setUploadProgress(50);
      setStatusMessage("Extracting 22 recruiter features on 10k candidates...");

      await new Promise(r => setTimeout(r, 1000));
      setUploadProgress(70);
      setStatusMessage("Running LightGBM LambdaRank inference...");

      await new Promise(r => setTimeout(r, 800));
      setUploadProgress(85);
      setStatusMessage("Generating SHAP-inspired reasoning...");

      await new Promise(r => setTimeout(r, 600));
      setUploadProgress(95);
      setStatusMessage("Forensic consistency checks...");

      await new Promise(r => setTimeout(r, 400));
      setResults(DEMO_CANDIDATES);
      setUploadProgress(100);
      setStatusMessage("Complete!");
    } catch (err: unknown) {
      console.error("Processing failed:", err);
      setError(err instanceof Error ? err.message : "An unexpected error occurred.");
    } finally {
      setIsProcessing(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.9) return "text-emerald-400";
    if (score >= 0.7) return "text-blue-400";
    if (score >= 0.5) return "text-amber-400";
    return "text-red-400";
  };

  const getScoreBg = (score: number) => {
    if (score >= 0.9) return "from-emerald-500/20 to-emerald-500/5";
    if (score >= 0.7) return "from-blue-500/20 to-blue-500/5";
    if (score >= 0.5) return "from-amber-500/20 to-amber-500/5";
    return "from-red-500/20 to-red-500/5";
  };

  return (
    <div className="min-h-screen bg-[#020617] text-slate-50 selection:bg-blue-500/30">
      {/* Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/8 blur-[150px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-600/8 blur-[150px] rounded-full" />
      </div>

      {/* Header */}
      <header className="border-b border-white/5 bg-black/40 backdrop-blur-2xl sticky top-0 z-50 px-8 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <a href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-bold tracking-tight">SignalHire<span className="text-blue-500">AI</span></span>
            </a>
            <Badge className="bg-white/5 text-slate-400 border-white/10 text-[10px] font-medium">Dashboard</Badge>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-400">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Engine Online
            </div>
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
              <h1 className="text-4xl font-extrabold tracking-tight text-white leading-tight">
                Identify Top Talent{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-500">
                  Beyond the Keywords
                </span>
              </h1>
              <p className="text-slate-400 text-sm leading-relaxed">
                Upload a Job Description to activate the 5-dimension recruiter intelligence engine.
                The system will rank 100,000 candidates across 22 handcrafted features in under 35 seconds.
              </p>
            </div>

            {/* Upload Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-4xl mx-auto">
              {/* JD Upload */}
              <Card className="group relative p-8 bg-white/[0.03] border-white/5 hover:border-blue-500/30 transition-all rounded-2xl">
                <div className="flex items-center gap-4 mb-8">
                  <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center ring-1 ring-blue-500/20">
                    <Briefcase className="w-6 h-6 text-blue-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold">Job Description</h3>
                    <p className="text-xs text-slate-500">PDF, DOCX, or TXT</p>
                  </div>
                </div>
                <div
                  onClick={() => document.getElementById("jd-upload")?.click()}
                  className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all
                    ${jdFile ? "border-emerald-500/30 bg-emerald-500/5" : "border-white/10 hover:border-white/20"}`}
                >
                  <input id="jd-upload" type="file" accept=".pdf,.txt,.docx" className="hidden" onChange={(e) => setJdFile(e.target.files?.[0] || null)} />
                  {jdFile ? (
                    <div className="space-y-3">
                      <CheckCircle className="w-14 h-14 text-emerald-500 mx-auto" />
                      <p className="text-emerald-400 text-sm font-bold truncate max-w-xs mx-auto">{jdFile.name}</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <Upload className="w-14 h-14 text-slate-500 mx-auto group-hover:text-blue-400 transition-colors" />
                      <p className="text-sm text-slate-400 font-semibold">Drop Job Specification</p>
                    </div>
                  )}
                </div>
              </Card>

              {/* Resumes Upload (Optional) */}
              <Card className="group relative p-8 bg-white/[0.03] border-white/5 hover:border-purple-500/30 transition-all rounded-2xl">
                <div className="flex items-center gap-4 mb-8">
                  <div className="w-12 h-12 rounded-2xl bg-purple-500/10 flex items-center justify-center ring-1 ring-purple-500/20">
                    <Users className="w-6 h-6 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold">Candidate Pool</h3>
                    <p className="text-xs text-slate-500">{resumeFiles.length > 0 ? `${resumeFiles.length} files queued` : "100k candidates pre-loaded"}</p>
                  </div>
                </div>
                <div
                  onClick={() => document.getElementById("resume-upload")?.click()}
                  className="border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer border-white/10 hover:border-white/20 transition-all"
                >
                  <input id="resume-upload" type="file" accept=".pdf,.csv,.jsonl" multiple className="hidden" onChange={(e) => {
                    const files = Array.from(e.target.files || []);
                    setResumeFiles(prev => [...prev, ...files]);
                  }} />
                  <div className="space-y-4">
                    <div className="w-14 h-14 mx-auto rounded-2xl bg-purple-500/10 flex items-center justify-center">
                      <CheckCircle className="w-8 h-8 text-purple-400" />
                    </div>
                    <p className="text-sm text-slate-400 font-semibold">100,000 candidates pre-indexed</p>
                    <p className="text-[10px] text-slate-500">Or upload additional resumes</p>
                  </div>
                </div>
              </Card>
            </div>

            {/* Process Button */}
            <div className="flex flex-col items-center gap-8 py-8">
              {isProcessing ? (
                <div className="w-full max-w-xl space-y-6">
                  <div className="flex justify-between items-end">
                    <div className="space-y-1">
                      <p className="text-xs font-bold uppercase tracking-widest text-blue-400 animate-pulse">{statusMessage}</p>
                      <p className="text-[10px] text-slate-500 font-medium">Multi-Stage Pipeline</p>
                    </div>
                    <span className="text-2xl font-extrabold text-white">{Math.round(uploadProgress)}%</span>
                  </div>
                  <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${uploadProgress}%` }}
                      className="h-full bg-gradient-to-r from-blue-600 to-purple-600 rounded-full shadow-[0_0_15px_rgba(37,99,235,0.4)]"
                    />
                  </div>
                </div>
              ) : (
                <div className="space-y-4 text-center">
                  <Button
                    onClick={handleProcess}
                    disabled={!jdFile}
                    className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold h-14 px-14 rounded-2xl shadow-2xl shadow-blue-600/30 disabled:opacity-40 disabled:grayscale transition-all"
                  >
                    <Zap className="w-5 h-5 mr-2" /> Activate Ranking Engine
                  </Button>
                  <p className="text-[10px] text-slate-500 font-medium uppercase tracking-widest">
                    Hybrid Retrieval × 22 Features × LambdaRank
                  </p>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* ==========================================
             RESULTS VIEW
             ========================================== */
          <div className="space-y-8 pb-20">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-3xl font-extrabold tracking-tight">
                  Recruiting <span className="text-blue-500">Intelligence</span>
                </h2>
                <p className="text-sm text-slate-500 mt-1">Top 100 candidates ranked by recruiter judgment score</p>
              </div>
              <div className="flex items-center gap-3">
                <Badge className="bg-blue-500/10 text-blue-400 border-blue-500/20 font-semibold px-3">{results.length} Ranked</Badge>
                <Button
                  variant="outline"
                  size="sm"
                  className="border-white/10 hover:bg-white/5 text-slate-300 text-xs"
                  onClick={() => { setResults([]); setJdFile(null); setResumeFiles([]); setSelectedCandidate(null); }}
                >
                  <ArrowLeft className="w-3 h-3 mr-1" /> Reset
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Candidate List */}
              <div className="lg:col-span-2 space-y-3">
                {results.map((res, i) => (
                  <motion.div
                    key={res.candidate_id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.08 }}
                    onClick={() => setSelectedCandidate(res)}
                    className={`p-5 rounded-2xl border transition-all cursor-pointer group ${
                      selectedCandidate?.candidate_id === res.candidate_id
                        ? "bg-blue-500/10 border-blue-500/30"
                        : "bg-white/[0.02] border-white/5 hover:border-white/10 hover:bg-white/[0.04]"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${getScoreBg(res.score)} flex items-center justify-center text-lg font-extrabold ${getScoreColor(res.score)}`}>
                          {res.rank}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-bold text-white">{res.candidate_id}</h3>
                            {res.rank <= 3 && (
                              <Badge className="bg-amber-500/10 text-amber-400 border-amber-500/20 text-[9px]">
                                Top Pick
                              </Badge>
                            )}
                          </div>
                          <p className="text-xs text-slate-500 mt-1 line-clamp-1 max-w-md">{res.reasoning}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-xl font-extrabold ${getScoreColor(res.score)}`}>
                          {(res.score * 100).toFixed(1)}
                          <span className="text-xs font-normal text-slate-500 ml-0.5">%</span>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Detail Panel */}
              <div className="space-y-4 lg:sticky lg:top-24">
                {selectedCandidate ? (
                  <motion.div
                    key={selectedCandidate.candidate_id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <Card className="p-6 bg-white/[0.03] border-white/5 rounded-2xl space-y-6 backdrop-blur-xl">
                      <div>
                        <div className="flex items-center justify-between mb-4">
                          <h3 className="text-lg font-extrabold">{selectedCandidate.candidate_id}</h3>
                          <div className={`text-2xl font-extrabold ${getScoreColor(selectedCandidate.score)}`}>
                            #{selectedCandidate.rank}
                          </div>
                        </div>
                        <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                          selectedCandidate.score >= 0.9 ? "bg-emerald-500/10 text-emerald-400" : "bg-blue-500/10 text-blue-400"
                        }`}>
                          <TrendingUp className="w-3 h-3" />
                          Score: {(selectedCandidate.score * 100).toFixed(1)}%
                        </div>
                      </div>

                      <div>
                        <h4 className="text-[10px] uppercase font-bold text-slate-500 tracking-widest mb-3">AI Reasoning</h4>
                        <p className="text-sm text-slate-300 leading-relaxed">{selectedCandidate.reasoning}</p>
                      </div>

                      <div>
                        <h4 className="text-[10px] uppercase font-bold text-slate-500 tracking-widest mb-3">Feature Breakdown</h4>
                        <div className="space-y-3">
                          {featureBreakdown.map((f) => (
                            <div key={f.name}>
                              <div className="flex justify-between text-xs mb-1">
                                <span className="text-slate-400">{f.name}</span>
                                <span className="text-slate-300 font-semibold">{f.value}%</span>
                              </div>
                              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                                <motion.div
                                  initial={{ width: 0 }}
                                  animate={{ width: `${f.value}%` }}
                                  transition={{ delay: 0.2 }}
                                  className={`h-full rounded-full ${f.color}`}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </Card>
                  </motion.div>
                ) : (
                  <Card className="p-8 bg-white/[0.02] border-white/5 rounded-2xl text-center">
                    <Search className="w-8 h-8 text-slate-600 mx-auto mb-3" />
                    <p className="text-sm text-slate-500 font-medium">Select a candidate to view details</p>
                  </Card>
                )}

                <Card className="p-5 bg-white/[0.03] border-white/5 rounded-2xl space-y-4">
                  <h4 className="text-[10px] font-bold uppercase text-slate-500 tracking-widest">Pipeline Stats</h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between"><span className="text-slate-400">Candidates Scanned</span><span className="text-white font-semibold">100,000</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Hybrid Retrieved</span><span className="text-white font-semibold">~10,000</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Features Extracted</span><span className="text-white font-semibold">22</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Final Ranked</span><span className="text-white font-semibold">100</span></div>
                    <div className="flex justify-between"><span className="text-slate-400">Inference Time</span><span className="text-emerald-400 font-semibold">&lt;35s</span></div>
                  </div>
                </Card>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}