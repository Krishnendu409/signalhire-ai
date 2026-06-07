"use client";

import { motion } from "framer-motion";
import {
  CheckCircle,
  AlertTriangle,
  GitCompare,
} from "lucide-react";
import type { Candidate } from "@/store/workspace";

interface CandidateCardProps {
  candidate: Candidate;
  isSelected: boolean;
  onSelect: (candidate: Candidate) => void;
  onCompare: (candidate: Candidate) => void;
}

export function CandidateCard({
  candidate,
  isSelected,
  onSelect,
  onCompare,
}: CandidateCardProps) {
  const isUnranked = candidate.rank > 100;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2, transition: { duration: 0.15 } }}
      onClick={() => onSelect(candidate)}
      className={`group relative cursor-pointer rounded-lg border p-4 transition-all duration-200 ${
        isSelected
          ? "border-cyan-400/60 bg-cyan-400/[0.06] shadow-[0_0_24px_rgba(34,211,238,0.08)]"
          : "border-white/[0.08] bg-white/[0.03] hover:border-white/[0.15] hover:bg-white/[0.05]"
      }`}
    >
      {/* Top row: Rank + Name + Compare */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          {/* Rank badge */}
          <div
            className={`flex items-center justify-center w-8 h-8 rounded-md text-xs font-bold shrink-0 ${
              candidate.rank <= 3
                ? "bg-cyan-400/20 text-cyan-400 border border-cyan-400/30"
                : candidate.rank <= 10
                ? "bg-white/[0.08] text-white/70 border border-white/[0.12]"
                : isUnranked
                ? "bg-rose-500/10 text-rose-400/70 border border-rose-500/20"
                : "bg-white/[0.05] text-white/40 border border-white/[0.08]"
            }`}
          >
            {isUnranked ? "—" : `#${candidate.rank}`}
          </div>

          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-white truncate">
              {candidate.name}
            </h3>
            <p className="text-xs text-white/50 truncate">{candidate.title}</p>
          </div>
        </div>

        {/* Compare button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onCompare(candidate);
          }}
          className="flex items-center gap-1 px-2 py-1 text-[10px] font-medium text-white/40 rounded border border-white/[0.08] hover:border-cyan-400/40 hover:text-cyan-400 transition-all opacity-0 group-hover:opacity-100"
        >
          <GitCompare className="w-3 h-3" />
          Compare
        </button>
      </div>

      {/* Trajectory */}
      <div className="flex items-center gap-1 mt-2.5">
        {candidate.trajectory.map((company, i) => (
          <span key={i} className="flex items-center text-[10px] text-white/40">
            <span className="text-white/60 font-medium">{company}</span>
            {i < candidate.trajectory.length - 1 && (
              <span className="mx-1 text-white/20">→</span>
            )}
          </span>
        ))}
      </div>

      {/* Match score bar */}
      <div className="mt-3 flex items-center gap-2">
        <div className="flex-1 h-1 bg-white/[0.06] rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${candidate.matchScore}%` }}
            transition={{ delay: 0.3, duration: 0.6, ease: "easeOut" }}
            className={`h-full rounded-full ${
              candidate.matchScore >= 85
                ? "bg-cyan-400"
                : candidate.matchScore >= 70
                ? "bg-cyan-400/60"
                : candidate.matchScore >= 50
                ? "bg-amber-400/60"
                : "bg-rose-400/60"
            }`}
          />
        </div>
        <span
          className={`text-xs font-mono font-bold ${
            candidate.matchScore >= 85
              ? "text-cyan-400"
              : candidate.matchScore >= 70
              ? "text-white/60"
              : candidate.matchScore >= 50
              ? "text-amber-400"
              : "text-rose-400"
          }`}
        >
          {candidate.matchScore}%
        </span>
      </div>

      {/* Why Here signals */}
      <div className="mt-3 space-y-1">
        <span className="text-[10px] font-semibold text-emerald-400/70 tracking-wider uppercase">
          Why Here
        </span>
        <div className="flex flex-wrap gap-1.5">
          {candidate.whyHere.slice(0, 4).map((signal) => (
            <span
              key={signal}
              className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] rounded bg-emerald-400/[0.08] text-emerald-400/80 border border-emerald-400/[0.15]"
            >
              <CheckCircle className="w-2.5 h-2.5" />
              {signal}
            </span>
          ))}
        </div>
      </div>

      {/* Risks */}
      {candidate.risks.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {candidate.risks.slice(0, 2).map((risk) => (
            <span
              key={risk}
              className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] rounded bg-rose-400/[0.06] text-rose-400/60 border border-rose-400/[0.1]"
            >
              <AlertTriangle className="w-2.5 h-2.5" />
              {risk}
            </span>
          ))}
        </div>
      )}

      {/* ID watermark */}
      <div className="mt-3 text-[9px] font-mono text-white/15 tracking-wider">
        {candidate.id}
      </div>
    </motion.div>
  );
}
