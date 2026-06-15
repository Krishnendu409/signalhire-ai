export type RankingLatestResponse = {
  status: string;
  results?: Array<Record<string, unknown>>;
  total_candidates?: number;
  query_text?: string;
  message?: string;
  error?: string;
};

const DEFAULT_METADATA = {
  totalEvaluated: 0,
  retrieved: 0,
  ranked: 0,
  shortlisted: 0,
  featuresExtracted: 22,
  model: "Exhaustive V2 Ranking Engine",
  jdTitle: "Unknown",
  skills: {} as Record<string, number>,
  signals: [] as Array<{ name: string; count: number; avgRank: number; avgScore: number }>,
  rejections: [] as Array<{ reason: string; count: number }>,
};

export async function fetchLatestRanking(
  jobId: string,
  apiBase: string,
): Promise<RankingLatestResponse | null> {
  const url = new URL(`/rankings/${jobId}/latest`, apiBase);
  let res: Response;
  try {
    res = await fetch(url, { cache: 'no-store' });
  } catch {
    return null;
  }

  if (res.status === 404) {
    return { status: 'not_found', message: 'Job not found' };
  }

  if (!res.ok) {
    return null;
  }

  return res.json();
}

export function buildRankingMetadata(data: RankingLatestResponse) {
  const results = data.results || [];
  return {
    totalEvaluated: data.total_candidates || 0,
    retrieved: data.total_candidates || 0,
    ranked: results.length,
    shortlisted: results.filter((r) => ((r.rank as number) || 0) <= 100).length,
    featuresExtracted: 22,
    model: "Exhaustive V2 Ranking Engine",
    jdTitle: data.query_text || "Unknown Role",
    skills: {} as Record<string, number>,
    signals: [] as Array<{ name: string; count: number; avgRank: number; avgScore: number }>,
    rejections: [
      {
        reason: "Lacks Domain Authenticity",
        count: results.filter(
          (r) =>
            (r.dimension_scores as { domain_authenticity?: { score?: number } })
              ?.domain_authenticity?.score != null &&
            ((r.dimension_scores as { domain_authenticity?: { score?: number } })
              .domain_authenticity?.score as number) < 50,
        ).length,
      },
      {
        reason: "Missing Hard Skills",
        count: results.filter(
          (r) =>
            (r.dimension_scores as { skill_depth?: { score?: number } })?.skill_depth
              ?.score != null &&
            ((r.dimension_scores as { skill_depth?: { score?: number } }).skill_depth
              ?.score as number) < 30,
        ).length,
      },
      {
        reason: "Trajectory Mismatch",
        count: results.filter((r) => ((r.final_score as number) || 0) < 40).length,
      },
    ],
  };
}

export { DEFAULT_METADATA };
