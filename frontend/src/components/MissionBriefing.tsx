"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  Upload,
  Crosshair,
  Sparkles,
  Database,
  CheckCircle2,
  Zap,
} from "lucide-react";

interface MissionBriefingProps {
  onLaunch: (jdText: string, signals: string[]) => void;
}

const SIGNAL_KEYWORDS: Record<string, string[]> = {
  Retrieval: ["retrieval", "search", "query", "information retrieval", "ir"],
  Ranking: ["ranking", "rank", "relevance", "ndcg", "mrr"],
  "Vector Search": ["vector", "embedding", "faiss", "ann", "similarity", "dense"],
  "Production ML": ["production", "deploy", "serving", "inference", "scale", "pipeline"],
  "Startup Experience": ["startup", "founding", "early-stage", "scrappy", "0-to-1"],
  "Evaluation Frameworks": ["evaluation", "metrics", "a/b test", "benchmark", "offline eval"],
  "LLM / RAG": ["llm", "rag", "large language model", "gpt", "transformer", "generative"],
  NLP: ["nlp", "natural language", "tokeniz", "bert", "language model"],
  Leadership: ["lead", "manage", "principal", "staff", "architect", "director"],
  Infrastructure: ["infrastructure", "distributed", "microservice", "kubernetes", "cloud"],
};

function extractSignals(text: string): string[] {
  const lower = text.toLowerCase();
  const found: string[] = [];
  for (const [signal, keywords] of Object.entries(SIGNAL_KEYWORDS)) {
    if (keywords.some((kw) => lower.includes(kw))) {
      found.push(signal);
    }
  }
  return found;
}

export function MissionBriefing({ onLaunch }: MissionBriefingProps) {
  const [jdText, setJdText] = useState("");
  const [signals, setSignals] = useState<string[]>([]);
  const [uploaded, setUploaded] = useState(false);

  const handleTextChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const text = e.target.value;
      setJdText(text);
      setSignals(extractSignals(text));
    },
    []
  );

  const handleUploadClick = useCallback(() => {
    setUploaded(true);
  }, []);

  const canLaunch = jdText.trim().length > 20 && uploaded;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      {/* Backdrop with grid pattern */}
      <div className="absolute inset-0 bg-[#0A0C10]">
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-cyan-400/[0.03] via-transparent to-transparent" />
      </div>

      {/* Content */}
      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="relative w-full max-w-4xl"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-400/[0.08] border border-cyan-400/20 mb-4">
            <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
            <span className="text-[10px] font-mono text-cyan-400 tracking-widest uppercase">
              SignalHire Intelligence System
            </span>
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">
            Mission Briefing
          </h1>
          <p className="text-sm text-white/30 mt-2">
            Define your target profile. Upload your candidate universe. Launch
            the investigation.
          </p>
        </div>

        {/* Two-column layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left: JD Input */}
          <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-5">
            <div className="flex items-center gap-2 mb-3">
              <FileText className="w-4 h-4 text-cyan-400" />
              <h2 className="text-xs font-bold text-white/60 tracking-wider uppercase">
                Job Description — Mission Brief
              </h2>
            </div>
            <textarea
              value={jdText}
              onChange={handleTextChange}
              placeholder="Paste the job description here...&#10;&#10;Example: We're looking for a Principal Search Engineer with deep experience in retrieval systems, ranking infrastructure, and evaluation frameworks. Ideal candidates have built production ML systems at scale, worked with vector search technologies like FAISS, and have experience leading technical teams..."
              className="w-full h-52 bg-white/[0.03] border border-white/[0.08] rounded-lg px-4 py-3 text-sm text-white/80 placeholder:text-white/15 resize-none focus:outline-none focus:border-cyan-400/30 focus:ring-1 focus:ring-cyan-400/20 transition-all font-mono text-xs leading-relaxed"
            />

            {/* Extracted Signals */}
            <AnimatePresence>
              {signals.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mt-3 overflow-hidden"
                >
                  <p className="text-[10px] text-white/30 uppercase tracking-wider mb-2">
                    Required Signals Detected
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {signals.map((signal) => (
                      <motion.span
                        key={signal}
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="inline-flex items-center gap-1 px-2 py-1 text-[10px] font-medium rounded-md bg-cyan-400/[0.1] text-cyan-400 border border-cyan-400/20"
                      >
                        <Sparkles className="w-2.5 h-2.5" />
                        {signal}
                      </motion.span>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Right: Upload */}
          <div className="rounded-xl border border-white/[0.08] bg-white/[0.02] p-5">
            <div className="flex items-center gap-2 mb-3">
              <Database className="w-4 h-4 text-cyan-400" />
              <h2 className="text-xs font-bold text-white/60 tracking-wider uppercase">
                Candidate Universe
              </h2>
            </div>

            <button
              type="button"
              onClick={handleUploadClick}
              className={`w-full h-52 rounded-lg border-2 border-dashed flex flex-col items-center justify-center gap-3 transition-all ${
                uploaded
                  ? "border-emerald-400/30 bg-emerald-400/[0.04]"
                  : "border-white/[0.1] bg-white/[0.02] hover:border-cyan-400/30 hover:bg-cyan-400/[0.02]"
              }`}
            >
              {uploaded ? (
                <motion.div
                  initial={{ opacity: 0, scale: 0.5 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex flex-col items-center gap-2"
                >
                  <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                  <span className="text-sm font-semibold text-emerald-400">
                    100,000 candidates detected
                  </span>
                  <span className="text-[10px] text-emerald-400/50 font-mono">
                    CANDIDATE_UNIVERSE_V2.CSV — 2.4 GB
                  </span>
                  <div className="flex gap-2 mt-1">
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/[0.05] text-white/30">
                      47,230 Engineers
                    </span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/[0.05] text-white/30">
                      12,890 Researchers
                    </span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/[0.05] text-white/30">
                      39,880 Others
                    </span>
                  </div>
                </motion.div>
              ) : (
                <>
                  <Upload className="w-8 h-8 text-white/20" />
                  <span className="text-sm text-white/30">
                    Drop candidate CSV or click to upload
                  </span>
                  <span className="text-[10px] text-white/15 font-mono">
                    CSV, JSON, or LinkedIn Export
                  </span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Launch Button */}
        <div className="mt-8 flex justify-center">
          <motion.button
            whileHover={canLaunch ? { scale: 1.02 } : {}}
            whileTap={canLaunch ? { scale: 0.98 } : {}}
            onClick={() => canLaunch && onLaunch(jdText, signals)}
            disabled={!canLaunch}
            className={`relative group flex items-center gap-3 px-10 py-4 rounded-xl text-sm font-bold tracking-wide uppercase transition-all ${
              canLaunch
                ? "bg-cyan-400 text-[#0A0C10] shadow-[0_0_40px_rgba(34,211,238,0.3)] hover:shadow-[0_0_60px_rgba(34,211,238,0.5)]"
                : "bg-white/[0.05] text-white/20 cursor-not-allowed"
            }`}
          >
            <Crosshair
              className={`w-5 h-5 ${
                canLaunch ? "text-[#0A0C10]" : "text-white/15"
              }`}
            />
            Launch Investigation
            {canLaunch && (
              <Zap className="w-4 h-4 text-[#0A0C10]" />
            )}
            {canLaunch && (
              <div className="absolute inset-0 rounded-xl bg-cyan-400/20 animate-pulse pointer-events-none" />
            )}
          </motion.button>
        </div>

        {/* Status */}
        <p className="text-center text-[10px] text-white/15 mt-4 font-mono tracking-wider">
          {!jdText.trim()
            ? "STEP 1: PASTE JOB DESCRIPTION"
            : !uploaded
            ? "STEP 2: UPLOAD CANDIDATE UNIVERSE"
            : "READY TO LAUNCH INVESTIGATION"}
        </p>
      </motion.div>
    </motion.div>
  );
}
