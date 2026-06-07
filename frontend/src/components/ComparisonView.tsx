"use client";

import { motion } from "framer-motion";
import {
  X,
  Trophy,
  ArrowUp,
  ArrowDown,
  Minus,
  Swords,
  Brain,
  ShieldAlert,
} from "lucide-react";
import type { Candidate } from "@/store/workspace";

interface ComparisonViewProps {
  candidateA: Candidate;
  candidateB: Candidate;
  onClose: () => void;
}

type Dimension = {
  label: string;
  key: keyof Candidate["scores"];
};

const DIMENSIONS: Dimension[] = [
  { label: "Technical Fit", key: "technical" },
  { label: "Production Ownership", key: "production" },
  { label: "Leadership", key: "leadership" },
  { label: "Evaluation Experience", key: "evaluation" },
  { label: "Hireability", key: "hireability" },
];

export function ComparisonView({
  candidateA,
  candidateB,
  onClose,
}: ComparisonViewProps) {
  const aTotal = Object.values(candidateA.scores).reduce((a, b) => a + b, 0);
  const bTotal = Object.values(candidateB.scores).reduce((a, b) => a + b, 0);
  const aWins = DIMENSIONS.filter(
    (d) => candidateA.scores[d.key] > candidateB.scores[d.key]
  ).length;
  const bWins = DIMENSIONS.filter(
    (d) => candidateB.scores[d.key] > candidateA.scores[d.key]
  ).length;

  const winner = aTotal >= bTotal ? candidateA : candidateB;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-6"
    >
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-md"
        onClick={onClose}
      />

      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="relative w-full max-w-4xl bg-[#0C0E14] rounded-2xl border border-white/[0.08] shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
      >
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.06] shrink-0">
          <div className="flex items-center gap-3">
            <Swords className="w-5 h-5 text-cyan-400" />
            <div>
              <h2 className="text-sm font-bold text-white">
                Intelligence Comparison:{" "}
                <span className="text-cyan-400">{candidateA.name}</span> vs{" "}
                <span className="text-rose-400">{candidateB.name}</span>
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-white/[0.05] text-white/40 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="overflow-y-auto p-6 space-y-6">
          
          {/* CONFIDENCE SHIFT SECTION */}
          <div className="w-full rounded-xl border border-white/[0.06] bg-black/40 overflow-hidden">
            <div className="p-3 border-b border-white/[0.06] bg-white/[0.02]">
              <h3 className="text-xs font-bold text-white uppercase tracking-widest">Confidence Shift</h3>
            </div>
            
            <div className="grid grid-cols-2 divide-x divide-white/[0.06]">
              {/* ATS View */}
              <div className="p-4 bg-rose-900/[0.02]">
                <div className="flex items-center gap-2 mb-3">
                  <ShieldAlert className="w-4 h-4 text-rose-400" />
                  <span className="text-[10px] text-rose-400 uppercase tracking-widest font-bold">Traditional ATS</span>
                </div>
                <div className="flex items-end gap-3 mb-2">
                  <p className="text-sm font-medium text-white/80">{candidateB.name}</p>
                  <p className="text-2xl font-mono font-bold text-emerald-400">82%</p>
                </div>
                <p className="text-[10px] text-white/50 mb-3 uppercase tracking-widest">Initial Confidence</p>
                
                <div className="p-3 rounded bg-white/[0.02] border border-white/[0.04]">
                  <p className="text-xs text-white/60">Candidate B selected due to raw keyword overlap (42 hits). High initial score before evidence review.</p>
                </div>
              </div>

              {/* Recruiter Intelligence View */}
              <div className="p-4 bg-cyan-900/[0.03]">
                <div className="flex items-center gap-2 mb-3">
                  <Brain className="w-4 h-4 text-cyan-400" />
                  <span className="text-[10px] text-cyan-400 uppercase tracking-widest font-bold">Recruiter Intelligence</span>
                </div>
                <div className="flex items-end gap-3 mb-2">
                  <p className="text-sm font-medium text-white">{candidateA.name}</p>
                  <p className="text-2xl font-mono font-bold text-cyan-400">96%</p>
                </div>
                <p className="text-[10px] text-white/50 mb-3 uppercase tracking-widest">Calibrated Confidence</p>
                
                <div className="p-3 rounded bg-cyan-400/[0.05] border border-cyan-400/20 shadow-[0_0_15px_rgba(34,211,238,0.05)]">
                  <p className="text-xs text-cyan-100/70">Candidate A promoted over Candidate B due to proven retrieval infrastructure ownership and production scale. Candidate B match score dropped to {candidateB.matchScore}% after evidence review.</p>
                </div>
              </div>
            </div>
          </div>

          {/* HEAD TO HEAD METRICS */}
          <div>
            <h3 className="text-xs font-bold text-white/40 uppercase tracking-widest mb-4">Metric Breakdown</h3>
            <div className="space-y-3">
              {DIMENSIONS.map((dim, index) => {
                const scoreA = candidateA.scores[dim.key];
                const scoreB = candidateB.scores[dim.key];
                const diff = scoreA - scoreB;
                const aWin = diff > 0;
                const tie = diff === 0;

                return (
                  <motion.div
                    key={dim.key}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.08 }}
                    className="grid grid-cols-[1fr_auto_1fr] gap-4 items-center"
                  >
                    {/* A Score */}
                    <div className="flex items-center gap-3">
                      <div className="flex-1 flex justify-end">
                          <div
                            className={`h-2 rounded-full ${aWin ? "bg-cyan-400" : tie ? "bg-white/20" : "bg-rose-400/40"}`}
                            style={{ width: `${scoreA}%` }}
                          />
                      </div>
                      <span className={`text-sm font-mono font-bold w-8 text-right ${aWin ? "text-cyan-400" : tie ? "text-white/50" : "text-rose-400/70"}`}>
                        {scoreA}
                      </span>
                    </div>

                    {/* Center label */}
                    <div className="flex flex-col items-center w-36">
                      <span className="text-[10px] text-white/40 font-medium uppercase tracking-wider text-center">
                        {dim.label}
                      </span>
                      <div className="flex items-center gap-1 mt-0.5">
                        {aWin ? (
                          <ArrowUp className="w-3 h-3 text-cyan-400" />
                        ) : tie ? (
                          <Minus className="w-3 h-3 text-white/20" />
                        ) : (
                          <ArrowDown className="w-3 h-3 text-rose-400" />
                        )}
                        <span className={`text-[10px] font-mono ${aWin ? "text-cyan-400" : tie ? "text-white/20" : "text-rose-400"}`}>
                          {tie ? "TIE" : `${Math.abs(diff)} pts`}
                        </span>
                      </div>
                    </div>

                    {/* B Score */}
                    <div className="flex items-center gap-3">
                      <span className={`text-sm font-mono font-bold w-8 ${!aWin && !tie ? "text-rose-400" : tie ? "text-white/50" : "text-white/20"}`}>
                        {scoreB}
                      </span>
                      <div className="flex-1">
                        <div
                          className={`h-2 rounded-full ${!aWin && !tie ? "bg-rose-400" : tie ? "bg-white/20" : "bg-white/10"}`}
                          style={{ width: `${scoreB}%` }}
                        />
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>

        </div>

      </motion.div>
    </motion.div>
  );
}
