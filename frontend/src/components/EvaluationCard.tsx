"use client"

import { useState } from "react"
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
      extracted_evidence: {
        claim: string
        evidence: string
        mapped_requirement?: string
        confidence?: number
        source_section?: string
      }[]
    }
    parsed_data: {
      _trajectory?: {
        archetype: TrajectoryArchetype
        score: number
        details: string
      }
      _meta?: {
        layout_complexity: number
        extraction_confidence: number
        parser_warnings: string[]
        raw_extracted_text?: string
      }
    }
  }
}

export function EvaluationCard({ candidate }: EvaluationCardProps) {
  const { explanation, final_score, dimension_scores, parsed_data } = candidate
  const trajectory = parsed_data._trajectory
  const meta = parsed_data._meta
  const isUncertain = (meta?.extraction_confidence ?? 1.0) < 0.8
  const [showRawText, setShowRawText] = useState(false)
  const confidencePercent = Math.round((meta?.extraction_confidence ?? 1.0) * 100)

  return (
    <Card className="overflow-hidden border-white/5 bg-slate-900/50 backdrop-blur-sm">
      <div className="p-6 space-y-6">
        {/* Header: Score & Name */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h3 className="text-xl font-bold text-white">{candidate.full_name}</h3>
            <div className="flex items-center gap-2">
              <TrajectoryBadge archetype={trajectory?.archetype || "unknown"} />
              {isUncertain && (
                <Badge variant="outline" className="bg-amber-500/10 text-amber-400 border-amber-500/20 gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  {confidencePercent}% Layout Confidence
                </Badge>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-black text-blue-400">{final_score}<span className="text-sm font-normal text-slate-500 ml-0.5">%</span></div>
            <p className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Match Score</p>
          </div>
        </div>

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

        {/* Uncertainty Warning */}
        {isUncertain && (
          <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/10 flex gap-3">
            <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-xs font-semibold text-amber-400">Calibrated Uncertainty Warning</p>
              <p className="text-[11px] text-amber-500/80 leading-relaxed">
                Layout-parsing confidence: {confidencePercent}% — this candidate may be underscored due to a decorative PDF. Click to verify raw extracted text.
              </p>
              {meta?.parser_warnings?.[0] && (
                <p className="text-[11px] text-amber-500/70 leading-relaxed">{meta.parser_warnings[0]}</p>
              )}
              {meta?.raw_extracted_text && (
                <button
                  type="button"
                  onClick={() => setShowRawText((current) => !current)}
                  className="text-[11px] font-semibold text-amber-300 hover:text-amber-200 transition-colors"
                >
                  {showRawText ? "Hide raw extracted text" : "Verify raw extracted text"}
                </button>
              )}
            </div>
          </div>
        )}
        {isUncertain && showRawText && meta?.raw_extracted_text && (
          <div className="p-3 rounded-lg bg-black/30 border border-amber-500/20">
            <p className="text-[10px] uppercase font-bold text-amber-300 mb-2">Raw Extracted Text</p>
            <pre className="text-[11px] text-slate-300 whitespace-pre-wrap max-h-56 overflow-y-auto font-sans leading-relaxed">
              {meta.raw_extracted_text}
            </pre>
          </div>
        )}

        {/* Evidence Snippets */}
        {explanation?.extracted_evidence && explanation.extracted_evidence.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-[10px] uppercase font-bold text-slate-500 flex items-center gap-1">
              <Quote className="w-3 h-3" /> Evidence-Citation Cards
            </h4>
            {explanation.extracted_evidence.slice(0, 3).map((item, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-black/20 border border-white/5 italic text-xs text-slate-400 relative">
                &quot;{item.evidence}&quot;
                <div className="mt-2 text-[10px] not-italic font-bold text-slate-500 flex items-center gap-1">
                  <ChevronRight className="w-3 h-3" /> {item.claim}
                </div>
                <div className="mt-1 text-[10px] not-italic text-slate-500">
                  {item.mapped_requirement ? `Maps to ${item.mapped_requirement}` : "Mapped requirement unavailable"}
                  {typeof item.confidence === "number" ? ` (${Math.round(item.confidence * 100)}% confidence` : ""}
                  {item.source_section ? `, ${item.source_section} section` : ""}
                  {typeof item.confidence === "number" ? ")" : ""}
                </div>
              </div>
            ))}
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
