"use client"

import Link from "next/link"
import { AppShell } from "@/components/layout/AppShell"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  BookOpen,
  Terminal,
  ArrowRight,
  Layers,
  FileCode,
} from "lucide-react"

const glossary = [
  {
    term: "Code / Program",
    plain: "Instructions a computer follows, written in a language like Python.",
    here: "The hackathon pipeline is Python scripts in the hackathon_pipeline/ folder.",
  },
  {
    term: "Frontend",
    plain: "What you see in the browser — buttons, pages, colors.",
    here: "The Next.js app in frontend/ — this dashboard you're using.",
  },
  {
    term: "Backend",
    plain: "The server that stores data and runs logic behind the scenes.",
    here: "The FastAPI app in backend/ — handles jobs, candidates, rankings (optional for hackathon).",
  },
  {
    term: "API",
    plain: "A way for two programs to talk. Like a waiter taking your order to the kitchen.",
    here: "The frontend could ask the backend for ranked candidates via HTTP requests.",
  },
  {
    term: "Database",
    plain: "Organized storage for information, like a giant spreadsheet.",
    here: "PostgreSQL stores jobs and candidates in the full app; the hackathon uses JSONL files instead.",
  },
  {
    term: "Embedding",
    plain: "Turning text into a list of numbers so a computer can compare meaning.",
    here: "Each candidate profile becomes a vector; similar profiles have similar numbers.",
  },
  {
    term: "Retrieval",
    plain: "Finding the most relevant items from a huge pile.",
    here: "From 100,000 candidates, we narrow to ~10,000 who might fit the job.",
  },
  {
    term: "Ranking",
    plain: "Sorting items from best to worst for a specific goal.",
    here: "LightGBM scores and orders candidates 1–100 for the hackathon submission.",
  },
  {
    term: "Feature",
    plain: "A measurable signal about something — like 'years of ML experience'.",
    here: "22 handcrafted features like retrieval_experience_score, trust_score, etc.",
  },
  {
    term: "Model / ML",
    plain: "Software that learned patterns from data to make predictions.",
    here: "LightGBM learned how features combine to predict recruiter preference.",
  },
  {
    term: "CSV",
    plain: "A simple text file with rows and columns, opens in Excel.",
    here: "submission.csv is what you submit to the hackathon — top 100 candidates.",
  },
  {
    term: "Docker",
    plain: "Packages an app and its dependencies into a container that runs anywhere.",
    here: "docker-compose.yml starts database, backend, and frontend together.",
  },
]

const hackathonSteps = [
  {
    step: "1",
    title: "Get the dataset",
    cmd: "Place [PUB] India_runs_data_and_ai_challenge/ next to the project",
    detail: "Contains candidates.jsonl (100k profiles) and job_description.docx",
  },
  {
    step: "2",
    title: "Install Python packages",
    cmd: "pip install pandas numpy scikit-learn lightgbm sentence-transformers",
    detail: "These libraries handle data, math, and AI models",
  },
  {
    step: "3",
    title: "Run offline embedder (once)",
    cmd: "python hackathon_pipeline/offline_embedder.py",
    detail: "Takes 1–2 hours — converts all profiles to embeddings",
  },
  {
    step: "4",
    title: "Train the ranker (once)",
    cmd: "python hackathon_pipeline/train_lightgbm.py",
    detail: "Creates lgbm_ranker.txt in ~1 minute",
  },
  {
    step: "5",
    title: "Generate submission",
    cmd: "python hackathon_pipeline/run_ranking.py",
    detail: "Outputs submission.csv with top 100 ranked candidates",
  },
  {
    step: "6",
    title: "View in dashboard",
    cmd: "cd frontend && npm run dev",
    detail: "Open http://localhost:3000/dashboard to explore results",
  },
]

export default function LearnPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-4xl px-6 py-12">
        <div className="mb-12 text-center">
          <Badge className="mb-4 border-violet-500/20 bg-violet-500/10 text-violet-300">
            Beginner Guide
          </Badge>
          <h1 className="text-4xl font-extrabold text-white">Learn the Project</h1>
          <p className="mx-auto mt-4 max-w-2xl text-slate-400">
            Everything explained in plain English — what each piece does and how to run it for
            the hackathon.
          </p>
        </div>

        <section className="mb-16">
          <h2 className="mb-4 flex items-center gap-2 text-xl font-bold text-white">
            <Layers className="h-5 w-5 text-blue-400" />
            What is SignalHire AI?
          </h2>
          <Card className="space-y-4 rounded-2xl border-white/5 bg-white/[0.03] p-6 text-sm leading-relaxed text-slate-300">
            <p>
              Imagine you're hiring an ML engineer. You have <strong className="text-white">100,000 resumes</strong>{" "}
              and one job description. You can't read them all — and keyword search fails because
              people stuff fake skills into profiles.
            </p>
            <p>
              SignalHire AI acts like a <strong className="text-white">smart recruiter</strong>. It
              reads the job, scans all candidates, filters fakes, scores real fit across 5
              dimensions, and gives you the <strong className="text-white">top 100</strong> with
              explanations.
            </p>
            <p>
              The project has two parts: a <strong className="text-white">hackathon pipeline</strong>{" "}
              (Python scripts that produce submission.csv) and a <strong className="text-white">web dashboard</strong>{" "}
              (what you're looking at now) to visualize results.
            </p>
          </Card>
        </section>

        <section className="mb-16">
          <h2 className="mb-6 flex items-center gap-2 text-xl font-bold text-white">
            <Terminal className="h-5 w-5 text-emerald-400" />
            Hackathon Setup Checklist
          </h2>
          <div className="space-y-4">
            {hackathonSteps.map((s) => (
              <Card
                key={s.step}
                className="rounded-2xl border-white/5 bg-white/[0.02] p-5"
              >
                <div className="flex gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-500/10 text-sm font-bold text-blue-400">
                    {s.step}
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="font-semibold text-white">{s.title}</h3>
                    <p className="mt-1 text-xs text-slate-500">{s.detail}</p>
                    <code className="mt-3 block overflow-x-auto rounded-lg bg-black/40 px-3 py-2 text-xs text-emerald-300">
                      {s.cmd}
                    </code>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </section>

        <section className="mb-16">
          <h2 className="mb-6 flex items-center gap-2 text-xl font-bold text-white">
            <BookOpen className="h-5 w-5 text-amber-400" />
            Glossary — CS Terms Explained
          </h2>
          <div className="space-y-3">
            {glossary.map((g) => (
              <Card
                key={g.term}
                className="rounded-xl border-white/5 bg-white/[0.02] p-4"
              >
                <h3 className="font-semibold text-blue-300">{g.term}</h3>
                <p className="mt-1 text-sm text-slate-400">{g.plain}</p>
                <p className="mt-2 text-xs text-slate-500">
                  <span className="font-medium text-slate-400">In this project: </span>
                  {g.here}
                </p>
              </Card>
            ))}
          </div>
        </section>

        <section className="mb-12">
          <h2 className="mb-4 flex items-center gap-2 text-xl font-bold text-white">
            <FileCode className="h-5 w-5 text-violet-400" />
            Project Folder Map
          </h2>
          <Card className="rounded-2xl border-white/5 bg-black/30 p-6 font-mono text-xs text-slate-300">
            <pre className="overflow-x-auto leading-relaxed">{`signalhire-ai/
├── hackathon_pipeline/     ← Python ranking engine (main hackathon work)
│   ├── offline_embedder.py ← Step 1: build embeddings (slow, run once)
│   ├── train_lightgbm.py   ← Step 2: train ranker model
│   ├── run_ranking.py      ← Step 3: produce submission.csv
│   └── feature_extractor.py← 22 recruiter features
├── submission.csv          ← Your hackathon output (top 100)
├── lgbm_ranker.txt         ← Trained AI model file
├── frontend/               ← Web dashboard (Next.js)
└── backend/                ← Full app API (optional for hackathon)`}</pre>
          </Card>
        </section>

        <div className="flex justify-center">
          <Link href="/dashboard">
            <Button className="rounded-xl bg-blue-600 px-8 hover:bg-blue-500">
              View Results Dashboard
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </div>
    </AppShell>
  )
}
