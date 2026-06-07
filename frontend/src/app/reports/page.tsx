"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Fingerprint, Download, FileText, CheckCircle2, ShieldAlert } from "lucide-react";
import { getCombinedShortlist, getRankingMetadata } from "@/lib/api";
import { Candidate } from "@/store/workspace";

type Metadata = Awaited<ReturnType<typeof getRankingMetadata>>;

export default function ReportsPage() {
  const [data, setData] = useState<{ shortlist: Candidate[], meta: Metadata } | null>(null);

  useEffect(() => {
    Promise.all([getCombinedShortlist(), getRankingMetadata()]).then(([candidates, meta]) => {
      const shortlist = candidates.filter(c => c.rank <= 10).sort((a, b) => a.rank - b.rank);
      setData({ shortlist, meta });
    });
  }, []);

  const handleDownload = () => {
    if (!data) return;
    const content = `# Investigation Report: REQ-2026-001

## Executive Summary
Model Used: ${data.meta.model}
Total Candidates Evaluated: ${data.meta.totalEvaluated.toLocaleString()}
Total Candidates Retrieved: ${data.meta.retrieved.toLocaleString()}
Final Shortlist Size: ${data.meta.shortlisted}

## Top 10 Candidates
${data.shortlist.map((c) => `${c.rank}. ${c.name} - ${c.title} (Score: ${c.matchScore}%)
   Retrieved because: ${c.decisionPath.rankedBecause.join(', ')}
   Risk: ${c.decisionPath.penalizedBecause.join(', ') || 'None identified'}`).join('\n\n')}

## Rejection Patterns
${data.meta.rejections.map(r => `- ${r.reason}: ${r.count} candidates`).join('\n')}
`;
    const blob = new Blob([content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "investigation_report_2026_001.md";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!data) return <div className="h-screen bg-[#0A0A0A]" />;

  return (
    <div className="h-screen bg-[#0A0A0A] text-[#e5e2e1] font-sans overflow-hidden flex flex-col">
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

      <main className="pt-24 px-4 md:px-10 max-w-4xl mx-auto w-full flex-1 flex flex-col">
        <header className="mb-10 flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-semibold text-white mb-2">Investigation Report</h1>
            <p className="text-sm text-[#A3A3A3]">Compiled findings for Req 2026-001.</p>
          </div>
          <button onClick={handleDownload} className="flex items-center gap-2 bg-white text-black px-4 py-2 font-bold text-xs uppercase tracking-widest rounded hover:bg-gray-200 transition-colors">
            <Download className="w-4 h-4" />
            Export Markdown
          </button>
        </header>

        <div className="space-y-6 overflow-y-auto scrollbar-thin pb-20 pr-4">
          
          {/* Summary */}
          <section className="border border-[#262626] bg-[#111111] p-6 rounded-lg">
            <h2 className="text-xs font-bold text-white uppercase tracking-widest flex items-center gap-2 mb-4">
              <FileText className="w-4 h-4" /> Executive Summary
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-[#141313] p-4 border border-[#262626] rounded">
                <p className="text-[10px] text-[#A3A3A3] font-mono mb-1">EVALUATED</p>
                <p className="text-xl font-semibold text-white">{data.meta.totalEvaluated.toLocaleString()}</p>
              </div>
              <div className="bg-[#141313] p-4 border border-[#262626] rounded">
                <p className="text-[10px] text-[#A3A3A3] font-mono mb-1">RETRIEVED</p>
                <p className="text-xl font-semibold text-white">{data.meta.retrieved.toLocaleString()}</p>
              </div>
              <div className="bg-[#141313] p-4 border border-[#262626] rounded">
                <p className="text-[10px] text-[#A3A3A3] font-mono mb-1">RANKED</p>
                <p className="text-xl font-semibold text-white">{data.meta.ranked.toLocaleString()}</p>
              </div>
              <div className="bg-[#22C55E]/10 p-4 border border-[#22C55E]/30 rounded">
                <p className="text-[10px] text-[#22C55E] font-bold uppercase mb-1">SHORTLIST</p>
                <p className="text-xl font-semibold text-[#22C55E]">{data.meta.shortlisted}</p>
              </div>
            </div>
          </section>

          {/* Reasoning Samples */}
          <section className="border border-[#262626] bg-[#111111] p-6 rounded-lg">
            <h2 className="text-xs font-bold text-white uppercase tracking-widest flex items-center gap-2 mb-4">
              <CheckCircle2 className="w-4 h-4 text-[#22C55E]" /> Reasoning Samples (Top Candidates)
            </h2>
            <div className="space-y-4">
              {data.shortlist.slice(0, 3).map(c => (
                <div key={c.id} className="bg-[#141313] border border-[#262626] rounded p-4">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-sm font-semibold text-white">#{c.rank} {c.name} - {c.title}</h3>
                    <span className="text-[10px] font-mono text-[#22C55E] bg-[#22C55E]/10 px-2 py-1 rounded border border-[#22C55E]/20">SCORE: {c.matchScore}%</span>
                  </div>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-[10px] text-[#A3A3A3] font-mono mb-1">PROMOTED BECAUSE</p>
                      <p className="text-xs text-[#c4c7c8]">{c.decisionPath.rankedBecause.join('. ')}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-[#A3A3A3] font-mono mb-1">RISK IDENTIFIED</p>
                      <p className="text-xs text-[#c4c7c8]">{c.decisionPath.penalizedBecause.join('. ') || 'None significant.'}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Rejection Patterns */}
          <section className="border border-[#262626] bg-[#111111] p-6 rounded-lg">
            <h2 className="text-xs font-bold text-white uppercase tracking-widest flex items-center gap-2 mb-4">
              <ShieldAlert className="w-4 h-4 text-[#EF4444]" /> Major Rejection Patterns
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data.meta.rejections.map(r => (
                <div key={r.reason} className="bg-[#141313] border border-[#262626] rounded p-3 flex justify-between items-center">
                  <span className="text-xs text-[#c4c7c8] font-medium">{r.reason}</span>
                  <span className="text-xs font-mono text-[#EF4444] bg-[#EF4444]/10 px-2 py-0.5 rounded">{r.count}</span>
                </div>
              ))}
            </div>
          </section>

        </div>
      </main>
    </div>
  );
}
