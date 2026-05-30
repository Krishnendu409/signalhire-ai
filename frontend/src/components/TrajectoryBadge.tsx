"use client"

import { motion } from "framer-motion"
import { TrendingUp, Anchor, AlertCircle, HelpCircle } from "lucide-react"

export type TrajectoryArchetype = "fast_climber" | "stable_performer" | "chaotic_hopper" | "mixed" | "unknown"

interface TrajectoryBadgeProps {
  archetype: TrajectoryArchetype
  details?: string
  metrics?: {
    promotion_rate?: number
    avg_tenure_years?: number
    industry_diversity?: number
  }
  showIcon?: boolean
  className?: string
}

const ARCHETYPE_CONFIG = {
  fast_climber: {
    label: "Fast Climber",
    color: "text-blue-400 bg-blue-500/10 border-blue-500/20",
    icon: TrendingUp,
    description: "Rapid promotions and increasing scope."
  },
  stable_performer: {
    label: "Stable Performer",
    color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    icon: Anchor,
    description: "Deep expertise and long tenures."
  },
  chaotic_hopper: {
    label: "Chaotic Hopper",
    color: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    icon: AlertCircle,
    description: "Frequent short stints without clear progression."
  },
  mixed: {
    label: "Mixed Trajectory",
    color: "text-slate-400 bg-slate-500/10 border-slate-500/20",
    icon: HelpCircle,
    description: "Multi-archetype characteristics."
  },
  unknown: {
    label: "Unknown",
    color: "text-slate-500 bg-slate-500/5 border-slate-500/10",
    icon: HelpCircle,
    description: "Insufficient data to classify."
  }
}

export function TrajectoryBadge({ archetype, details, metrics, showIcon = true, className = "" }: TrajectoryBadgeProps) {
  const config = ARCHETYPE_CONFIG[archetype] || ARCHETYPE_CONFIG.unknown
  const Icon = config.icon
  const fallbackDetails = config.description
  const metricSummary = [
    typeof metrics?.promotion_rate === "number" ? `${metrics.promotion_rate.toFixed(2)}/yr promotions` : "",
    typeof metrics?.avg_tenure_years === "number" ? `${metrics.avg_tenure_years.toFixed(1)}y avg tenure` : "",
    typeof metrics?.industry_diversity === "number" ? `${metrics.industry_diversity} industry tracks` : "",
  ].filter(Boolean).join(" • ")

  return (
    <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className={`space-y-1 ${className}`}>
      <div
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-semibold ${config.color}`}
        title={details || fallbackDetails}
      >
        {showIcon && <Icon className="w-3 h-3" />}
        {config.label}
      </div>
      <p className="text-[11px] text-slate-400 max-w-xl leading-relaxed">{details || fallbackDetails}</p>
      {metricSummary && <p className="text-[10px] text-slate-500">{metricSummary}</p>}
    </motion.div>
  )
}
