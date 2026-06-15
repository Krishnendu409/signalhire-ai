"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import { useEffect, useState } from "react"
import { AlertTriangle, Fingerprint, XCircle, CheckCircle2, User, Terminal, ArrowRight, ShieldAlert, Users, Brain, Clock, Cpu, Zap, ShieldCheck, Target, TrendingUp, Search, Database, BarChart3, Shield } from "lucide-react"
// Removed unused imports

const stats = [
  { label: "Candidates Analyzed", value: "116,423", icon: Users },
  { label: "Recruiter Features", value: "22", icon: Brain },
  { label: "Inference Time", value: "<16s", icon: Clock },
  { label: "CPU Only", value: "2GB", icon: Cpu },
]

const dimensions = [
  {
    title: "Technical Fit",
    description: "Retrieval, ranking, vector DBs, evaluation frameworks, production ML",
    icon: Brain,
    color: "from-blue-500 to-cyan-500",
    bgColor: "bg-blue-500/10",
    borderColor: "border-blue-500/20",
    textColor: "text-blue-400"
  },
  {
    title: "Startup Readiness",
    description: "Ownership mindset, cross-functional work, greenfield experience",
    icon: Zap,
    color: "from-purple-500 to-pink-500",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/20",
    textColor: "text-purple-400"
  },
  {
    title: "Candidate Authenticity",
    description: "Career consistency, timeline integrity, synthetic profile detection",
    icon: ShieldCheck,
    color: "from-emerald-500 to-teal-500",
    bgColor: "bg-emerald-500/10",
    borderColor: "border-emerald-500/20",
    textColor: "text-emerald-400"
  },
  {
    title: "Hireability",
    description: "Response rates, notice periods, recruiter engagement, recency",
    icon: Target,
    color: "from-amber-500 to-orange-500",
    bgColor: "bg-amber-500/10",
    borderColor: "border-amber-500/20",
    textColor: "text-amber-400"
  },
  {
    title: "Behavioral Reliability",
    description: "Role progression slope, leadership momentum, open-source activity",
    icon: TrendingUp,
    color: "from-rose-500 to-red-500",
    bgColor: "bg-rose-500/10",
    borderColor: "border-rose-500/20",
    textColor: "text-rose-400"
  },
]

const pipelineSteps = [
  { step: "01", title: "Dataset Upload", desc: "Ingest CSV/JSONL candidate pools", icon: Database },
  { step: "02", title: "Feature Extraction", desc: "22 handcrafted recruiter signals", icon: Search },
  { step: "03", title: "Affinity Scoring", desc: "Deterministic matching on Skills, Title, Career", icon: BarChart3 },
  { step: "04", title: "Forensic Filtering", desc: "Honeypot & consistency detection", icon: Shield },
]

export default function Home() {
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
      <main className="flex-1 flex flex-col items-stretch max-w-7xl mx-auto w-full p-6 lg:p-12 gap-6">
        
        {/* Hero Section */}
        <div className="flex flex-col lg:flex-row gap-6 w-full">
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
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="flex flex-wrap gap-3">
              <Link href="/new">
                <button className="bg-white text-black px-6 py-3 font-semibold text-sm rounded flex items-center gap-2 hover:bg-gray-200 transition-colors">
                  Start a search <ArrowRight className="w-4 h-4" />
                </button>
              </Link>
              <Link href="/workspace">
                <button className="border border-[#404040] text-white px-6 py-3 font-semibold text-sm rounded hover:bg-[#171717] transition-colors">
                  View sample shortlist
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
                  <h2 className="text-lg text-white font-medium">Alex Chen</h2>
                  <p className="text-[10px] text-[#A3A3A3] font-mono mt-1">ATS SCORE: 42%</p>
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
                <div className="flex items-start gap-3 border-l-2 border-[#F59E0B] pl-3">
                  <AlertTriangle className="text-[#F59E0B] w-4 h-4 shrink-0" />
                  <div>
                    <p className="text-[#F59E0B] mb-1">Audit Finding</p>
                    <p className="text-[10px] text-[#A3A3A3]">Domain Contradiction Detected</p>
                  </div>
                </div>
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
                  <h2 className="text-lg text-white font-medium">Sarah Jenkins</h2>
                  <p className="text-[10px] text-[#A3A3A3] font-mono mt-1">MATCH SCORE: 98%</p>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 mb-4">
                <span className="px-2 py-1 bg-[#0A0A0A] border border-[#262626] text-[10px] font-mono text-white rounded-sm">Skill Affinity: 0.95</span>
                <span className="px-2 py-1 bg-[#0A0A0A] border border-[#262626] text-[10px] font-mono text-white rounded-sm">Career Affinity: 0.88</span>
              </div>

              <div className="pt-4 border-t border-[#262626] flex items-center gap-2 text-[#22C55E]">
                <CheckCircle2 className="w-4 h-4" />
                <span className="text-xs font-bold uppercase tracking-widest">RECOMMENDED</span>
              </div>
            </section>
          </motion.div>
        </div>

        {/* 5 Dimensions Section */}
        <section id="dimensions" className="mt-32">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-4">
              Five Dimensions of <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">Recruiter Cognition</span>
            </h2>
            <p className="text-slate-400 max-w-xl mx-auto">
              We don't just measure keyword overlap. We model how a senior recruiter actually evaluates a candidate.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {dimensions.map((dim, i) => (
              <motion.div
                key={dim.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                whileHover={{ y: -6, scale: 1.02 }}
                className={`p-7 rounded-2xl bg-white/[0.02] border ${dim.borderColor} hover:bg-white/[0.04] transition-all relative overflow-hidden group`}
              >
                <div className={`absolute inset-0 bg-gradient-to-br ${dim.color} opacity-0 group-hover:opacity-[0.03] transition-opacity`} />
                <div className="relative z-10">
                  <div className={`w-12 h-12 rounded-xl ${dim.bgColor} flex items-center justify-center mb-5`}>
                    <dim.icon className={`w-6 h-6 ${dim.textColor}`} />
                  </div>
                  <h3 className="text-lg font-bold mb-2 text-slate-100">{dim.title}</h3>
                  <p className="text-sm text-slate-400 leading-relaxed">{dim.description}</p>
                </div>
              </motion.div>
            ))}
            {/* Extra card: The result */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.5 }}
              className="p-7 rounded-2xl bg-gradient-to-br from-blue-600/10 to-indigo-600/10 border border-blue-500/20 flex flex-col justify-center items-center text-center"
            >
              <CheckCircle2 className="w-10 h-10 text-blue-400 mb-4" />
              <h3 className="text-lg font-bold mb-2">Top 100 Ranked</h3>
              <p className="text-sm text-slate-400">With recruiter-style SHAP reasoning for every candidate</p>
            </motion.div>
          </div>
        </section>

        {/* Pipeline Section */}
        <section id="pipeline" className="mt-32">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-4">
              The <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">Ranking Pipeline</span>
            </h2>
            <p className="text-slate-400 max-w-xl mx-auto">
              100,000 → 10,000 → 100. Four stages. Under 35 seconds on CPU.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {pipelineSteps.map((s, i) => (
              <motion.div
                key={s.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-emerald-500/20 transition-all group"
              >
                <div className="text-4xl font-extrabold text-white/5 group-hover:text-emerald-500/10 transition-colors mb-4">{s.step}</div>
                <s.icon className="w-6 h-6 text-emerald-400 mb-3" />
                <h3 className="text-base font-bold mb-1">{s.title}</h3>
                <p className="text-xs text-slate-500">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}