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

const UNCERTAINTY_THRESHOLD = 0.8

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
      compliance_note?: string
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
        promotion_rate?: number
        avg_tenure_years?: number
        industry_diversity?: number
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
  const isUncertain = (meta?.extraction_confidence ?? 1.0) < UNCERTAINTY_THRESHOLD
  const [showRawText, setShowRawText] = useState(false)
  const confidencePercent = Math.round((meta?.extraction_confidence ?? 1.0) * 100)
  const formatEvidenceMeta = (item: {
    mapped_requirement?: string
    confidence?: number
    source_section?: string
  }) => {
    const parts: string[] = []
    parts.push(item.mapped_requirement ? `Maps to ${item.mapped_requirement}` : "General evidence")
    if (typeof item.confidence === "number") {
      parts.push(`${Math.round(item.confidence * 100)}% confidence`)
    }
    if (item.source_section) {
      parts.push(`${item.source_section} section`)
    }
    return parts.join(" • ")
  }

  return (
    <Card className="overflow-hidden border-white/5 bg-slate-900/50 backdrop-blur-sm">
      <div className="p-6 space-y-6">
        {/* Header: Score & Name */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h3 className="text-xl font-bold text-white">{candidate.full_name}</h3>
            <div className="flex items-start gap-2">
              <TrajectoryBadge
                archetype={trajectory?.archetype || "unknown"}
                details={trajectory?.details}
                metrics={{
                  promotion_rate: trajectory?.promotion_rate,
                  avg_tenure_years: trajectory?.avg_tenure_years,
                  industry_diversity: trajectory?.industry_diversity,
                }}
              />
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
                 <li key={`${s}-${i}`} className="text-xs text-slate-300 flex items-start gap-2">
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
                  aria-expanded={showRawText}
                  aria-controls="raw-extracted-text-panel"
                  className="text-[11px] font-semibold text-amber-300 hover:text-amber-200 transition-colors"
                >
                  {showRawText ? "Hide raw extracted text" : "Verify raw extracted text"}
                </button>
              )}
            </div>
          </div>
        )}
        {isUncertain && showRawText && meta?.raw_extracted_text && (
          <div id="raw-extracted-text-panel" className="p-3 rounded-lg bg-black/30 border border-amber-500/20">
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
            {explanation.extracted_evidence.map((item, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-black/20 border border-white/5 italic text-xs text-slate-400 relative">
                &quot;{item.evidence}&quot;
                <div className="mt-2 text-[10px] not-italic font-bold text-slate-500 flex items-center gap-1">
                  <ChevronRight className="w-3 h-3" /> {item.claim}
                </div>
                <div className="mt-1 text-[10px] not-italic text-slate-500">
                  {formatEvidenceMeta(item)}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Explainability breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="bg-white/[0.02] rounded-lg p-3 border border-white/5">
            <h4 className="text-[10px] uppercase font-bold text-slate-500 mb-2">Adjacent Skills</h4>
            <ul className="space-y-1">
              {(explanation?.adjacent_skills?.length ? explanation.adjacent_skills : ["No adjacent coverage detected."])
                .slice(0, 3)
                .map((item, idx) => (
                  <li key={`${item}-${idx}`} className="text-xs text-slate-300">{item}</li>
                ))}
            </ul>
          </div>
          <div className="bg-white/[0.02] rounded-lg p-3 border border-white/5">
            <h4 className="text-[10px] uppercase font-bold text-slate-500 mb-2">Missing Skills</h4>
            <ul className="space-y-1">
              {(explanation?.missing_skills?.length ? explanation.missing_skills : ["No critical gaps identified."])
                .slice(0, 3)
                .map((item, idx) => (
                  <li key={`${item}-${idx}`} className="text-xs text-slate-300">{item}</li>
                ))}
            </ul>
          </div>
          <div className="bg-white/[0.02] rounded-lg p-3 border border-white/5">
            <h4 className="text-[10px] uppercase font-bold text-slate-500 mb-2">Risk Factors</h4>
            <ul className="space-y-1">
              {(explanation?.risk_factors?.length ? explanation.risk_factors : ["No immediate hiring risk flagged."])
                .slice(0, 3)
                .map((item, idx) => (
                  <li key={`${item}-${idx}`} className="text-xs text-slate-300">{item}</li>
                ))}
            </ul>
          </div>
        </div>
      </div>
      
      {/* Footer / Assessment */}
      <div className="px-6 py-3 bg-white/[0.02] border-t border-white/5">
        <p className="text-[11px] text-slate-400 leading-relaxed">
          <span className="font-bold text-slate-300">AI Assessment:</span> {explanation?.overall_assessment}
        </p>
        {explanation?.compliance_note && (
          <p className="text-[10px] text-slate-500 mt-2">{explanation.compliance_note}</p>
        )}
      </div>
    </Card>
  )
}
