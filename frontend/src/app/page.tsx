"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { useEffect, useState } from "react"
import { AlertTriangle, Fingerprint, XCircle, CheckCircle2, User, Terminal, ArrowRight, ShieldAlert } from "lucide-react"
import { getLandingPageData } from "@/lib/api"
import type { Candidate } from "@/store/workspace"

export default function Home() {
  const [data, setData] = useState<{ trap: Candidate, elite: Candidate } | null>(null);

  useEffect(() => {
    getLandingPageData().then(setData);
  }, []);

  if (!data) return <div className="min-h-screen bg-[#0A0A0A]" />;
  return (
    <div className="min-h-screen bg-[#0A0A0A] text-[#E5E2E1] overflow-hidden flex flex-col font-sans selection:bg-[#22C55E]/30">
      
      {/* Top Header */}
      <header className="w-full z-50 flex justify-between items-center px-6 h-16 border-b border-[#262626] bg-[#0A0A0A]/80 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <Fingerprint className="text-white w-5 h-5" />
          <span className="text-sm font-semibold text-white tracking-tight">SignalHire AI</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs text-white/50 font-bold uppercase tracking-widest font-mono">Evidence-Driven Recruiting</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col lg:flex-row items-stretch max-w-7xl mx-auto w-full p-6 lg:p-12 gap-6">
        
        {/* Left Column: Narrative Copy */}
        <div className="flex-1 flex flex-col justify-center max-w-xl py-12 lg:pr-12">
          <motion.h1 
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} 
            className="text-4xl md:text-5xl font-semibold text-white leading-[1.1] tracking-tight mb-6"
          >
            Your ATS picked the wrong candidate.
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
            className="text-lg text-[#A3A3A3] leading-relaxed mb-10"
          >
            Traditional systems reward keyword matches. We expose fraudulent resumes and identify engineers who actually built retrieval, ranking, and search infrastructure.
          </motion.p>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
            <Link href="/new">
              <button className="bg-white text-black px-6 py-3 font-semibold text-sm rounded flex items-center gap-2 hover:bg-gray-200 transition-colors">
                Start Investigation <ArrowRight className="w-4 h-4" />
              </button>
            </Link>
          </motion.div>
        </div>

        {/* Right Column: Stitch Narrative UI */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: 0.3 }}
          className="flex-1 flex flex-col gap-4 max-w-md w-full relative"
        >
          
          {/* ATS Decision Section */}
          <section className="bg-[#111111] border border-[#262626] rounded-md p-5 relative overflow-hidden">
            <div className="flex justify-between items-center mb-4">
              <span className="font-mono text-[10px] uppercase tracking-widest text-[#EF4444]">ATS DECISION: REJECTED</span>
              <ShieldAlert className="text-[#EF4444] w-4 h-4" />
            </div>
            
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-[#171717] rounded border border-[#262626] flex items-center justify-center">
                <User className="text-[#A3A3A3] w-6 h-6" />
              </div>
              <div>
                <h2 className="text-lg text-white font-medium">{data.trap.title}</h2>
                <p className="text-[10px] text-[#A3A3A3] font-mono mt-1">ATS SCORE: {data.trap.matchScore}%</p>
              </div>
            </div>

            <div className="bg-[#EF4444]/10 border border-[#EF4444]/20 p-3 rounded-sm">
              <p className="text-xs text-[#EF4444] font-mono">Heavy keyword matches found in resume.</p>
            </div>

            {/* Overturned Stamp */}
            <div className="absolute inset-0 m-auto w-fit h-fit px-6 py-2 border-4 border-[#EF4444] text-[#EF4444] font-bold text-3xl transform -rotate-12 opacity-80 pointer-events-none select-none">
              OVERTURNED
            </div>
          </section>

          {/* Evidence Review Section */}
          <section className="bg-[#111111] border border-[#262626] rounded-md flex flex-col">
            <div className="border-b border-[#262626] p-3 flex justify-between items-center bg-[#171717]">
              <h3 className="font-mono text-[10px] text-white uppercase tracking-widest">EVIDENCE LOG</h3>
              <span className="font-mono text-[10px] text-[#A3A3A3]">SYS_AUDIT_V2.1</span>
            </div>
            <div className="p-4 flex flex-col gap-3 font-mono text-xs">
              {data.trap.decisionPath.penalizedBecause.map((reason, idx) => (
                <div key={idx} className="flex items-start gap-3 border-l-2 border-[#F59E0B] pl-3">
                  <AlertTriangle className="text-[#F59E0B] w-4 h-4 shrink-0" />
                  <div>
                    <p className="text-[#F59E0B] mb-1">Audit Finding</p>
                    <p className="text-[10px] text-[#A3A3A3]">{reason}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Correct Candidate Section */}
          <section className="bg-[#171717] border border-[#22C55E]/30 rounded-md p-5 shadow-[0_0_30px_rgba(34,197,94,0.05)]">
            <div className="flex justify-between items-center mb-4">
              <span className="font-mono text-[10px] uppercase tracking-widest text-white">EVIDENCE-DRIVEN RECOMMENDATION</span>
            </div>

            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-white rounded border border-[#262626] flex items-center justify-center">
                <Terminal className="text-black w-6 h-6" />
              </div>
              <div>
                <h2 className="text-lg text-white font-medium">{data.elite.title}</h2>
                <p className="text-[10px] text-[#A3A3A3] font-mono mt-1">MATCH SCORE: {data.elite.matchScore}%</p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 mb-4">
              {data.elite.decisionPath.rankedBecause.map((f, idx) => (
                <span key={idx} className="px-2 py-1 bg-[#0A0A0A] border border-[#262626] text-[10px] font-mono text-white rounded-sm">{f}</span>
              ))}
            </div>

            <div className="pt-4 border-t border-[#262626] flex items-center gap-2 text-[#22C55E]">
              <CheckCircle2 className="w-4 h-4" />
              <span className="text-xs font-bold uppercase tracking-widest">RECOMMENDED</span>
            </div>
          </section>

        </motion.div>
      </main>
    </div>
  )
}