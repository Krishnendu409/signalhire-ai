"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronRight, Filter } from "lucide-react";

interface FunnelStage {
  label: string;
  count: string;
  width: string;
  color: string;
}

const FUNNEL_STAGES: FunnelStage[] = [
  {
    label: "Total Candidates",
    count: "100,000",
    width: "100%",
    color: "bg-white/10",
  },
  {
    label: "Semantic Matches",
    count: "5,000",
    width: "72%",
    color: "bg-cyan-400/20",
  },
  {
    label: "Hybrid Matches",
    count: "1,000",
    width: "48%",
    color: "bg-cyan-400/30",
  },
  {
    label: "Ranked Candidates",
    count: "100",
    width: "28%",
    color: "bg-cyan-400/50",
  },
  {
    label: "Top Interviews",
    count: "10",
    width: "14%",
    color: "bg-cyan-400",
  },
];

export function SelectionFunnel() {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <div className="rounded-lg border border-white/[0.08] bg-white/[0.02] overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full flex items-center justify-between px-3 py-2.5 hover:bg-white/[0.03] transition-colors"
      >
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-xs font-semibold text-white/70 tracking-wide uppercase">
            Selection Funnel
          </span>
        </div>
        {isCollapsed ? (
          <ChevronRight className="w-3.5 h-3.5 text-white/40" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-white/40" />
        )}
      </button>

      {/* Funnel body */}
      <AnimatePresence>
        {!isCollapsed && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-3 pb-3 space-y-1.5">
              {FUNNEL_STAGES.map((stage, index) => (
                <motion.div
                  key={stage.label}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.08, duration: 0.3 }}
                  className="flex flex-col gap-0.5"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-white/50">{stage.label}</span>
                    <span className="text-[10px] font-mono text-white/70 font-medium">
                      {stage.count}
                    </span>
                  </div>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: stage.width }}
                    transition={{ delay: index * 0.12 + 0.2, duration: 0.5, ease: "easeOut" }}
                    className={`h-1.5 rounded-full ${stage.color}`}
                  />
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
