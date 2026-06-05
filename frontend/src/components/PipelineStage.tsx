"use client"

import { motion } from "framer-motion"
import { CheckCircle2, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

export type PipelineStage = {
  id: string
  label: string
  description: string
  progress: number
}

type Props = {
  stages: PipelineStage[]
  currentIndex: number
  overallProgress: number
}

export function PipelineProgress({ stages, currentIndex, overallProgress }: Props) {
  return (
    <div className="w-full max-w-2xl space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-widest text-blue-400">
            {stages[currentIndex]?.label ?? "Processing"}
          </p>
          <p className="mt-1 text-sm text-slate-400">
            {stages[currentIndex]?.description ?? "Running ranking pipeline..."}
          </p>
        </div>
        <span className="text-3xl font-extrabold text-white">{Math.round(overallProgress)}%</span>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-white/5">
        <motion.div
          className="h-full rounded-full bg-gradient-to-r from-blue-500 via-indigo-500 to-violet-500"
          animate={{ width: `${overallProgress}%` }}
          transition={{ ease: "easeOut" }}
        />
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        {stages.map((stage, i) => {
          const done = i < currentIndex
          const active = i === currentIndex
          return (
            <div
              key={stage.id}
              className={cn(
                "flex items-start gap-3 rounded-xl border p-3 transition-colors",
                done && "border-emerald-500/20 bg-emerald-500/5",
                active && "border-blue-500/30 bg-blue-500/10",
                !done && !active && "border-white/5 bg-white/[0.02]"
              )}
            >
              <div className="mt-0.5">
                {done ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                ) : active ? (
                  <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
                ) : (
                  <div className="h-4 w-4 rounded-full border border-white/20" />
                )}
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-200">{stage.label}</p>
                <p className="text-[10px] text-slate-500">{stage.description}</p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
