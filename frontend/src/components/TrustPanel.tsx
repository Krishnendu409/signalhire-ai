"use client";

import { motion } from "framer-motion";
import { Filter, Users, Database, ShieldCheck, CheckCircle2 } from "lucide-react";

export function TrustPanel() {
  const steps = [
    { label: "Total Pool", count: "100,000", icon: Users, color: "text-slate-400" },
    { label: "Lexical & Semantic Match", count: "5,000", icon: Database, color: "text-cyan-400" },
    { label: "Technical Rank", count: "1,000", icon: Filter, color: "text-emerald-400" },
    { label: "Composite Shortlist", count: "100", icon: ShieldCheck, color: "text-violet-400" },
    { label: "Interview Ready", count: "20", icon: CheckCircle2, color: "text-amber-400" }
  ];

  return (
    <div className="w-full rounded-lg border border-white/[0.06] bg-white/[0.02] p-3 mb-4">
      <h3 className="text-[10px] font-bold tracking-widest text-white/40 uppercase mb-3 flex items-center gap-2">
        <ShieldCheck className="w-3 h-3 text-emerald-400" />
        Intelligence Funnel
      </h3>
      <div className="space-y-2">
        {steps.map((step, i) => (
          <div key={i} className="flex items-center group relative">
            {/* Connecting line */}
            {i !== steps.length - 1 && (
              <div className="absolute left-[11px] top-6 w-px h-4 bg-white/[0.08]" />
            )}
            
            <div className={`w-6 h-6 rounded-full border border-white/[0.08] bg-black/40 flex items-center justify-center shrink-0 z-10 ${step.color}`}>
              <step.icon className="w-3 h-3" />
            </div>
            
            <div className="ml-3 flex-1 flex items-center justify-between">
              <span className="text-[10px] text-white/60 font-medium">{step.label}</span>
              <span className={`text-[10px] font-mono font-bold ${step.color}`}>{step.count}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
