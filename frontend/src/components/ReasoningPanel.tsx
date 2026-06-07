"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  Route,
  FileText,
  Search,
  UserCheck,
  ShieldAlert,
  X,
  Crosshair,
  ArrowDown,
  Brain,
  CheckCircle2,
  XCircle,
  BarChart3,
  BookOpen
} from "lucide-react";
import { CareerTimeline } from "@/components/CareerTimeline";
import type { Candidate } from "@/store/workspace";
import { AtsVsAiComponent } from "./AtsVsAiComponent";
import { useWorkspaceStore } from "@/store/workspace";

interface ReasoningPanelProps {
  candidate: Candidate | null;
  onClose?: () => void;
}

export function ReasoningPanel({ candidate, onClose }: ReasoningPanelProps) {
  const allCandidates = useWorkspaceStore(state => state.candidates);
  
  if (!candidate) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-20 px-6">
        <div className="w-16 h-16 rounded-full border border-white/[0.08] bg-white/[0.02] flex items-center justify-center mb-6 shadow-[0_0_30px_rgba(34,211,238,0.05)]">
          <Route className="w-8 h-8 text-cyan-400/40" />
        </div>
        <p className="text-sm font-medium text-white/60 text-center leading-relaxed">
          Select a candidate to inspect
          <br />
          decision traces.
        </p>
      </div>
    );
  }

  const isUnranked = candidate.rank > 100;

  // We find a keyword stuffer candidate for the ATS vs AI comparison
  const keywordStuffer = allCandidates.find(c => c.name === "Amanda Torres" || c.name === "Kevin Park") || allCandidates[allCandidates.length - 1];

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={candidate.id}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        transition={{ duration: 0.25 }}
        className="h-full overflow-y-auto scrollbar-thin"
      >
        <div className="sticky top-0 z-10 bg-[#0A0C10]/90 backdrop-blur-md pb-3 border-b border-white/[0.06]">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-[10px] font-mono text-cyan-400/60 tracking-widest uppercase">
                Intelligence Brief
              </p>
              <h2 className="text-base font-bold text-white mt-0.5">
                {candidate.name}
              </h2>
              <p className="text-xs text-white/40">
                {candidate.title} · {candidate.company}
              </p>
            </div>
            {onClose && (
              <button
                onClick={onClose}
                className="p-1.5 rounded hover:bg-white/[0.05] text-white/30 hover:text-white/60 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        <div className="space-y-6 pt-4 pb-8">
          
          {/* Decision Trace - The core visual flow */}
          <section>
            <SectionHeader icon={Route} label="Decision Trace" />
            <div className="mt-4 flex flex-col items-center">
              
              {/* Retrieved Because */}
              <div className="w-full rounded-lg border border-cyan-500/20 bg-cyan-500/[0.02] p-3 text-center">
                <p className="text-[10px] font-bold text-cyan-400 uppercase tracking-widest mb-2">Retrieved Because</p>
                <div className="flex flex-wrap justify-center gap-1.5">
                  {candidate.whyHere.map((reason, i) => (
                    <span key={i} className="px-2 py-1 bg-cyan-500/10 text-cyan-300 text-[10px] rounded border border-cyan-500/20">{reason}</span>
                  ))}
                </div>
              </div>

              <ArrowDown className="w-4 h-4 text-white/20 my-2" />

              {/* Promoted Because */}
              <div className="w-full rounded-lg border border-emerald-500/20 bg-emerald-500/[0.02] p-3 text-center">
                <p className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest mb-2">Promoted Because</p>
                <ul className="text-xs text-emerald-100/70 space-y-1">
                  {candidate.decisionPath.rankedBecause.map((reason, i) => (
                    <li key={i}>{reason}</li>
                  ))}
                </ul>
              </div>

              <ArrowDown className="w-4 h-4 text-white/20 my-2" />

              {/* Penalized Because */}
              <div className="w-full rounded-lg border border-rose-500/20 bg-rose-500/[0.02] p-3 text-center">
                <p className="text-[10px] font-bold text-rose-400 uppercase tracking-widest mb-2">Penalized Because</p>
                {candidate.decisionPath.penalizedBecause.length > 0 ? (
                  <ul className="text-xs text-rose-100/70 space-y-1">
                    {candidate.decisionPath.penalizedBecause.map((reason, i) => (
                      <li key={i}>{reason}</li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-xs text-white/30 italic">No significant penalties</span>
                )}
              </div>

              <ArrowDown className="w-4 h-4 text-white/20 my-2" />

              {/* Final Verdict */}
              <div className={`w-full rounded-lg border p-3 text-center ${isUnranked ? 'border-rose-500/30 bg-rose-500/10' : 'border-cyan-500/30 bg-cyan-500/10 shadow-[0_0_15px_rgba(34,211,238,0.1)]'}`}>
                <p className={`text-[10px] font-bold uppercase tracking-widest mb-1 ${isUnranked ? 'text-rose-400' : 'text-cyan-400'}`}>Final Verdict</p>
                <p className="text-sm font-bold text-white">
                  {isUnranked ? "Keyword Trap — Reject" : "Interview Recommended"}
                </p>
              </div>

            </div>
          </section>

          {/* ATS vs AI Demo Component */}
          {(!isUnranked && candidate.rank <= 3) && (
            <section>
               <AtsVsAiComponent candidateA={candidate} candidateB={keywordStuffer} />
            </section>
          )}

          {/* Why Not Ranked Component */}
          {isUnranked && (
            <section>
              <SectionHeader icon={ShieldAlert} label="Why Not Ranked" variant="danger" />
              <div className="w-full rounded-lg border border-rose-500/20 bg-rose-500/[0.02] p-4 mt-3">
                 <p className="text-xs text-white/70 mb-3">
                   This candidate has strong keyword overlap with the JD but was rejected by the ranking system due to missing core evidence.
                 </p>
                 <div className="space-y-2 text-xs">
                   <div className="flex gap-2 text-rose-300">
                     <XCircle className="w-4 h-4 shrink-0" />
                     <span>No retrieval ownership</span>
                   </div>
                   <div className="flex gap-2 text-rose-300">
                     <XCircle className="w-4 h-4 shrink-0" />
                     <span>No ranking infrastructure experience</span>
                   </div>
                   <div className="flex gap-2 text-rose-300">
                     <XCircle className="w-4 h-4 shrink-0" />
                     <span>Weak production ML evidence</span>
                   </div>
                 </div>
              </div>
            </section>
          )}

          {/* Evidence Board */}
          <section>
            <SectionHeader icon={FileText} label="Evidence Extract" />
            <div className="space-y-3 mt-2">
              <EvidenceSection
                icon={<Search className="w-3 h-3 text-cyan-400" />}
                title="Retrieval Evidence"
                items={candidate.evidence.retrieval}
                color="cyan"
              />
              <EvidenceSection
                icon={<BarChart3 className="w-3 h-3 text-violet-400" />}
                title="Ranking Evidence"
                items={candidate.evidence.ranking}
                color="violet"
              />
              <EvidenceSection
                icon={<UserCheck className="w-3 h-3 text-emerald-400" />}
                title="Recruiter Intelligence"
                items={candidate.evidence.recruiter}
                color="emerald"
              />
            </div>
          </section>

          {/* Risks */}
          {candidate.risks.length > 0 && (
            <section>
               <SectionHeader icon={ShieldAlert} label="Risk Factors" variant="danger" />
               <ul className="mt-3 space-y-1.5">
                  {candidate.risks.map((risk, i) => (
                    <li key={i} className="text-xs text-rose-300/70 flex items-start gap-1.5">
                      <span className="text-rose-400 mt-0.5 shrink-0">•</span>
                      {risk}
                    </li>
                  ))}
               </ul>
            </section>
          )}

        </div>
      </motion.div>
    </AnimatePresence>
  );
}

function SectionHeader({
  icon: Icon,
  label,
  variant = "default",
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  variant?: "default" | "danger";
}) {
  return (
    <div className="flex items-center gap-2">
      <Icon
        className={`w-3.5 h-3.5 ${
          variant === "danger" ? "text-rose-400" : "text-cyan-400/60"
        }`}
      />
      <h3
        className={`text-[10px] font-bold tracking-widest uppercase ${
          variant === "danger" ? "text-rose-400/70" : "text-white/40"
        }`}
      >
        {label}
      </h3>
      <div className="flex-1 h-px bg-white/[0.06]" />
    </div>
  );
}

function EvidenceSection({
  icon,
  title,
  items,
  color,
}: {
  icon: React.ReactNode;
  title: string;
  items: string[];
  color: "cyan" | "violet" | "emerald";
}) {
  const borderColor = {
    cyan: "border-cyan-400/[0.1]",
    violet: "border-violet-400/[0.1]",
    emerald: "border-emerald-400/[0.1]",
  };
  const bgColor = {
    cyan: "bg-cyan-400/[0.03]",
    violet: "bg-violet-400/[0.03]",
    emerald: "bg-emerald-400/[0.03]",
  };

  return (
    <div
      className={`p-2.5 rounded-md border ${borderColor[color]} ${bgColor[color]}`}
    >
      <div className="flex items-center gap-1.5 mb-1.5">
        {icon}
        <span className="text-[10px] text-white/50 uppercase tracking-wider font-medium">
          {title}
        </span>
      </div>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="text-xs text-white/60 flex items-start gap-1.5">
            <span className="text-white/20 mt-0.5 shrink-0">›</span>
            <span className="italic">&ldquo;{item}&rdquo;</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
