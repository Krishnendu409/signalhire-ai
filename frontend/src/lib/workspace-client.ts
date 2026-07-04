import { getApiBase } from './api-base';
import type { Candidate } from '../store/workspace';

type RankingResult = {
  rank?: number;
  candidate_id: string;
  title?: string;
  final_score?: number;
  parsed_data?: Record<string, unknown>;
  dimension_scores?: Record<string, { score?: number }>;
  TitleAff_Contrib?: number;
  SkillAff_Contrib?: number;
  CareerAff_Contrib?: number;
  Quality_Contrib?: number;
  Penalties?: number;
  penalties?: number;
  SemSim_Contrib?: number;
  BM25_Contrib?: number;
  adaptation_risk?: string;
  transferability_evidence?: string[];
  matched_skills?: string[];
  missing_skills?: string[];
  adjacent_skills?: string[];
  explanation?: string;
};

function asStringArray(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.filter((item): item is string => typeof item === 'string');
  }
  if (typeof value === 'string' && value.trim()) {
    return value.split(',').map((s) => s.trim()).filter(Boolean);
  }
  return [];
}

function buildRecruiterSignals(record: Record<string, unknown>): string[] {
  const signals = (record.redrob_signals as Record<string, unknown>) || {};
  const responseRate = signals.recruiter_response_rate;
  const noticeDays = signals.notice_period_days;
  const lines: string[] = [];
  if (typeof responseRate === 'number') {
    lines.push(`Response Rate: ${Math.round(responseRate * 100)}%`);
  }
  if (typeof noticeDays === 'number') {
    lines.push(`Notice Period: ${noticeDays} days`);
  }
  if (lines.length === 0) {
    lines.push('Response Rate: 0%', 'Notice Period: 30 days');
  }
  return lines;
}

function mapResult(sub: RankingResult): Candidate {
  const record = sub.parsed_data || {};
  const matchScore = Math.round(sub.final_score ?? 0);
  const isLowMatch = matchScore < 30;
  const penalties = sub.Penalties ?? sub.penalties ?? 0;
  const rawCareer = record.career_history;
  const careerHistory = Array.isArray(rawCareer)
    ? rawCareer.filter((item): item is Record<string, string> => !!item && typeof item === 'object')
    : [];
  const matched = asStringArray(sub.matched_skills);
  const missing = asStringArray(sub.missing_skills);
  const name = (record.full_name as string) || 'Unknown Candidate';
  const title = sub.title || (record.current_title as string) || 'Unknown Title';
  const company = (record.current_company as string) || 'Unknown Company';
  const years = record.total_years_of_experience as number | undefined;

  const narrative = isLowMatch
    ? `${name} scores below the shortlist threshold (${matchScore}%). Primary gaps: ${missing.slice(0, 3).join(', ') || 'role and skill fit'}.`
    : `${name} is a ${matchScore}% match for this role${years ? ` with ${years} years of experience` : ''}. Strong alignment on ${matched.slice(0, 4).join(', ') || 'core requirements'} at ${company}.`;

  return {
    id: sub.candidate_id,
    name,
    title,
    company,
    trajectory: careerHistory.map((c) => c.company || 'Unknown'),
    rank: sub.rank ?? 0,
    matchScore,
    isLowMatch,
    whyHere: isLowMatch ? ['Below shortlist threshold'] : ['Strong role and skill fit'],
    risks: isLowMatch
      ? [`Missing: ${missing.slice(0, 2).join(', ') || 'key requirements'}`]
      : penalties < 0 ? ['Minor profile inconsistencies'] : [],
    decisionPath: {
      enteredVia: 'Candidate pool',
      rankedBecause: isLowMatch
        ? []
        : [sub.explanation || `Ranked #${sub.rank ?? 0} with ${matchScore}% overall match.`],
      penalizedBecause: isLowMatch
        ? [`Match score ${matchScore}% is below the 30% shortlist bar.`]
        : penalties < 0 ? ['Profile consistency penalty applied'] : [],
    },
    evidence: {
      retrieval: [
        ...(sub.SemSim_Contrib ? [`Semantic Match: ${sub.SemSim_Contrib.toFixed(2)}`] : []),
        ...(sub.BM25_Contrib ? [`Keyword Match: ${sub.BM25_Contrib.toFixed(2)}`] : []),
      ],
      ranking: [
        `Experience Affinity: ${(sub.dimension_scores?.experience_affinity?.score ?? 0).toFixed(2)}`,
        `Skill Depth: ${(sub.dimension_scores?.skill_depth?.score ?? 0).toFixed(2)}`,
      ],
      recruiter: buildRecruiterSignals(record),
    },
    career: careerHistory.map((c) => ({
      role: c.title || 'Unknown',
      company: c.company || 'Unknown',
      year: parseInt(c.start_date?.split('-')[0] || '2020', 10),
    })),
    scores: {
      experience_affinity: sub.dimension_scores?.experience_affinity?.score ?? 0,
      skill_depth: sub.dimension_scores?.skill_depth?.score ?? 0,
      credential_affinity: sub.dimension_scores?.credential_affinity?.score ?? 0,
      availability_affinity: sub.dimension_scores?.availability_affinity?.score ?? 0,
      responsiveness_affinity: sub.dimension_scores?.responsiveness_affinity?.score ?? 0,
      trajectory_affinity: sub.dimension_scores?.trajectory_affinity?.score ?? 0,
      domain_authenticity: sub.dimension_scores?.domain_authenticity?.score ?? 0,
    },
    finalScores: {
      final: sub.final_score ?? 0,
      titleAffinity: sub.TitleAff_Contrib ?? 0,
      skillAffinity: sub.SkillAff_Contrib ?? 0,
      careerAffinity: sub.CareerAff_Contrib ?? 0,
      experienceAffinity: sub.dimension_scores?.experience_affinity?.score ?? 0,
      skillDepth: sub.dimension_scores?.skill_depth?.score ?? 0,
      domainAuthenticity: sub.dimension_scores?.domain_authenticity?.score ?? 0,
      quality: sub.Quality_Contrib ?? 0,
      penalties,
    },
    narrative,
    matched_skills: matched,
    missing_skills: missing,
    explanation: sub.explanation || 'No explanation provided.',
    adjacent_skills: asStringArray(sub.adjacent_skills),
    transferability_evidence: asStringArray(sub.transferability_evidence),
  };
}

export async function fetchDefaultJobId(): Promise<string | null> {
  const apiBase = getApiBase();
  try {
    const res = await fetch(`${apiBase}/jobs/default`, { cache: 'no-store' });
    if (!res.ok) return null;
    const job = await res.json();
    return job.id ?? null;
  } catch {
    return null;
  }
}

export async function fetchLatestJobId(): Promise<string | null> {
  const defaultJobId = await fetchDefaultJobId();
  if (defaultJobId) return defaultJobId;

  const apiBase = getApiBase();
  try {
    const res = await fetch(`${apiBase}/jobs/`, { cache: 'no-store' });
    if (!res.ok) return null;
    const jobs = await res.json();
    return jobs[0]?.id ?? null;
  } catch {
    return null;
  }
}

export async function fetchWorkspaceData(jobId: string): Promise<{
  status: string;
  candidates: Candidate[];
  metadata: {
    totalEvaluated: number;
    ranked: number;
    shortlisted: number;
    jdTitle: string;
  };
  error?: string;
}> {
  const apiBase = getApiBase();
  let res: Response;
  try {
    res = await fetch(`${apiBase}/rankings/${jobId}/latest`, { cache: 'no-store' });
  } catch {
    throw new Error('Cannot reach backend. Is the API running on port 8000?');
  }

  if (res.status === 404) {
    return {
      status: 'not_found',
      candidates: [],
      metadata: { totalEvaluated: 0, ranked: 0, shortlisted: 0, jdTitle: 'Unknown' },
      error: 'Investigation not found.',
    };
  }

  if (!res.ok) {
    throw new Error(`Failed to load ranking (${res.status})`);
  }

  const data = await res.json();

  if (data.status === 'failed') {
    return {
      status: 'failed',
      candidates: [],
      metadata: { totalEvaluated: 0, ranked: 0, shortlisted: 0, jdTitle: 'Unknown' },
      error: data.error || 'Ranking failed.',
    };
  }

  if (data.status !== 'completed') {
    return {
      status: data.status || 'pending',
      candidates: [],
      metadata: {
        totalEvaluated: data.total_candidates || 0,
        ranked: 0,
        shortlisted: 0,
        jdTitle: data.query_text || 'Processing…',
      },
    };
  }

  const rawResults = data.results;
  const results: RankingResult[] = Array.isArray(rawResults) ? rawResults : [];
  const candidates = results.map((result) => {
    try {
      return mapResult(result);
    } catch {
      return null;
    }
  }).filter((candidate): candidate is Candidate => candidate !== null);

  let jdTitle = data.query_text || 'Unknown Role';
  try {
    const jobRes = await fetch(`${apiBase}/jobs/${jobId}`, { cache: 'no-store' });
    if (jobRes.ok) {
      const job = await jobRes.json();
      if (job.title) jdTitle = job.title;
    }
  } catch {
    // keep query_text fallback
  }

  return {
    status: 'completed',
    candidates,
    metadata: {
      totalEvaluated: data.total_candidates || candidates.length,
      ranked: candidates.length,
      shortlisted: candidates.filter((c) => !c.isLowMatch).length,
      jdTitle,
    },
  };
}


export async function pollWorkspaceData(
  jobId: string,
  timeoutMs = 90_000,
  intervalMs = 2000,
): Promise<Awaited<ReturnType<typeof fetchWorkspaceData>>> {
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    const data = await fetchWorkspaceData(jobId);
    if (data.status === 'completed' && data.candidates.length > 0) return data;
    if (data.status === 'failed' || data.status === 'not_found') return data;
    await new Promise((r) => setTimeout(r, intervalMs));
  }

  throw new Error('Ranking is still processing. Try again in a moment or run a new investigation.');
}

/**
 * Fetch the Top-100 results from the 100k pipeline and map them into
 * the Candidate[] format expected by the workspace page.
 */
export async function fetch100kWorkspaceData(): Promise<{
  status: string;
  candidates: Candidate[];
  metadata: {
    totalEvaluated: number;
    ranked: number;
    shortlisted: number;
    jdTitle: string;
  };
}> {
  const apiBase = getApiBase();
  let res: Response;
  try {
    res = await fetch(`${apiBase}/pipeline/100k-results`, { cache: 'no-store' });
  } catch {
    throw new Error('Cannot reach backend. Is the API running on port 8000?');
  }

  if (!res.ok) {
    return {
      status: 'idle',
      candidates: [],
      metadata: { totalEvaluated: 0, ranked: 0, shortlisted: 0, jdTitle: '100k Pipeline' },
    };
  }

  const data = await res.json();

  if (data.status !== 'completed' || !data.results) {
    return {
      status: data.status || 'idle',
      candidates: [],
      metadata: { totalEvaluated: 0, ranked: 0, shortlisted: 0, jdTitle: '100k Pipeline' },
    };
  }

  const rawResults: any[] = data.results;
  const analytics = data.analytics || {};

  const candidates: Candidate[] = rawResults.map((r: any) => {
    const matchScore = Math.round(r.final_score ?? 0);
    const isLowMatch = matchScore < 30;
    const career = (r.career || []).map((c: any) => ({
      role: c.role || 'Unknown',
      company: c.company || 'Unknown',
      year: c.year || 2020,
    }));

    const matched = Array.isArray(r.matched_skills) ? r.matched_skills : [];
    const missing = Array.isArray(r.missing_skills) ? r.missing_skills : [];
    const feats = r.feature_scores || {};
    const reasoning = r.reasoning || r.explanation || 'No explanation available.';

    return {
      id: r.candidate_id,
      name: r.full_name || `Candidate ${r.rank}`,
      title: r.title || 'Unknown Title',
      company: (r.parsed_data?.redrob_signals as any)?.current_company || 'Unknown Company',
      trajectory: career.map((c: any) => c.company),
      rank: r.rank ?? 0,
      matchScore,
      isLowMatch,
      whyHere: isLowMatch ? ['Below shortlist threshold'] : ['100k Pipeline Top-100'],
      risks: isLowMatch ? [`Missing: ${missing.slice(0, 2).join(', ') || 'key requirements'}`] : [],
      decisionPath: {
        enteredVia: r.decisionPath?.enteredVia || '100k Pipeline',
        rankedBecause: r.decisionPath?.rankedBecause || [reasoning],
        penalizedBecause: r.decisionPath?.penalizedBecause || [],
      },
      evidence: {
        retrieval: [`Hybrid BM25 + Semantic Retrieval`],
        ranking: [
          `Title Match: ${feats.title_similarity ?? 0}%`,
          `Skill Coverage: ${feats.skill_coverage ?? 0}%`,
          `Seniority Alignment: ${feats.seniority_alignment ?? 0}%`,
          `Semantic Similarity: ${feats.semantic_sim ?? 0}%`,
        ],
        recruiter: [
          `Response Rate: ${Math.round((r.parsed_data?.redrob_signals as any)?.recruiter_response_rate * 100 || 0)}%`,
          `Notice Period: ${(r.parsed_data?.redrob_signals as any)?.notice_period_days || 30} days`,
        ],
      },
      career,
      scores: {
        experience_affinity: (feats.seniority_alignment ?? 0) / 100,
        skill_depth: (feats.skill_coverage ?? 0) / 100,
        credential_affinity: (feats.quality_score ?? 0) / 100,
        availability_affinity: 0,
        responsiveness_affinity: 0,
        trajectory_affinity: (feats.title_similarity ?? 0) / 100,
        domain_authenticity: Math.max(0, 1 - (feats.anti_skill_penalty ?? 0) / 100),
      },
      finalScores: {
        final: r.final_score ?? 0,
        titleAffinity: (feats.title_similarity ?? 0) / 100,
        skillAffinity: (feats.skill_coverage ?? 0) / 100,
        careerAffinity: (feats.seniority_alignment ?? 0) / 100,
        experienceAffinity: (feats.seniority_alignment ?? 0) / 100,
        skillDepth: (feats.skill_coverage ?? 0) / 100,
        domainAuthenticity: Math.max(0, 1 - (feats.anti_skill_penalty ?? 0) / 100),
        quality: (feats.quality_score ?? 0) / 100,
        penalties: -((feats.anti_skill_penalty ?? 0) + (feats.keyword_stuffing_risk ?? 0)) / 100,
      },
      narrative: reasoning,
      matched_skills: matched,
      missing_skills: missing,
      explanation: reasoning,
      adjacent_skills: [],
      transferability_evidence: [],
    };
  });

  return {
    status: 'completed',
    candidates,
    metadata: {
      totalEvaluated: analytics.totalEvaluated || rawResults.length,
      ranked: analytics.ranked || rawResults.length,
      shortlisted: analytics.shortlisted || candidates.filter(c => !c.isLowMatch).length,
      jdTitle: 'Senior Search Engineer — 100k Pipeline',
    },
  };
}

export async function trigger100kPipeline(): Promise<void> {
  const apiBase = getApiBase();
  try {
    await fetch(`${apiBase}/pipeline/run-100k`, { method: 'POST' });
  } catch (e) {
    console.error('Failed to start pipeline:', e);
  }
}

export async function getPipelineStatus(): Promise<{ status: string, progress: number, stage: string }> {
  const apiBase = getApiBase();
  try {
    const res = await fetch(`${apiBase}/pipeline/100k-status`);
    return await res.json();
  } catch (e) {
    return { status: "error", progress: 0, stage: "Error" };
  }
}

