"use client"

import { 
  CheckCircle2, 
  AlertTriangle, 
  ChevronRight, 
  Quote,
  Zap
} from "lucide-react"
import { Card } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { TrajectoryBadge, TrajectoryArchetype } from "./TrajectoryBadge"

interface EvaluationCardProps {
  candidate: {
    full_name: string
    final_score: number
    dimension_scores: {
      semantic_relevance?: { score?: number }
      career_trajectory?: { score?: number }
    }
    explanation?: {
      top_strengths: string[]
      missing_skills: string[]
      adjacent_skills: string[]
      risk_factors: string[]
      overall_assessment: string
      extracted_evidence: { claim: string; evidence: string }[]
    }
    parsed_data: {
      _trajectory?: {
        archetype: TrajectoryArchetype
        score: number
        details: string
      }
      negated_skills?: { canonical_name?: string; name?: string }[]
      _meta?: {
        layout_complexity: number
        extraction_confidence: number
        parser_warnings: string[]
      }
    }
  }
}

export function EvaluationCard({ candidate }: EvaluationCardProps) {
  const { explanation, final_score, dimension_scores, parsed_data } = candidate
  const trajectory = parsed_data._trajectory
  const meta = parsed_data._meta
  const isUncertain = (meta?.extraction_confidence ?? 1.0) < 0.8

  return (
    <Card className="overflow-hidden border-white/5 bg-slate-900/50 backdrop-blur-sm">
      <div className="p-6 space-y-6">
        {/* Header: Score & Name */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h3 className="text-xl font-bold text-white">{candidate.full_name}</h3>
            <div className="flex items-center gap-2">
              <TrajectoryBadge archetype={trajectory?.archetype || "unknown"} explanation={trajectory?.details} />
              {isUncertain && (
                <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/20 gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  Low Confidence
                </Badge>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-black text-blue-400">{final_score}<span className="text-sm font-normal text-slate-500 ml-0.5">%</span></div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Match Score</p>
          </div>
        </div>
        {trajectory?.details && (
          <p className="text-xs text-slate-400 leading-relaxed">{trajectory.details}</p>
        )}

        {/* Alignment Dimensions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-3">
             <div className="flex justify-between text-xs font-medium">
               <span className="text-slate-400">Semantic Alignment</span>
               <span className="text-blue-400">{dimension_scores?.semantic_relevance?.score}%</span>
             </div>
             <Progress value={dimension_scores?.semantic_relevance?.score} className="h-1 bg-white/5" />
             
             <div className="flex justify-between text-xs font-medium pt-1">
               <span className="text-slate-400">Career Trajectory</span>
               <span className="text-purple-400">{dimension_scores?.career_trajectory?.score}%</span>
             </div>
             <Progress value={dimension_scores?.career_trajectory?.score} className="h-1 bg-white/5" />
          </div>
          
          <div className="bg-white/[0.02] rounded-lg p-3 border border-white/5">
             <h4 className="text-[10px] uppercase font-bold text-slate-500 mb-2 flex items-center gap-1">
               <Zap className="w-3 h-3 text-yellow-500" /> Key Strengths
             </h4>
             <ul className="space-y-1">
               {explanation?.top_strengths.slice(0, 2).map((s, i) => (
                 <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
                   <CheckCircle2 className="w-3 h-3 text-emerald-500 mt-0.5 flex-shrink-0" />
                   {s}
                 </li>
               ))}
             </ul>
          </div>
        </div>

        {(explanation?.adjacent_skills?.length || explanation?.missing_skills?.length || explanation?.risk_factors?.length) ? (
         <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
           <div className="bg-white/[0.02] rounded-lg p-3 border border-white/5">
             <h4 className="text-[10px] uppercase font-bold text-slate-500 mb-2">Adjacent Skills</h4>
             <p className="text-xs text-slate-300">{explanation?.adjacent_skills?.slice(0, 2).join(" • ") || "None identified"}</p>
           </div>
           <div className="bg-white/[0.02] rounded-lg p-3 border border-white/5">
             <h4 className="text-[10px] uppercase font-bold text-slate-500 mb-2">Missing Skills</h4>
             <p className="text-xs text-slate-300">{explanation?.missing_skills?.slice(0, 2).join(" • ") || "No major gaps"}</p>
           </div>
           <div className="bg-white/[0.02] rounded-lg p-3 border border-white/5">
             <h4 className="text-[10px] uppercase font-bold text-slate-500 mb-2">Risk Factors</h4>
             <p className="text-xs text-slate-300">{explanation?.risk_factors?.slice(0, 2).join(" • ") || "No major flags"}</p>
           </div>
         </div>
        ) : null}

        {parsed_data?.negated_skills && parsed_data.negated_skills.length > 0 && (
         <div className="p-3 rounded-lg bg-rose-500/5 border border-rose-500/10">
           <p className="text-xs font-semibold text-rose-400">Negation Filter Applied</p>
           <p className="text-[11px] text-rose-300/90 mt-1">
             Excluded from scoring: {parsed_data.negated_skills.slice(0, 3).map(s => s.canonical_name || s.name).filter(Boolean).join(", ")}
           </p>
         </div>
        )}

        {/* Uncertainty Warning */}
        {isUncertain && (
          <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/10 flex gap-3">
            <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-xs font-semibold text-amber-400">Calibrated Uncertainty Warning</p>
              <p className="text-[11px] text-amber-500/80 leading-relaxed">
                {meta?.parser_warnings[0] || "High layout complexity detected. Verify extraction manually."}
              </p>
            </div>
          </div>
        )}

        {/* Evidence Snippets */}
        {explanation?.extracted_evidence && explanation.extracted_evidence.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-[10px] uppercase font-bold text-slate-500 flex items-center gap-1">
              <Quote className="w-3 h-3" /> Extracted Evidence
            </h4>
            <div className="p-3 rounded-lg bg-black/20 border border-white/5 italic text-xs text-slate-400 relative">
              &quot;{explanation.extracted_evidence[0].evidence}&quot;
              <div className="mt-2 text-[10px] not-italic font-bold text-slate-500 flex items-center gap-1">
                <ChevronRight className="w-3 h-3" /> {explanation.extracted_evidence[0].claim}
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Footer / Assessment */}
      <div className="px-6 py-3 bg-white/[0.02] border-t border-white/5">
        <p className="text-[11px] text-slate-400 leading-relaxed">
          <span className="font-bold text-slate-300">AI Assessment:</span> {explanation?.overall_assessment}
        </p>
      </div>
    </Card>
  )
}
