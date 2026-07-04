"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Fingerprint, BarChart2, Filter, ChevronDown, Activity,
  AlertCircle, TrendingUp, Users, Loader2, Zap
} from "lucide-react";
import { getRankingMetadataClient, get100kStatus } from "@/lib/api-client";

type Metadata = Awaited<ReturnType<typeof getRankingMetadataClient>>;
type Signal = Metadata["signals"][0];

export default function AnalyticsPage() {
  const [data, setData] = useState<Metadata | null>(null);
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        // Check if pipeline is running
        const statusRes = await get100kStatus();
        if (mounted && statusRes.status === "running") {
          setPipelineRunning(true);
        }

        const meta = await getRankingMetadataClient();
        if (mounted) {
          setData(meta);
          setPipelineRunning(false);
        }
      } catch (e) {
        if (mounted) {
          setError("Cannot reach backend. Make sure the FastAPI server is running on port 8000.");
        }
      }
    }

    load();

    // Poll every 3 seconds if pipeline is running
    const interval = setInterval(async () => {
      if (!mounted) return;
      try {
        const s = await get100kStatus();
        if (s.status === "running") {
          setPipelineRunning(true);
        } else if (s.status === "completed") {
          clearInterval(interval);
          const meta = await getRankingMetadataClient();
          if (mounted) { setData(meta); setPipelineRunning(false); }
        }
      } catch { /* ignore transient */ }
    }, 3000);

    return () => { mounted = false; clearInterval(interval); };
  }, []);

  if (error) {
    return (
      <div className="h-screen bg-[#0A0A0A] flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-10 h-10 text-[#EF4444] mx-auto mb-4" />
          <p className="text-white text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="h-screen bg-[#0A0A0A] flex items-center justify-center">
        <Loader2 className="w-6 h-6 text-white animate-spin" />
      </div>
    );
  }

  const hasPipelineData = data.totalEvaluated > 0;

  return (
    <div className="h-screen bg-[#0A0A0A] text-[#e5e2e1] font-sans overflow-hidden flex flex-col">
      {/* Top Navigation */}
      <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-4 md:px-10 h-14 bg-[#141313] border-b border-[#262626]">
        <Link href="/" className="flex items-center gap-3">
          <Fingerprint className="text-white w-5 h-5" />
          <span className="text-base font-semibold text-white tracking-tight">SignalHire</span>
        </Link>
        <div className="hidden md:flex items-center gap-6">
          <Link className="text-[#c4c7c8] text-xs hover:bg-[#353434] transition-colors px-3 py-1 rounded" href="/new">New Investigation</Link>
          <Link className="text-[#c4c7c8] text-xs hover:bg-[#353434] transition-colors px-3 py-1 rounded" href="/workspace">Workspace</Link>
          <Link className="text-white font-bold text-xs bg-[#353434] px-3 py-1 rounded" href="/analytics">Analytics</Link>
          <Link className="text-[#c4c7c8] text-xs hover:bg-[#353434] transition-colors px-3 py-1 rounded" href="/reports">Reports</Link>
        </div>
      </nav>

      <main className="pt-20 px-4 md:px-10 max-w-7xl mx-auto w-full flex-1 overflow-y-auto scrollbar-thin pb-20">
        <header className="mb-8 flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-semibold text-white mb-2">Investigation Analytics</h1>
            <p className="text-sm text-[#A3A3A3]">
              {hasPipelineData
                ? <span className="flex items-center gap-1.5"><Zap className="w-3.5 h-3.5 text-[#22C55E]" />100k Pipeline — {data.totalEvaluated.toLocaleString()} candidates evaluated</span>
                : "Run the 100k pipeline to populate this dashboard."}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {pipelineRunning && (
              <div className="flex items-center gap-1.5 text-xs text-[#F59E0B]">
                <Loader2 className="w-3.5 h-3.5 animate-spin" /> Pipeline running…
              </div>
            )}
            <div className="flex items-center gap-2 text-xs font-mono text-[#A3A3A3]">
              <Activity className="w-4 h-4 text-[#22C55E]" />
              MODEL: {(data.model || "—").toUpperCase()}
            </div>
          </div>
        </header>

        {!hasPipelineData ? (
          /* Empty state — pipeline not yet run */
          <div className="border border-dashed border-[#262626] rounded-xl p-16 flex flex-col items-center justify-center text-center">
            <BarChart2 className="w-10 h-10 text-[#333] mb-4" />
            <h2 className="text-lg font-semibold text-white mb-2">No data yet</h2>
            <p className="text-sm text-[#A3A3A3] max-w-md mb-6">
              Run the <strong className="text-white">100k Pipeline</strong> to generate analytics data.
            </p>
            <Link
              href="/new"
              className="flex items-center gap-2 bg-white text-black px-5 py-2.5 rounded font-bold text-xs uppercase tracking-widest hover:bg-gray-200 transition-colors"
            >
              <Zap className="w-4 h-4" /> Go to Pipeline
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Column 1: Funnel & Skills */}
            <div className="space-y-6">
              <div className="border border-[#262626] bg-[#111111] rounded-lg p-5">
                <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                  <Filter className="w-4 h-4" /> Retrieval Funnel
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center bg-[#141313] p-3 border border-[#262626] rounded">
                    <span className="text-xs text-[#c4c7c8]">Evaluated</span>
                    <span className="font-mono text-sm text-white">{data.totalEvaluated.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-center"><ChevronDown className="w-4 h-4 text-[#404040]" /></div>
                  <div className="flex justify-between items-center bg-[#141313] p-3 border border-[#262626] rounded w-11/12 mx-auto">
                    <span className="text-xs text-[#c4c7c8]">Retrieved</span>
                    <span className="font-mono text-sm text-white">{data.retrieved.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-center"><ChevronDown className="w-4 h-4 text-[#404040]" /></div>
                  <div className="flex justify-between items-center bg-[#141313] p-3 border border-[#262626] rounded w-5/6 mx-auto">
                    <span className="text-xs text-[#c4c7c8]">Ranked</span>
                    <span className="font-mono text-sm text-white">{data.ranked.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-center"><ChevronDown className="w-4 h-4 text-[#404040]" /></div>
                  <div className="flex justify-between items-center bg-[#22C55E]/10 p-3 border border-[#22C55E]/30 rounded w-4/6 mx-auto">
                    <span className="text-xs text-[#22C55E] font-bold uppercase tracking-wider">Shortlist</span>
                    <span className="font-mono text-sm text-[#22C55E] font-bold">{data.shortlisted}</span>
                  </div>
                </div>
              </div>

              <div className="border border-[#262626] bg-[#111111] rounded-lg p-5">
                <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                  <Users className="w-4 h-4" /> Skill Distribution (Top 100)
                </h3>
                <div className="space-y-2">
                  {Object.entries(data.skills).length > 0 ? (
                    Object.entries(data.skills).map(([skill, count]) => (
                      <div key={skill} className="flex items-center justify-between">
                        <span className="text-xs text-[#c4c7c8] capitalize">{skill}</span>
                        <div className="flex items-center gap-3">
                          <div className="w-32 h-1.5 bg-[#262626] rounded-full overflow-hidden">
                            <div className="h-full bg-white" style={{ width: `${(count / 100) * 100}%` }} />
                          </div>
                          <span className="font-mono text-xs w-6 text-right text-white">{count}</span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-[#8e9192]">No skill data available yet.</p>
                  )}
                </div>
              </div>
            </div>

            {/* Column 2: Signals */}
            <div className="border border-[#262626] bg-[#111111] rounded-lg p-5 flex flex-col">
              <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                <TrendingUp className="w-4 h-4" /> Top Ranking Signals
              </h3>
              <p className="text-xs text-[#A3A3A3] mb-6">Click a signal to view its impact on the final shortlist.</p>

              <div className="space-y-3 mb-8">
                {data.signals.length > 0 ? data.signals.map(sig => (
                  <button
                    key={sig.name}
                    onClick={() => setSelectedSignal(sig)}
                    className={`w-full flex items-center justify-between p-3 border rounded transition-all text-left ${
                      selectedSignal?.name === sig.name
                        ? "bg-white text-black border-white"
                        : "bg-[#141313] border-[#262626] hover:border-[#404040]"
                    }`}
                  >
                    <span className="text-sm font-semibold">{sig.name}</span>
                    <span className="font-mono text-xs opacity-70">{sig.count} Candidates</span>
                  </button>
                )) : (
                  <p className="text-xs text-[#8e9192]">Run the pipeline to see signal data.</p>
                )}
              </div>

              {selectedSignal ? (
                <div className="mt-auto p-4 border border-[#262626] bg-[#0A0A0A] rounded">
                  <h4 className="text-xs font-bold uppercase tracking-widest mb-3 text-white">Signal Impact: {selectedSignal.name}</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-[10px] text-[#A3A3A3] font-mono mb-1">AVERAGE RANK</p>
                      <p className="text-2xl font-semibold text-white">#{selectedSignal.avgRank}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-[#A3A3A3] font-mono mb-1">AVERAGE SCORE</p>
                      <p className="text-2xl font-semibold text-[#22C55E]">{selectedSignal.avgScore}%</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="mt-auto p-4 border border-dashed border-[#262626] rounded flex items-center justify-center h-28 text-xs text-[#8e9192]">
                  Select a signal to drill down.
                </div>
              )}
            </div>

            {/* Column 3: Rejections */}
            <div className="border border-[#262626] bg-[#111111] rounded-lg p-5">
              <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-[#EF4444]" /> Rejection Analysis
              </h3>
              <div className="space-y-4">
                {data.rejections.length > 0 ? data.rejections.map(rej => (
                  <div key={rej.reason} className="p-4 bg-[#141313] border border-[#262626] rounded border-l-2 border-l-[#EF4444]">
                    <div className="flex justify-between items-start mb-2">
                      <span className="text-xs font-bold text-[#EF4444] uppercase tracking-wider">{rej.reason}</span>
                      <span className="font-mono text-[10px] text-white bg-[#262626] px-1.5 py-0.5 rounded">
                        {rej.count.toLocaleString()} cases
                      </span>
                    </div>
                    <p className="text-[10px] text-[#A3A3A3] leading-relaxed">
                      Candidates failed to meet confidence threshold due to lack of verifiable evidence in this category.
                    </p>
                  </div>
                )) : (
                  <p className="text-xs text-[#8e9192]">No rejection data yet. Run the pipeline.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
