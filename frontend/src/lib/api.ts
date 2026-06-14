'use server';

import type { Candidate, CareerStep } from '../store/workspace';

function mapToUICandidate(sub: any, record: any): Candidate {
  const technicalScore = Math.round((sub?.final_score ?? 0) * 10);
  const matchScore = technicalScore;
  const isRejected = matchScore < 30; // Reject if score is too low
  
  // Extract career trajectory
  const career: CareerStep[] = (record?.career_history || []).map((c: any) => ({
    role: c.title || 'Unknown',
    company: c.company || 'Unknown',
    year: parseInt(c.start_date?.split('-')[0] || '2020', 10),
  }));

  const trajectory = career.map((c: any) => c.company);

  // Evidence Parsing based on actual reasoning
  const retrievalEvidence = [];
  const rankingEvidence = [];
  
  if ((sub?.SemSim_Contrib ?? 0) > 0) {
    retrievalEvidence.push(`Semantic Match: ${(sub?.SemSim_Contrib ?? 0).toFixed(2)}`);
  }
  if ((sub?.BM25_Contrib ?? 0) > 0) {
    retrievalEvidence.push(`Keyword Match: ${(sub?.BM25_Contrib ?? 0).toFixed(2)}`);
  }

  rankingEvidence.push(`Experience Affinity: ${(sub?.dimension_scores?.experience_affinity?.score ?? 0).toFixed(2)}`);
  rankingEvidence.push(`Skill Depth: ${(sub?.dimension_scores?.skill_depth?.score ?? 0).toFixed(2)}`);

  const penalties = sub?.Penalties ?? sub?.penalties ?? 0;

  return {
    id: sub.candidate_id,
    name: record?.profile?.anonymized_name || "Unknown Candidate",
    title: sub.title || record?.profile?.current_title || "Unknown Title",
    company: record?.profile?.current_company || "Unknown Company",
    trajectory,
    rank: isRejected ? 101 + sub.rank : sub.rank, // Force rank > 100 if rejected
    matchScore: matchScore,
    whyHere: isRejected ? ["Low Match Score"] : ["Domain Affinity"],
    risks: penalties < 0 ? ["Inconsistent Profile"] : [],
    decisionPath: {
      enteredVia: "Exhaustive Pipeline",
      rankedBecause: sub?.explanation?.top_strengths || ["Met requirement threshold"],
      penalizedBecause: penalties < 0 ? ["Inconsistency Detected"] : [],
    },
    evidence: {
      retrieval: retrievalEvidence,
      ranking: rankingEvidence,
      recruiter: [
        `Response Rate: ${(record?.redrob_signals?.recruiter_response_rate || 0) * 100}%`,
        `Notice Period: ${record?.redrob_signals?.notice_period_days || 30} days`,
      ],
    },
    career,
    scores: {
      experience_affinity: sub?.dimension_scores?.experience_affinity?.score ?? 0,
      skill_depth: sub?.dimension_scores?.skill_depth?.score ?? 0,
      credential_affinity: sub?.dimension_scores?.credential_affinity?.score ?? 0,
      availability_affinity: sub?.dimension_scores?.availability_affinity?.score ?? 0,
      responsiveness_affinity: sub?.dimension_scores?.responsiveness_affinity?.score ?? 0,
      trajectory_affinity: sub?.dimension_scores?.trajectory_affinity?.score ?? 0,
      domain_authenticity: sub?.dimension_scores?.domain_authenticity?.score ?? 0,
    },
    finalScores: {
      final: sub?.final_score ?? 0,
      titleAffinity: 0,
      skillAffinity: 0,
      careerAffinity: 0,
      experienceAffinity: sub?.dimension_scores?.experience_affinity?.score ?? 0,
      skillDepth: sub?.dimension_scores?.skill_depth?.score ?? 0,
      domainAuthenticity: sub?.dimension_scores?.domain_authenticity?.score ?? 0,
      quality: 0,
      penalties: sub?.penalties ?? 0
    },
    narrative: `Final Score: ${(sub?.final_score ?? 0).toFixed(2)}\nTitle Affinity: ${(sub?.TitleAff_Contrib ?? 0).toFixed(2)}\nSkill Affinity: ${(sub?.SkillAff_Contrib ?? 0).toFixed(2)}\nCareer Affinity: ${(sub?.CareerAff_Contrib ?? 0).toFixed(2)}\nPenalties: ${(sub?.Penalties ?? 0).toFixed(2)}`,
  };
}

export async function getCombinedShortlist(jobId?: string): Promise<Candidate[]> {
  if (!jobId) {
    return [];
  } else {
    const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    if (!UUID_REGEX.test(jobId)) {
      throw new Error("Invalid investigation id");
    }
  }

  const url = new URL(`/api/rankings/${jobId}/latest`, 'http://localhost:8000');
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error("Failed to fetch results");
  }
  const data = await res.json();
  if (data.status !== 'completed') {
    return [];
  }
  const results = data.results || [];

  return results.map((sub: any) => {
    return mapToUICandidate(sub, sub.parsed_data); 
  });
}

export async function getRankingMetadata(jobId?: string) {
  if (!jobId) {
    return {
      totalEvaluated: 0,
      retrieved: 0,
      ranked: 0,
      shortlisted: 0,
      featuresExtracted: 22,
      model: "Exhaustive V2 Ranking Engine",
      jdTitle: "Unknown",
      skills: {} as Record<string, number>,
      signals: [] as Array<{name: string, count: number, avgRank: number, avgScore: number}>,
      rejections: []
    };
  } else {
    const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    if (!UUID_REGEX.test(jobId)) {
      throw new Error("Invalid investigation id");
    }
  }

  const url = new URL(`/api/rankings/${jobId}/latest`, 'http://localhost:8000');
  const res = await fetch(url, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error("Failed to fetch metadata");
  }
  const data = await res.json();
  const results = data.results || [];
  
  return {
      totalEvaluated: data.total_candidates || 0,
      retrieved: data.total_candidates || 0,
      ranked: results.length,
      shortlisted: results.filter((r: any) => (r.rank || 0) <= 100).length,
      featuresExtracted: 22,
      model: "Exhaustive V2 Ranking Engine",
      jdTitle: data.query_text || "Unknown Role",
      skills: {} as Record<string, number>,
      signals: [] as Array<{name: string, count: number, avgRank: number, avgScore: number}>,
      rejections: [
        { reason: "Lacks Domain Authenticity", count: results.filter((r: any) => r.dimension_scores?.domain_authenticity?.score < 50).length },
        { reason: "Missing Hard Skills", count: results.filter((r: any) => r.dimension_scores?.skill_depth?.score < 30).length },
        { reason: "Trajectory Mismatch", count: results.filter((r: any) => r.final_score < 40).length }
      ]
  };
}

export async function getLandingPageData() {
  return {
    trap: null as any,
    elite: null as any
  };
}
