"use client";

import { motion } from "framer-motion";
import { ShieldAlert, Brain, CheckCircle2, XCircle, ArrowUpRight, ArrowDownRight } from "lucide-react";
import type { Candidate } from "@/store/workspace";

export function AtsVsAiComponent({ candidateA, candidateB }: { candidateA: Candidate; candidateB: Candidate }) {
  // We assume candidateB is the keyword stuffer (Traditional ATS winner)
  // and candidateA is the true specialist (AI Winner)

  return (
    <div className="w-full rounded-xl border border-white/[0.08] bg-black/40 overflow-hidden mt-4">
      <div className="p-3 border-b border-white/[0.06] bg-white/[0.02]">
        <h3 className="text-xs font-bold text-white uppercase tracking-widest flex items-center gap-2">
          <GitCompare className="w-4 h-4 text-cyan-400" /> Head-to-Head: ATS vs AI
        </h3>
      </div>
      
      <div className="grid grid-cols-2 divide-x divide-white/[0.06]">
        {/* TRADITIONAL ATS VIEW */}
        <div className="p-4 space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            <h4 className="text-[10px] font-bold text-rose-400 uppercase tracking-widest">Traditional ATS</h4>
          </div>
          
          <div className="p-3 rounded bg-white/[0.02] border border-white/[0.04]">
            <p className="text-xs text-white/80 font-medium mb-1">{candidateB.name}</p>
            <p className="text-[10px] text-white/50">{candidateB.title}</p>
            
            <div className="mt-3 flex items-center justify-between">
              <span className="text-[10px] text-white/40">Keyword Match:</span>
              <span className="text-xs font-mono font-bold text-emerald-400">42 hits</span>
            </div>
            <div className="mt-2 flex items-center justify-between">
              <span className="text-[10px] text-white/40">ATS Confidence:</span>
              <span className="text-xs font-mono font-bold text-emerald-400 flex items-center gap-1">
                82% <ArrowUpRight className="w-3 h-3" />
              </span>
            </div>
          </div>
          
          <div className="text-xs text-white/60 space-y-2">
            <div className="flex items-start gap-1.5">
              <XCircle className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
              <span>Keyword stuffed resume (AI, LLM, Vector DB)</span>
            </div>
            <div className="flex items-start gap-1.5">
              <XCircle className="w-3.5 h-3.5 text-rose-400 shrink-0 mt-0.5" />
              <span>No retrieval ownership</span>
            </div>
          </div>
        </div>

        {/* RECRUITER INTELLIGENCE VIEW */}
        <div className="p-4 space-y-4 bg-cyan-900/[0.03]">
          <div className="flex items-center gap-2 mb-2">
            <Brain className="w-4 h-4 text-cyan-400" />
            <h4 className="text-[10px] font-bold text-cyan-400 uppercase tracking-widest">Recruiter Intelligence</h4>
          </div>
          
          <div className="p-3 rounded bg-cyan-400/[0.05] border border-cyan-400/20 shadow-[0_0_15px_rgba(34,211,238,0.05)]">
            <p className="text-xs text-white/90 font-bold mb-1">{candidateA.name}</p>
            <p className="text-[10px] text-cyan-400/70">{candidateA.title}</p>
            
            <div className="mt-3 flex items-center justify-between">
              <span className="text-[10px] text-white/50">Production Score:</span>
              <span className="text-xs font-mono font-bold text-cyan-400">92/100</span>
            </div>
            <div className="mt-2 flex items-center justify-between">
              <span className="text-[10px] text-white/50">AI Confidence:</span>
              <span className="text-xs font-mono font-bold text-cyan-400 flex items-center gap-1">
                {candidateA.matchScore}% <ArrowUpRight className="w-3 h-3" />
              </span>
            </div>
          </div>

          <div className="text-xs text-cyan-100/70 space-y-2">
            <div className="flex items-start gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
              <span>Built ranking systems at scale</span>
            </div>
            <div className="flex items-start gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
              <span>Owned retrieval infrastructure</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function GitCompare(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="18" cy="18" r="3" />
      <circle cx="6" cy="6" r="3" />
      <path d="M13 6h3a2 2 0 0 1 2 2v7" />
      <path d="M11 18H8a2 2 0 0 1-2-2V9" />
    </svg>
  );
}
