"use client";

import { motion } from "framer-motion";
import type { CareerStep } from "@/store/workspace";

interface CareerTimelineProps {
  career: CareerStep[];
}

export function CareerTimeline({ career }: CareerTimelineProps) {
  return (
    <div className="w-full overflow-x-auto py-4">
      <div className="flex items-center min-w-max gap-0">
        {career.map((step, index) => {
          const isLast = index === career.length - 1;
          return (
            <div key={`${step.company}-${step.year}`} className="flex items-center">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.15, duration: 0.4 }}
                className="flex flex-col items-center gap-2 relative"
              >
                {/* Node */}
                <div
                  className={`relative w-3 h-3 rounded-full ${
                    isLast
                      ? "bg-cyan-400 shadow-[0_0_12px_rgba(34,211,238,0.6)]"
                      : "bg-white/30 border border-white/20"
                  }`}
                >
                  {isLast && (
                    <div className="absolute inset-0 rounded-full bg-cyan-400/40 animate-ping" />
                  )}
                </div>

                {/* Info card */}
                <div
                  className={`flex flex-col items-center px-3 py-2 rounded-lg border min-w-[120px] ${
                    isLast
                      ? "bg-cyan-400/[0.08] border-cyan-400/30 shadow-[0_0_20px_rgba(34,211,238,0.1)]"
                      : "bg-white/[0.03] border-white/[0.08]"
                  }`}
                >
                  <span
                    className={`text-[10px] font-bold tracking-wider uppercase ${
                      isLast ? "text-cyan-400" : "text-white/40"
                    }`}
                  >
                    {step.year}
                  </span>
                  <span
                    className={`text-xs font-medium text-center leading-tight mt-1 ${
                      isLast ? "text-white" : "text-white/70"
                    }`}
                  >
                    {step.role}
                  </span>
                  <span
                    className={`text-[10px] mt-0.5 ${
                      isLast ? "text-cyan-400/70" : "text-white/30"
                    }`}
                  >
                    {step.company}
                  </span>
                </div>
              </motion.div>

              {/* Connector line */}
              {!isLast && (
                <motion.div
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{ delay: index * 0.15 + 0.1, duration: 0.3 }}
                  className="w-8 h-px bg-gradient-to-r from-white/20 to-white/10 origin-left self-start mt-[6px]"
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
