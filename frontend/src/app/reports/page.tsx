"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Fingerprint, Download, FileText, CheckCircle2, ShieldAlert,
  Zap, Loader2, AlertCircle
} from "lucide-react";
import { get100kResults } from "@/lib/api-client";

type PipelineResult = {
  rank: number;
  candidate_id: string;
  full_name: string;
  title: string;
  final_score: number;
  reasoning: string;
  matched_skills: string[];
  missing_skills: string[];
  years_of_experience: number;
  decisionPath: {
    rankedBecause: string[];
    penalizedBecause: string[];
  };
};

type Meta = {
  totalEvaluated: number;
  retrieved: number;
  ranked: number;
  shortlisted: number;
  model: string;
  rejections: Array<{ reason: string; count: number }>;
};

export default function ReportsPage() {
  const [results, setResults] = useState<PipelineResult[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    get100kResults()
      .then((res) => {
        if (res.status === "completed" && res.results && res.analytics) {
          const top10 = (res.results as PipelineResult[])
            .filter((r) => r.rank <= 10)
            .sort((a, b) => a.rank - b.rank);
          setResults(top10);
          setMeta({
            totalEvaluated: res.analytics.totalEvaluated,
            retrieved: res.analytics.retrieved,
            ranked: res.analytics.ranked,
            shortlisted: res.analytics.shortlisted,
            model: res.analytics.model,
            rejections: res.analytics.rejections,
          });
        } else if (res.status === "running") {
          setError("Pipeline is still running. Please wait for it to complete.");
        } else {
          setError("No pipeline results yet. Run the 100k pipeline first.");
        }
      })
      .catch(() => {
        setError("Cannot reach backend. Make sure the API is running on port 8000.");
      })
      .finally(() => setLoading(false));
  }, []);

  const handleDownload = () => {
    if (!meta || results.length === 0) return;

    const content = `# SignalHire — Investigation Report: REQ-2026-001\n\n## Executive Summary\nModel Used: ${meta.model}\nTotal Candidates Evaluated: ${meta.totalEvaluated.toLocaleString()}\nTotal Candidates Retrieved: ${meta.retrieved.toLocaleString()}\nFinal Shortlist Size: ${meta.shortlisted}\n\n## Top 10 Candidates\n${results.map((c) =>
      `${c.rank}. ${c.full_name} — ${c.title} (Score: ${c.final_score}%)\n   Matched: ${c.matched_skills?.join(", ") || "—"}\n   Missing: ${c.missing_skills?.join(", ") || "None"}\n   Reasoning: ${c.reasoning || "No reasoning provided"}\n   Risk Flags: ${c.decisionPath?.penalizedBecause?.join(", ") || "None identified"}`
    ).join("\n\n")}\n\n## Rejection Patterns\n${meta.rejections.map((r) => `- ${r.reason}: ${r.count} candidates`).join("\n")}\n\n## Methodology\n- Hybrid BM25 + Semantic Retrieval (5,000 candidate union)\n- 8-feature JD-relative extraction\n- LightGBM LambdaRank scoring\n- Score normalisation and reasoning generation\n`;

    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "SignalHire_Investigation_Report.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-[#e5e2e1] font-sans flex flex-col">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-4 md:px-10 h-14 bg-[#141313] border-b border-[#262626]">
        <Link href="/" className="flex items-center gap-3">
          <Fingerprint className="text-white w-5 h-5" />
          <span className="text-base font-semibold text-white tracking-tight">SignalHire</span>
        </Link>
        <div className="hidden md:flex items-center gap-6">
          <Link className="text-[#c4c7c8] text-xs hover:bg-[#353434] transition-colors px-3 py-1 rounded" href="/new">New Investigation</Link>
          <Link className="text-[#c4c7c8] text-xs hover:bg-[#353434] transition-colors px-3 py-1 rounded" href="/workspace">Workspace</Link>
          <Link className="text-[#c4c7c8] text-xs hover:bg-[#353434] transition-colors px-3 py-1 rounded" href="/analytics">Analytics</Link>
          <Link className="text-white font-bold text-xs bg-[#353434] px-3 py-1 rounded" href="/reports">Reports</Link>
        </div>
      </nav>

      <main className="pt-20 px-4 md:px-10 max-w-5xl mx-auto w-full flex-1 pb-24">
        <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-4 h-4 text-[#A3A3A3]" />
              <span className="text-[10px] font-mono uppercase tracking-widest text-[#A3A3A3]">Investigation Report</span>
            </div>
            <h1 className="text-3xl font-semibold text-white mb-1">REQ-2026-001</h1>
            <p className="text-sm text-[#A3A3A3]">Senior Search Engineer — 100k Pipeline Shortlist</p>
          </div>
          <button
            onClick={handleDownload}
            disabled={!meta || results.length === 0}
            className="flex items-center gap-2 bg-white text-black px-5 py-2.5 rounded font-bold text-xs uppercase tracking-widest hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Download className="w-4 h-4" /> Export Report
          </button>
        </header>

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="w-6 h-6 text-white animate-spin" />
            <span className="ml-3 text-sm text-[#A3A3A3]">Loading pipeline results…</span>
          </div>
        )}

        {/* Error / Empty state */}
        {!loading && error && (
          <div className="border border-dashed border-[#262626] rounded-xl p-16 flex flex-col items-center justify-center text-center">
            <AlertCircle className="w-10 h-10 text-[#EF4444] mb-4" />
            <h2 className="text-lg font-semibold text-white mb-2">No Report Available</h2>
            <p className="text-sm text-[#A3A3A3] max-w-md mb-6">{error}</p>
            <Link
              href="/new"
              className="flex items-center gap-2 bg-white text-black px-5 py-2.5 rounded font-bold text-xs uppercase tracking-widest hover:bg-gray-100 transition-colors"
            >
              <Zap className="w-4 h-4" /> Go to 100k Pipeline
            </Link>
          </div>
        )}

        {/* Results */}
        {!loading && !error && meta && (
          <div className="space-y-6">
            {/* Summary stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: "Candidates Evaluated", value: meta.totalEvaluated.toLocaleString(), color: "text-white" },
                { label: "Hybrid Retrieved", value: meta.retrieved.toLocaleString(), color: "text-[#3b82f6]" },
                { label: "Ranked", value: meta.ranked.toLocaleString(), color: "text-[#8b5cf6]" },
                { label: "Final Shortlist", value: meta.shortlisted.toString(), color: "text-[#22C55E]" },
              ].map((s) => (
                <div key={s.label} className="border border-[#262626] bg-[#111111] rounded-lg p-5">
                  <p className="text-[10px] text-[#A3A3A3] font-mono mb-2 uppercase">{s.label}</p>
                  <p className={`text-2xl font-semibold ${s.color}`}>{s.value}</p>
                </div>
              ))}
            </div>

            {/* Model badge */}
            <div className="border border-[#262626] bg-[#111111] rounded-lg p-4 flex items-center gap-3">
              <Zap className="w-4 h-4 text-[#F59E0B]" />
              <span className="text-xs font-mono text-[#F59E0B] uppercase tracking-widest">{meta.model}</span>
            </div>

            {/* Top 10 candidates */}
            <div className="border border-[#262626] bg-[#111111] rounded-lg p-5">
              <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-5 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#22C55E]" /> Top-10 Shortlisted Candidates
              </h3>
              <div className="space-y-4">
                {results.map((c) => (
                  <div key={c.candidate_id} className="border border-[#262626] rounded-lg p-4">
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-lg font-bold text-white w-8">#{c.rank}</span>
                        <div>
                          <p className="text-sm font-semibold text-white">{c.full_name}</p>
                          <p className="text-xs text-[#A3A3A3]">{c.title}{c.years_of_experience ? ` · ${c.years_of_experience}yrs` : ""}</p>
                        </div>
                      </div>
                      <p className="text-lg font-bold text-[#22C55E] shrink-0">{c.final_score}%</p>
                    </div>

                    {c.reasoning && (
                      <p className="text-xs text-[#c4c7c8] mb-3 leading-relaxed">{c.reasoning}</p>
                    )}

                    <div className="flex flex-wrap gap-1.5">
                      {(c.matched_skills || []).map((sk) => (
                        <span key={sk} className="text-[10px] bg-[#22C55E]/10 text-[#22C55E] border border-[#22C55E]/20 px-2 py-0.5 rounded capitalize">{sk}</span>
                      ))}
                      {(c.missing_skills || []).map((sk) => (
                        <span key={sk} className="text-[10px] bg-[#EF4444]/10 text-[#EF4444] border border-[#EF4444]/20 px-2 py-0.5 rounded capitalize">✗ {sk}</span>
                      ))}
                      {(c.decisionPath?.penalizedBecause || []).map((p) => (
                        <span key={p} className="text-[10px] bg-[#F59E0B]/10 text-[#F59E0B] border border-[#F59E0B]/20 px-2 py-0.5 rounded">⚠ {p}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Rejection breakdown */}
            <div className="border border-[#262626] bg-[#111111] rounded-lg p-5">
              <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-[#EF4444]" /> Rejection Analysis
              </h3>
              <div className="space-y-3">
                {meta.rejections.map((r) => (
                  <div key={r.reason} className="flex items-center justify-between p-3 border border-[#262626] rounded border-l-2 border-l-[#EF4444]">
                    <span className="text-xs text-[#c4c7c8]">{r.reason}</span>
                    <span className="text-xs font-mono text-[#EF4444] bg-[#EF4444]/10 px-2 py-0.5 rounded">{r.count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
