"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import { motion } from "framer-motion"
import {
  Upload,
  Briefcase,
  Zap,
  AlertTriangle,
  ArrowLeft,
  Search,
  Download,
  Users,
  Clock,
  Filter,
  BarChart3,
  Sparkles,
} from "lucide-react"
import { AppShell } from "@/components/layout/AppShell"
import { CandidateRow } from "@/components/CandidateRow"
import { CandidateDetailPanel } from "@/components/CandidateDetailPanel"
import { PipelineProgress } from "@/components/PipelineStage"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import {
  loadSubmission,
  normalizeScore,
  type RankedCandidate,
} from "@/lib/submission"

const PIPELINE_STAGES = [
  { id: "parse", label: "Parse Job Description", description: "Read role requirements from DOCX", progress: 10 },
  { id: "embed", label: "Load Embeddings", description: "100,000 pre-computed candidate vectors", progress: 25 },
  { id: "retrieve", label: "Hybrid Retrieval", description: "Semantic top 5k ∪ BM25 top 5k", progress: 45 },
  { id: "features", label: "Feature Extraction", description: "22 recruiter-aligned signals", progress: 65 },
  { id: "rank", label: "LambdaRank Scoring", description: "LightGBM ranks final candidates", progress: 85 },
  { id: "reason", label: "Generate Reasoning", description: "SHAP-inspired explanations", progress: 100 },
]

export default function DashboardPage() {
  const [jdFile, setJdFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [stageIndex, setStageIndex] = useState(0)
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState<RankedCandidate[]>([])
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<RankedCandidate | null>(null)
  const [search, setSearch] = useState("")
  const [filterTop, setFilterTop] = useState<"all" | "10" | "25">("all")

  const scoreRange = useMemo(() => {
    if (!results.length) return { min: 0, max: 1 }
    const scores = results.map((r) => r.score)
    return { min: Math.min(...scores), max: Math.max(...scores) }
  }, [results])

  const filtered = useMemo(() => {
    let list = results
    if (filterTop === "10") list = list.filter((r) => r.rank <= 10)
    if (filterTop === "25") list = list.filter((r) => r.rank <= 25)
    if (search.trim()) {
      const q = search.toLowerCase()
      list = list.filter(
        (r) =>
          r.candidate_id.toLowerCase().includes(q) ||
          r.reasoning.toLowerCase().includes(q)
      )
    }
    return list
  }, [results, search, filterTop])

  const runPipeline = useCallback(async () => {
    if (!jdFile) return
    setIsProcessing(true)
    setError(null)
    setStageIndex(0)
    setProgress(0)

    try {
      for (let i = 0; i < PIPELINE_STAGES.length; i++) {
        setStageIndex(i)
        setProgress(PIPELINE_STAGES[i].progress)
        await new Promise((r) => setTimeout(r, 700 + i * 120))
      }

      const data = await loadSubmission()
      setResults(data)
      setSelected(data[0] ?? null)
      setProgress(100)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Pipeline failed")
    } finally {
      setIsProcessing(false)
    }
  }, [jdFile])

  const loadDemo = useCallback(async () => {
    setIsProcessing(true)
    setError(null)
    try {
      const data = await loadSubmission()
      setResults(data)
      setSelected(data[0] ?? null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load results")
    } finally {
      setIsProcessing(false)
    }
  }, [])

  useEffect(() => {
    loadDemo()
  }, [loadDemo])

  const exportAll = () => {
    const header = "candidate_id,rank,score,reasoning\n"
    const rows = results
      .map((r) => `${r.candidate_id},${r.rank},${r.score},"${r.reasoning}"`)
      .join("\n")
    const blob = new Blob([header + rows], { type: "text/csv" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "submission.csv"
    a.click()
    URL.revokeObjectURL(url)
  }

  const getDisplayScore = (score: number) =>
    normalizeScore(score, scoreRange.min, scoreRange.max)

  return (
    <AppShell>
      <div className="mx-auto max-w-7xl px-6 py-10">
        {error && (
          <div className="mb-6 flex items-center justify-between rounded-2xl border border-red-500/20 bg-red-500/10 p-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-red-400" />
              <p className="text-sm font-medium text-red-300">{error}</p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setError(null)} className="text-red-400">
              Dismiss
            </Button>
          </div>
        )}

        {results.length === 0 && !isProcessing ? (
          <div className="space-y-12">
            <div className="mx-auto max-w-2xl text-center">
              <Badge className="mb-4 border-blue-500/20 bg-blue-500/10 text-blue-300">
                Hackathon Pipeline
              </Badge>
              <h1 className="text-4xl font-extrabold tracking-tight text-white md:text-5xl">
                Rank candidates like a{" "}
                <span className="bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">
                  senior recruiter
                </span>
              </h1>
              <p className="mt-4 text-slate-400">
                Upload a job description to simulate the full pipeline. Results load from your
                pre-generated <code className="text-blue-300">submission.csv</code>.
              </p>
            </div>

            <div className="mx-auto grid max-w-4xl gap-6 lg:grid-cols-2">
              <Card className="rounded-2xl border-white/5 bg-white/[0.03] p-6">
                <div className="mb-6 flex items-center gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-500/10 ring-1 ring-blue-500/20">
                    <Briefcase className="h-6 w-6 text-blue-400" />
                  </div>
                  <div>
                    <h3 className="font-bold text-white">Job Description</h3>
                    <p className="text-xs text-slate-500">PDF, DOCX, or TXT</p>
                  </div>
                </div>
                <label
                  className={`flex cursor-pointer flex-col items-center rounded-2xl border-2 border-dashed p-10 transition-colors ${
                    jdFile
                      ? "border-emerald-500/30 bg-emerald-500/5"
                      : "border-white/10 hover:border-white/20"
                  }`}
                >
                  <input
                    type="file"
                    accept=".pdf,.txt,.docx"
                    className="hidden"
                    onChange={(e) => setJdFile(e.target.files?.[0] ?? null)}
                  />
                  <Upload className="mb-3 h-10 w-10 text-slate-500" />
                  <p className="text-sm font-medium text-slate-300">
                    {jdFile ? jdFile.name : "Drop job description here"}
                  </p>
                </label>
              </Card>

              <Card className="rounded-2xl border-white/5 bg-white/[0.03] p-6">
                <div className="mb-6 flex items-center gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-500/10 ring-1 ring-violet-500/20">
                    <Users className="h-6 w-6 text-violet-400" />
                  </div>
                  <div>
                    <h3 className="font-bold text-white">Candidate Pool</h3>
                    <p className="text-xs text-slate-500">100,000 profiles pre-indexed</p>
                  </div>
                </div>
                <div className="space-y-3 rounded-2xl border border-white/5 bg-black/20 p-6">
                  {[
                    { label: "Embeddings", value: "Ready" },
                    { label: "LightGBM Model", value: "lgbm_ranker.txt" },
                    { label: "Submission", value: "100 ranked" },
                  ].map((item) => (
                    <div key={item.label} className="flex justify-between text-sm">
                      <span className="text-slate-500">{item.label}</span>
                      <span className="font-medium text-emerald-400">{item.value}</span>
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            <div className="flex flex-col items-center gap-4">
              {isProcessing ? (
                <PipelineProgress
                  stages={PIPELINE_STAGES}
                  currentIndex={stageIndex}
                  overallProgress={progress}
                />
              ) : (
                <>
                  <Button
                    onClick={runPipeline}
                    disabled={!jdFile}
                    className="h-14 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 px-12 text-base font-bold shadow-xl shadow-blue-600/25 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-40"
                  >
                    <Zap className="mr-2 h-5 w-5" />
                    Run Ranking Pipeline
                  </Button>
                  <Button variant="ghost" onClick={loadDemo} className="text-slate-400">
                    Or view existing submission results
                  </Button>
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-8 pb-16">
            <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
              <div>
                <div className="mb-2 flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-blue-400" />
                  <span className="text-xs font-semibold uppercase tracking-widest text-blue-400">
                    Results Ready
                  </span>
                </div>
                <h2 className="text-3xl font-extrabold text-white md:text-4xl">
                  Top {results.length} Candidates
                </h2>
                <p className="mt-1 text-sm text-slate-500">
                  Ranked by recruiter judgment across 5 dimensions
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="border-white/10 text-slate-300"
                  onClick={exportAll}
                >
                  <Download className="mr-1.5 h-3.5 w-3.5" />
                  Export CSV
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="border-white/10 text-slate-300"
                  onClick={() => {
                    setResults([])
                    setSelected(null)
                    setJdFile(null)
                  }}
                >
                  <ArrowLeft className="mr-1.5 h-3.5 w-3.5" />
                  Reset
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {[
                { icon: Users, label: "Scanned", value: "100,000" },
                { icon: Filter, label: "Retrieved", value: "~10,000" },
                { icon: BarChart3, label: "Features", value: "22" },
                { icon: Clock, label: "Inference", value: "<35s" },
              ].map((stat) => (
                <Card
                  key={stat.label}
                  className="rounded-2xl border-white/5 bg-white/[0.02] p-4"
                >
                  <stat.icon className="mb-2 h-4 w-4 text-blue-400" />
                  <div className="text-2xl font-bold text-white">{stat.value}</div>
                  <div className="text-xs text-slate-500">{stat.label}</div>
                </Card>
              ))}
            </div>

            <div className="flex flex-col gap-3 sm:flex-row">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <Input
                  placeholder="Search by ID or reasoning..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="h-11 border-white/10 bg-white/5 pl-10 text-slate-200 placeholder:text-slate-500"
                />
              </div>
              <div className="flex gap-2">
                {(["all", "25", "10"] as const).map((f) => (
                  <Button
                    key={f}
                    size="sm"
                    variant={filterTop === f ? "default" : "outline"}
                    className={
                      filterTop === f
                        ? "bg-blue-600 hover:bg-blue-500"
                        : "border-white/10 text-slate-400"
                    }
                    onClick={() => setFilterTop(f)}
                  >
                    {f === "all" ? "All" : `Top ${f}`}
                  </Button>
                ))}
              </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-5">
              <div className="space-y-2 lg:col-span-3">
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-xs text-slate-500">
                    Showing {filtered.length} of {results.length}
                  </p>
                </div>
                <div className="max-h-[70vh] space-y-2 overflow-y-auto pr-1">
                  {filtered.map((c, i) => (
                    <CandidateRow
                      key={c.candidate_id}
                      candidate={c}
                      displayScore={getDisplayScore(c.score)}
                      selected={selected?.candidate_id === c.candidate_id}
                      index={i}
                      onSelect={() => setSelected(c)}
                    />
                  ))}
                </div>
              </div>

              <div className="lg:col-span-2">
                <div className="lg:sticky lg:top-24">
                  <CandidateDetailPanel
                    candidate={selected}
                    displayScore={selected ? getDisplayScore(selected.score) : 0}
                    rawScore={selected?.score ?? 0}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {isProcessing && results.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          >
            <Card className="w-full max-w-lg rounded-2xl border-white/10 bg-[#0a0f1e] p-8">
              <PipelineProgress
                stages={PIPELINE_STAGES}
                currentIndex={stageIndex}
                overallProgress={progress}
              />
            </Card>
          </motion.div>
        )}
      </div>
    </AppShell>
  )
}
