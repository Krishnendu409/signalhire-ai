/**
 * api-client.ts — Pure client-side fetch helpers (NO 'use server').
 * Used by all client components that call the FastAPI backend directly
 * from the browser (pipeline/page.tsx, analytics/page.tsx, etc.)
 */

const API_BASE =
  (typeof process !== 'undefined' && process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, '')
    : 'http://localhost:8000') + '/api';

// ── 100k Pipeline ──────────────────────────────────────────────────────────

export async function run100kPipeline(): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/pipeline/run-100k`, {
    method: 'POST',
    cache: 'no-store',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to trigger 100k pipeline (${res.status})`);
  }
  return res.json();
}

export async function get100kStatus(): Promise<{
  status: string;
  progress: number;
  stage: string;
  error: string | null;
  has_results: boolean;
  elapsed_seconds: number | null;
}> {
  const res = await fetch(`${API_BASE}/pipeline/100k-status`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to fetch pipeline status (${res.status})`);
  return res.json();
}

export async function get100kResults(): Promise<{
  status: string;
  analytics?: {
    totalEvaluated: number;
    retrieved: number;
    ranked: number;
    shortlisted: number;
    model: string;
    skills: Record<string, number>;
    signals: Array<{ name: string; count: number; avgRank: number; avgScore: number }>;
    rejections: Array<{ reason: string; count: number }>;
  };
  results?: Array<Record<string, unknown>>;
  total_evaluated?: number;
  retrieved?: number;
  ranked?: number;
  shortlisted?: number;
  elapsed_seconds?: number;
  model?: string;
  scoring_method?: string;
  used_lgbm?: boolean;
  progress?: number;
  stage?: string;
  error?: string | null;
}> {
  const res = await fetch(`${API_BASE}/pipeline/100k-results`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`Failed to fetch 100k results (${res.status})`);
  return res.json();
}

// ── Rankings metadata (for analytics/reports pages) ───────────────────────

export async function getRankingMetadataClient(jobId?: string): Promise<{
  totalEvaluated: number;
  retrieved: number;
  ranked: number;
  shortlisted: number;
  model: string;
  jdTitle: string;
  skills: Record<string, number>;
  signals: Array<{ name: string; count: number; avgRank: number; avgScore: number }>;
  rejections: Array<{ reason: string; count: number }>;
}> {
  // First, try to get live 100k pipeline results
  try {
    const pipelineRes = await get100kResults();
    if (pipelineRes.status === 'completed' && pipelineRes.analytics) {
      const a = pipelineRes.analytics;
      return {
        totalEvaluated: a.totalEvaluated,
        retrieved: a.retrieved,
        ranked: a.ranked,
        shortlisted: a.shortlisted,
        model: a.model,
        jdTitle: 'Senior Search Engineer — 100k Pipeline',
        skills: a.skills,
        signals: a.signals,
        rejections: a.rejections,
      };
    }
  } catch {
    // fall through to legacy ranking
  }

  // Fallback: legacy ranking for a specific jobId
  if (!jobId) {
    return {
      totalEvaluated: 0, retrieved: 0, ranked: 0, shortlisted: 0,
      model: '—', jdTitle: '—', skills: {}, signals: [], rejections: [],
    };
  }

  const res = await fetch(`${API_BASE}/rankings/${jobId}/latest`, { cache: 'no-store' });
  if (!res.ok) {
    return {
      totalEvaluated: 0, retrieved: 0, ranked: 0, shortlisted: 0,
      model: '—', jdTitle: '—', skills: {}, signals: [], rejections: [],
    };
  }
  const data = await res.json();
  return {
    totalEvaluated: data.total_candidates || 0,
    retrieved: data.total_candidates || 0,
    ranked: (data.results || []).length,
    shortlisted: (data.results || []).filter((r: any) => (r.final_score ?? 0) >= 30).length,
    model: 'SignalHire Rank v1',
    jdTitle: data.query_text || 'Unknown Role',
    skills: {},
    signals: [],
    rejections: [],
  };
}
