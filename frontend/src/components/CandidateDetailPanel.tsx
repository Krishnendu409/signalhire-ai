"use client"

import { motion } from "framer-motion"
import {
  Brain,
  ShieldCheck,
  Target,
  TrendingUp,
  Zap,
  Download,
  Copy,
  Check,
} from "lucide-react"
import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { extractSignals, type RankedCandidate } from "@/lib/submission"

const dimensions = [
  { key: "technical", label: "Technical Fit", icon: Brain, color: "bg-blue-500" },
  { key: "startup", label: "Startup Ready", icon: Zap, color: "bg-purple-500" },
  { key: "authentic", label: "Authenticity", icon: ShieldCheck, color: "bg-emerald-500" },
  { key: "hireable", label: "Hireability", icon: Target, color: "bg-amber-500" },
  { key: "behavior", label: "Reliability", icon: TrendingUp, color: "bg-rose-500" },
]

function estimateDimensionScores(reasoning: string, rank: number) {
  const base = Math.max(20, 100 - rank * 0.8)
  const hasRetrieval = reasoning.includes("retrieval") ? 18 : 0
  const hasProd = reasoning.includes("production") || reasoning.includes("deploy") ? 15 : 0
  const hasHire = reasoning.includes("hireability") || reasoning.includes("engagement") ? 12 : 0
  const hasDeep = reasoning.includes("Extensive") ? 10 : 0

  return {
    technical: Math.min(98, base + hasRetrieval + hasProd),
    startup: Math.min(95, base * 0.85 + hasDeep),
    authentic: Math.min(96, base * 0.9),
    hireable: Math.min(97, base * 0.8 + hasHire),
    behavior: Math.min(94, base * 0.75 + (rank <= 20 ? 10 : 0)),
  }
}

type Props = {
  candidate: RankedCandidate | null
  displayScore: number
  rawScore: number
}

export function CandidateDetailPanel({ candidate, displayScore, rawScore }: Props) {
  const [copied, setCopied] = useState(false)

  if (!candidate) {
    return (
      <Card className="rounded-2xl border-white/5 bg-white/[0.02] p-8 text-center">
        <Brain className="mx-auto mb-3 h-10 w-10 text-slate-600" />
        <p className="text-sm font-medium text-slate-400">Select a candidate</p>
        <p className="mt-1 text-xs text-slate-500">
          Click any row to see AI reasoning and dimension scores
        </p>
      </Card>
    )
  }

  const scores = estimateDimensionScores(candidate.reasoning, candidate.rank)
  const signals = extractSignals(candidate.reasoning)

  const copyId = async () => {
    await navigator.clipboard.writeText(candidate.candidate_id)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <motion.div
      key={candidate.candidate_id}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      <Card className="overflow-hidden rounded-2xl border-white/5 bg-white/[0.03]">
        <div className="border-b border-white/5 bg-gradient-to-r from-blue-600/10 to-indigo-600/5 p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-widest text-blue-400">
                Rank #{candidate.rank}
              </p>
              <h3 className="mt-1 text-xl font-bold text-white">{candidate.candidate_id}</h3>
            </div>
            <div className="text-right">
              <div className="text-3xl font-extrabold text-blue-400">{displayScore.toFixed(0)}</div>
              <p className="text-[10px] text-slate-500">normalized match</p>
              <p className="text-[10px] text-slate-600">raw: {rawScore.toFixed(2)}</p>
            </div>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {signals.map((s) => (
              <Badge key={s} className="border-white/10 bg-white/5 text-slate-300">
                {s}
              </Badge>
            ))}
          </div>
        </div>

        <div className="space-y-5 p-6">
          <div>
            <h4 className="mb-2 text-[10px] font-bold uppercase tracking-widest text-slate-500">
              AI Reasoning
            </h4>
            <p className="text-sm leading-relaxed text-slate-300">{candidate.reasoning}</p>
          </div>

          <div>
            <h4 className="mb-3 text-[10px] font-bold uppercase tracking-widest text-slate-500">
              Five Dimensions
            </h4>
            <div className="space-y-3">
              {dimensions.map((dim) => {
                const value = scores[dim.key as keyof typeof scores]
                return (
                  <div key={dim.key}>
                    <div className="mb-1 flex items-center justify-between text-xs">
                      <span className="flex items-center gap-1.5 text-slate-400">
                        <dim.icon className="h-3.5 w-3.5" />
                        {dim.label}
                      </span>
                      <span className="font-semibold text-slate-200">{Math.round(value)}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-white/5">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${value}%` }}
                        transition={{ duration: 0.5 }}
                        className={`h-full rounded-full ${dim.color}`}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1 border-white/10 bg-transparent text-slate-300 hover:bg-white/5"
              onClick={copyId}
            >
              {copied ? <Check className="mr-1.5 h-3.5 w-3.5" /> : <Copy className="mr-1.5 h-3.5 w-3.5" />}
              {copied ? "Copied" : "Copy ID"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="flex-1 border-white/10 bg-transparent text-slate-300 hover:bg-white/5"
              onClick={() => {
                const blob = new Blob(
                  [`${candidate.candidate_id},${candidate.rank},${candidate.score},"${candidate.reasoning}"`],
                  { type: "text/csv" }
                )
                const url = URL.createObjectURL(blob)
                const a = document.createElement("a")
                a.href = url
                a.download = `${candidate.candidate_id}.csv`
                a.click()
                URL.revokeObjectURL(url)
              }}
            >
              <Download className="mr-1.5 h-3.5 w-3.5" />
              Export
            </Button>
          </div>
        </div>
      </Card>
    </motion.div>
  )
}
