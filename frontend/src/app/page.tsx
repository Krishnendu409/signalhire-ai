"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import {
  Sparkles,
  Search,
  TrendingUp,
  ShieldCheck,
  ArrowRight,
  Target,
  Zap,
  Brain,
  Database,
  BarChart3,
  Shield,
  Users,
  CheckCircle2,
  Clock,
  Cpu
} from "lucide-react"
import { Button } from "@/components/ui/button"

const stats = [
  { label: "Candidates Analyzed", value: "100,000", icon: Users },
  { label: "Recruiter Features", value: "22", icon: Brain },
  { label: "Inference Time", value: "<35s", icon: Clock },
  { label: "CPU Only", value: "16GB", icon: Cpu },
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
  { step: "01", title: "Hybrid Retrieval", desc: "Top 5k Semantic ∪ Top 5k BM25", icon: Search },
  { step: "02", title: "Feature Extraction", desc: "22 handcrafted recruiter signals", icon: Database },
  { step: "03", title: "LambdaRank Scoring", desc: "LightGBM learns non-linear interactions", icon: BarChart3 },
  { step: "04", title: "Forensic Filtering", desc: "Honeypot & consistency detection", icon: Shield },
]

export default function Home() {
  const [email, setEmail] = useState("")
  const router = useRouter()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    localStorage.setItem("signalhire_user", JSON.stringify({ email, id: "demo" }))
    router.push("/dashboard")
  }

  return (
    <div className="min-h-screen bg-[#020617] text-slate-50 selection:bg-blue-500/30 overflow-x-hidden">
      {/* Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 right-0 h-[600px] bg-gradient-to-b from-blue-950/30 to-transparent" />
        <div className="absolute -top-[10%] -left-[10%] w-[50%] h-[50%] bg-blue-600/15 blur-[150px] rounded-full" />
        <div className="absolute top-[20%] -right-[10%] w-[40%] h-[40%] bg-purple-600/15 blur-[150px] rounded-full" />
        <div className="absolute -bottom-[10%] left-[30%] w-[40%] h-[40%] bg-indigo-600/10 blur-[150px] rounded-full" />
      </div>

      {/* Nav */}
      <nav className="relative z-50 flex items-center justify-between px-6 py-5 max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold tracking-tight">SignalHire<span className="text-blue-400">AI</span></span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-400">
          <a href="#dimensions" className="hover:text-blue-400 transition-colors">Dimensions</a>
          <a href="#pipeline" className="hover:text-blue-400 transition-colors">Pipeline</a>
          <Button variant="ghost" className="text-slate-50 hover:bg-white/5" onClick={() => router.push("/dashboard")}>
            Dashboard →
          </Button>
        </div>
      </nav>

      {/* Hero */}
      <main className="relative z-10 pt-16 pb-32 px-6 max-w-7xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
            </span>
            Redrob Intelligent Candidate Discovery Challenge
          </div>

          <h1 className="text-5xl md:text-7xl lg:text-8xl font-extrabold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-br from-white via-blue-100 to-slate-400">
            Recruiter Judgment,<br />Quantified.
          </h1>

          <p className="max-w-2xl mx-auto text-lg md:text-xl text-slate-400 mb-12 leading-relaxed font-light">
            SignalHire AI models how senior recruiters actually think — scoring candidates across{" "}
            <span className="text-blue-400 font-semibold">5 cognitive dimensions</span>{" "}
            using 22 handcrafted features. Detects keyword stuffers, profile inconsistencies,
            and honeypot candidates before ranking.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 max-w-md mx-auto">
            <form onSubmit={handleSubmit} className="flex w-full group relative">
              <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl blur opacity-20 group-hover:opacity-40 transition duration-500" />
              <div className="relative flex w-full">
                <input
                  type="email"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full h-14 bg-[#0a0f25]/80 backdrop-blur-xl border border-white/10 rounded-l-xl px-5 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-lg"
                />
                <button
                  type="submit"
                  className="h-14 px-8 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold rounded-r-xl transition-all flex items-center gap-2 whitespace-nowrap shadow-xl hover:shadow-blue-500/25 active:scale-[0.98]"
                >
                  Launch <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>
            </form>
          </div>
        </motion.div>

        {/* Stats Bar */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-4"
        >
          {stats.map((stat) => (
            <div key={stat.label} className="p-6 rounded-2xl bg-white/[0.03] border border-white/5 text-center">
              <stat.icon className="w-5 h-5 text-blue-400 mx-auto mb-3" />
              <div className="text-2xl md:text-3xl font-extrabold text-white mb-1">{stat.value}</div>
              <div className="text-xs text-slate-500 font-medium">{stat.label}</div>
            </div>
          ))}
        </motion.div>

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

      <footer className="py-12 border-t border-white/5 mt-20">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6 opacity-50 text-sm">
          <p>© 2026 SignalHire AI — Redrob Intelligent Candidate Discovery Challenge</p>
          <div className="flex gap-8">
            <a href="https://github.com/Krishnendu409/signalhire-ai" className="hover:text-blue-400" target="_blank">GitHub</a>
          </div>
        </div>
      </footer>
    </div>
  )
}