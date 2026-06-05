"use client"

import { motion } from "framer-motion"
import { ChevronRight, Trophy, Medal, Award } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { extractSignals, type RankedCandidate } from "@/lib/submission"
import { cn } from "@/lib/utils"

type Props = {
  candidate: RankedCandidate
  displayScore: number
  selected: boolean
  index: number
  onSelect: () => void
}

function RankIcon({ rank }: { rank: number }) {
  if (rank === 1) return <Trophy className="h-4 w-4 text-amber-400" />
  if (rank === 2) return <Medal className="h-4 w-4 text-slate-300" />
  if (rank === 3) return <Award className="h-4 w-4 text-amber-600" />
  return <span className="text-sm font-bold text-slate-400">#{rank}</span>
}

export function CandidateRow({ candidate, displayScore, selected, index, onSelect }: Props) {
  const signals = extractSignals(candidate.reasoning)

  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index * 0.02, 0.4) }}
      onClick={onSelect}
      className={cn(
        "group w-full rounded-2xl border p-4 text-left transition-all",
        selected
          ? "border-blue-500/40 bg-blue-500/10 shadow-lg shadow-blue-500/10"
          : "border-white/5 bg-white/[0.02] hover:border-white/10 hover:bg-white/[0.04]"
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-3">
          <div
            className={cn(
              "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border",
              candidate.rank <= 3
                ? "border-amber-500/30 bg-amber-500/10"
                : "border-white/10 bg-white/5"
            )}
          >
            <RankIcon rank={candidate.rank} />
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="truncate font-semibold text-white">{candidate.candidate_id}</h3>
              {candidate.rank <= 10 && (
                <Badge className="border-amber-500/20 bg-amber-500/10 text-[10px] text-amber-300">
                  Top 10
                </Badge>
              )}
            </div>
            <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-slate-400">
              {candidate.reasoning}
            </p>
            {signals.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {signals.map((s) => (
                  <span
                    key={s}
                    className="rounded-md bg-white/5 px-2 py-0.5 text-[10px] font-medium text-slate-400"
                  >
                    {s}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <div className="text-right">
            <div className="text-xl font-bold text-blue-400">{displayScore.toFixed(0)}</div>
            <div className="text-[10px] uppercase tracking-wider text-slate-500">Match</div>
          </div>
          <ChevronRight
            className={cn(
              "h-4 w-4 text-slate-600 transition-transform group-hover:translate-x-0.5",
              selected && "text-blue-400"
            )}
          />
        </div>
      </div>
    </motion.button>
  )
}
