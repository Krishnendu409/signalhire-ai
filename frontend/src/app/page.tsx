"use client"

import Link from "next/link"
import { motion } from "framer-motion"
import {
  Sparkles,
  ArrowRight,
  Brain,
  ShieldCheck,
  Target,
  TrendingUp,
  Zap,
  Search,
  Database,
  BarChart3,
  Shield,
  CheckCircle2,
  Users,
  Clock,
  Cpu,
} from "lucide-react"
import { AppShell } from "@/components/layout/AppShell"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

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
    borderColor: "border-blue-500/20",
    textColor: "text-blue-400",
    bgColor: "bg-blue-500/10",
  },
  {
    title: "Startup Readiness",
    description: "Ownership mindset, cross-functional work, greenfield experience",
    icon: Zap,
    borderColor: "border-purple-500/20",
    textColor: "text-purple-400",
    bgColor: "bg-purple-500/10",
  },
  {
    title: "Candidate Authenticity",
    description: "Career consistency, timeline integrity, synthetic profile detection",
    icon: ShieldCheck,
    borderColor: "border-emerald-500/20",
    textColor: "text-emerald-400",
    bgColor: "bg-emerald-500/10",
  },
  {
    title: "Hireability",
    description: "Response rates, notice periods, recruiter engagement, recency",
    icon: Target,
    borderColor: "border-amber-500/20",
    textColor: "text-amber-400",
    bgColor: "bg-amber-500/10",
  },
  {
    title: "Behavioral Reliability",
    description: "Role progression slope, leadership momentum, open-source activity",
    icon: TrendingUp,
    borderColor: "border-rose-500/20",
    textColor: "text-rose-400",
    bgColor: "bg-rose-500/10",
  },
]

const pipelineSteps = [
  { step: "01", title: "Hybrid Retrieval", desc: "Top 5k Semantic ∪ Top 5k BM25", icon: Search },
  { step: "02", title: "Feature Extraction", desc: "22 handcrafted recruiter signals", icon: Database },
  { step: "03", title: "LambdaRank Scoring", desc: "LightGBM learns non-linear interactions", icon: BarChart3 },
  { step: "04", title: "Forensic Filtering", desc: "Honeypot & consistency detection", icon: Shield },
]

export default function Home() {
  return (
    <AppShell>
      <section className="mx-auto max-w-7xl px-6 pb-32 pt-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center"
        >
          <Badge className="mb-8 border-blue-500/20 bg-blue-500/10 text-blue-300">
            <span className="relative mr-2 inline-flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-500" />
            </span>
            Redrob Intelligent Candidate Discovery Challenge
          </Badge>

          <h1 className="mb-6 bg-gradient-to-br from-white via-blue-100 to-slate-400 bg-clip-text text-5xl font-extrabold tracking-tight text-transparent md:text-7xl lg:text-8xl">
            Recruiter Judgment,
            <br />
            Quantified.
          </h1>

          <p className="mx-auto mb-12 max-w-2xl text-lg font-light leading-relaxed text-slate-400 md:text-xl">
            SignalHire AI models how senior recruiters actually think — scoring candidates across{" "}
            <span className="font-semibold text-blue-400">5 cognitive dimensions</span> using 22
            handcrafted features. Detects keyword stuffers and honeypot profiles before ranking.
          </p>

          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link href="/dashboard">
              <Button className="h-14 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 px-10 text-base font-bold shadow-xl shadow-blue-600/25 hover:from-blue-500 hover:to-indigo-500">
                Open Dashboard
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link href="/learn">
              <Button
                variant="outline"
                className="h-14 rounded-2xl border-white/10 px-10 text-base text-slate-300 hover:bg-white/5"
              >
                <Sparkles className="mr-2 h-5 w-5" />
                Learn the Basics
              </Button>
            </Link>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="mt-20 grid grid-cols-2 gap-4 md:grid-cols-4"
        >
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-2xl border border-white/5 bg-white/[0.03] p-6 text-center"
            >
              <stat.icon className="mx-auto mb-3 h-5 w-5 text-blue-400" />
              <div className="mb-1 text-2xl font-extrabold text-white md:text-3xl">{stat.value}</div>
              <div className="text-xs font-medium text-slate-500">{stat.label}</div>
            </div>
          ))}
        </motion.div>

        <section id="dimensions" className="mt-32">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-3xl font-extrabold tracking-tight md:text-4xl">
              Five Dimensions of{" "}
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Recruiter Cognition
              </span>
            </h2>
            <p className="mx-auto max-w-xl text-slate-400">
              We model how a senior recruiter evaluates a candidate — not just keyword overlap.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
            {dimensions.map((dim, i) => (
              <motion.div
                key={dim.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                whileHover={{ y: -4 }}
                className={`rounded-2xl border ${dim.borderColor} bg-white/[0.02] p-7 transition-all hover:bg-white/[0.04]`}
              >
                <div className={`mb-5 flex h-12 w-12 items-center justify-center rounded-xl ${dim.bgColor}`}>
                  <dim.icon className={`h-6 w-6 ${dim.textColor}`} />
                </div>
                <h3 className="mb-2 text-lg font-bold text-slate-100">{dim.title}</h3>
                <p className="text-sm leading-relaxed text-slate-400">{dim.description}</p>
              </motion.div>
            ))}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="flex flex-col items-center justify-center rounded-2xl border border-blue-500/20 bg-gradient-to-br from-blue-600/10 to-indigo-600/10 p-7 text-center"
            >
              <CheckCircle2 className="mb-4 h-10 w-10 text-blue-400" />
              <h3 className="mb-2 text-lg font-bold">Top 100 Ranked</h3>
              <p className="text-sm text-slate-400">
                With recruiter-style reasoning for every candidate
              </p>
            </motion.div>
          </div>
        </section>

        <section id="pipeline" className="mt-32">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-3xl font-extrabold tracking-tight md:text-4xl">
              The{" "}
              <span className="bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
                Ranking Pipeline
              </span>
            </h2>
            <p className="mx-auto max-w-xl text-slate-400">
              100,000 → 10,000 → 100. Four stages. Under 35 seconds on CPU.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            {pipelineSteps.map((s, i) => (
              <motion.div
                key={s.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                className="group rounded-2xl border border-white/5 bg-white/[0.02] p-6 transition-all hover:border-emerald-500/20"
              >
                <div className="mb-4 text-4xl font-extrabold text-white/5 transition-colors group-hover:text-emerald-500/10">
                  {s.step}
                </div>
                <s.icon className="mb-3 h-6 w-6 text-emerald-400" />
                <h3 className="mb-1 text-base font-bold">{s.title}</h3>
                <p className="text-xs text-slate-500">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </section>
      </section>

      <footer className="border-t border-white/5 py-12">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 px-6 text-sm opacity-50 md:flex-row">
          <p>© 2026 SignalHire AI — Redrob Intelligent Candidate Discovery Challenge</p>
          <a
            href="https://github.com/Krishnendu409/signalhire-ai"
            className="hover:text-blue-400"
            target="_blank"
            rel="noreferrer"
          >
            GitHub
          </a>
        </div>
      </footer>
    </AppShell>
  )
}
