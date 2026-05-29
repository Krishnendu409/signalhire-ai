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
  Zap
} from "lucide-react"
import { Button } from "@/components/ui/button"

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
      {/* Background Glows */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-blue-600/10 blur-[120px] rounded-full" />
        <div className="absolute top-[20%] -right-[10%] w-[35%] h-[35%] bg-purple-600/10 blur-[120px] rounded-full" />
        <div className="absolute -bottom-[10%] left-[20%] w-[30%] h-[30%] bg-indigo-600/10 blur-[120px] rounded-full" />
      </div>

      {/* Nav */}
      <nav className="relative z-50 flex items-center justify-between px-6 py-4 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <span className="text-xl font-bold tracking-tight">SignalHire<span className="text-blue-400">AI</span></span>
        </div>
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-400">
          <a href="#features" className="hover:text-blue-400 transition-colors">Technology</a>
          <a href="#research" className="hover:text-blue-400 transition-colors">Research</a>
          <Button variant="ghost" className="text-slate-50 hover:bg-white/5" onClick={() => router.push("/dashboard")}>
            Sign In
          </Button>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative z-10 pt-20 pb-32 px-6 max-w-7xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold mb-6">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
            </span>
            Next-Gen Recruiting Intelligence
          </div>
          
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-b from-white to-slate-400">
            Hire with Semantic <br />Intelligence, not Keywords.
          </h1>
          
          <p className="max-w-2xl mx-auto text-lg md:text-xl text-slate-400 mb-10 leading-relaxed">
            SignalHire AI ranks candidates using deep career trajectory modeling 
            and multi-signal assessment. Move beyond rigid ATS filters to find 
            the <span className="text-blue-400 font-medium">Safe Business Investment</span>.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 max-w-md mx-auto">
            <form onSubmit={handleSubmit} className="flex w-full group">
              <div className="relative flex-1">
                <input
                  type="email"
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full h-12 bg-white/5 border border-white/10 rounded-l-xl px-4 text-slate-100 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500 transition-all"
                />
              </div>
              <button
                type="submit"
                className="h-12 px-6 bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-r-xl transition-all flex items-center gap-2 whitespace-nowrap shadow-lg shadow-blue-600/20"
              >
                Access Alpha <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          </div>
        </motion.div>

        {/* Feature Grid */}
        <div id="features" className="mt-32 grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
          <FeatureCard 
            icon={<Target className="w-6 h-6 text-blue-400" />}
            title="Trajectory Archetypes"
            description="Identify Fast Climbers, Stable Performers, and Chaotic Hoppers with sub-second precision."
          />
          <FeatureCard 
            icon={<Search className="w-6 h-6 text-purple-400" />}
            title="Semantic Retrieval"
            description="Our dual-stage embedding pipeline understands intent, not just string matching."
          />
          <FeatureCard 
            icon={<ShieldCheck className="w-6 h-6 text-emerald-400" />}
            title="Legal Defensibility"
            description="Built-in multi-agent audit trails ensuring FCRA and Colorado AI Act compliance."
          />
        </div>

        {/* Research section teaser */}
        <motion.div 
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mt-32 p-8 md:p-12 rounded-3xl bg-gradient-to-br from-white/[0.03] to-transparent border border-white/5 relative overflow-hidden"
        >
          <div className="relative z-10 grid md:grid-cols-2 gap-12 items-center">
            <div className="text-left">
              <h2 className="text-3xl font-bold mb-4">Bridging Cognitive Sourcing & Probabilistic IR</h2>
              <p className="text-slate-400 leading-relaxed mb-6">
                Based on deep research into recruiter cognition, our layout-parsing engine 
                handles complex infographic resumes while maintaining a 0.95+ extraction 
                confidence. We model progression mathematically, projecting the next 
                logical career move.
              </p>
              <div className="flex gap-4">
                <div className="flex items-center gap-2 text-sm text-slate-300">
                  <Zap className="w-4 h-4 text-yellow-500" /> Sub-200ms Reranking
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-300">
                  <TrendingUp className="w-4 h-4 text-blue-500" /> BARS Evaluation
                </div>
              </div>
            </div>
            <div className="bg-slate-900/50 rounded-2xl p-6 border border-white/10 shadow-2xl relative group overflow-hidden">
               {/* Visual representation of a ranking profile */}
               <div className="space-y-4 opacity-80 group-hover:opacity-100 transition-opacity">
                  <div className="h-4 w-3/4 bg-slate-800 rounded animate-pulse" />
                  <div className="flex gap-2">
                    <div className="h-6 w-20 bg-blue-500/20 rounded-full border border-blue-500/30" />
                    <div className="h-6 w-24 bg-purple-500/20 rounded-full border border-purple-500/30" />
                  </div>
                  <div className="space-y-2">
                    <div className="h-2 w-full bg-slate-800 rounded" />
                    <div className="h-2 w-5/6 bg-slate-800 rounded" />
                  </div>
               </div>
               <div className="absolute inset-0 bg-gradient-to-t from-[#020617] via-transparent to-transparent" />
            </div>
          </div>
        </motion.div>
      </main>

      <footer className="py-12 border-t border-white/5 mt-20">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:row items-center justify-between gap-6 opacity-50 text-sm">
          <p>© 2026 SignalHire AI. Enterprise-Grade Candidate Ranking.</p>
          <div className="flex gap-8">
            <a href="#" className="hover:text-blue-400">Terms</a>
            <a href="#" className="hover:text-blue-400">Privacy</a>
            <a href="#" className="hover:text-blue-400">Security</a>
          </div>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) {
  return (
    <motion.div 
      whileHover={{ y: -5 }}
      className="p-6 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-white/10 transition-all hover:bg-white/[0.03]"
    >
      <div className="w-12 h-12 rounded-xl bg-white/5 flex items-center justify-center mb-4">
        {icon}
      </div>
      <h3 className="text-xl font-bold mb-2">{title}</h3>
      <p className="text-slate-400 leading-relaxed text-sm">{description}</p>
    </motion.div>
  )
}