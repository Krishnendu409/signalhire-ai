'use server';

import { loadTop100, loadRejectedCases, loadCandidates, loadCandidateById } from './repository';
import type { Candidate, CareerStep } from '../store/workspace';

function mapToUICandidate(sub: any, record: any): Candidate {
  const isRejected = sub.rank > 100;
  
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
  
  if (sub.SemSim_Contrib > 0) {
    retrievalEvidence.push(`Semantic Match: ${sub.SemSim_Contrib.toFixed(2)}`);
  }
  if (sub.BM25_Contrib > 0) {
    retrievalEvidence.push(`Keyword Match: ${sub.BM25_Contrib.toFixed(2)}`);
  }

  rankingEvidence.push(`Skill Affinity: ${sub.SkillAff_Contrib.toFixed(2)}`);
  rankingEvidence.push(`Career Affinity: ${sub.CareerAff_Contrib.toFixed(2)}`);

  const technicalScore = Math.round(sub.final_score * 10);
  const matchScore = technicalScore;

  return {
    id: sub.candidate_id,
    name: record?.profile?.anonymized_name || "Unknown Candidate",
    title: sub.title || record?.profile?.current_title || "Unknown Title",
    company: record?.profile?.current_company || "Unknown Company",
    trajectory,
    rank: sub.rank,
    matchScore: matchScore,
    whyHere: isRejected ? ["Keyword Match"] : ["Domain Affinity"],
    risks: sub.Penalties < 0 ? ["Inconsistent Profile"] : [],
    decisionPath: {
      enteredVia: "Domain Affinity Heuristic",
      rankedBecause: [],
      penalizedBecause: sub.Penalties < 0 ? ["Domain Contradiction Detected"] : [],
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
      technical: technicalScore,
      production: sub.CareerAff_Contrib * 10,
      leadership: 50,
      evaluation: sub.Quality_Contrib * 10,
      hireability: (record?.redrob_signals?.recruiter_response_rate || 0) * 100,
    },
    finalScores: {
      final: sub.final_score,
      titleAffinity: sub.TitleAff_Contrib,
      skillAffinity: sub.SkillAff_Contrib,
      careerAffinity: sub.CareerAff_Contrib,
      semantic: sub.SemSim_Contrib,
      bm25: sub.BM25_Contrib,
      quality: sub.Quality_Contrib,
      penalties: sub.Penalties
    },
    narrative: `Final Score: ${sub.final_score.toFixed(2)}\nTitle Affinity: ${sub.TitleAff_Contrib.toFixed(2)}\nSkill Affinity: ${sub.SkillAff_Contrib.toFixed(2)}\nCareer Affinity: ${sub.CareerAff_Contrib.toFixed(2)}\nPenalties: ${sub.Penalties.toFixed(2)}`,
  };
}

export async function getCombinedShortlist(invId?: string): Promise<Candidate[]> {
  if (!invId) {
    // Fallback if no invId is provided
    const top100 = await loadTop100();
    const rejected = await loadRejectedCases();
    const allCases = [...top100.slice(0, 50), ...rejected];
    return allCases.map(c => {
      const sub = c.submission;
      // Mock fastAPI format for fallback
      return mapToUICandidate({
        candidate_id: sub.candidate_id,
        rank: sub.rank,
        title: c.record?.profile?.current_title,
        final_score: sub.score || 0,
        TitleAff_Contrib: 0,
        SkillAff_Contrib: 0,
        CareerAff_Contrib: 0,
        SemSim_Contrib: 0,
        BM25_Contrib: 0,
        Quality_Contrib: 0,
        Penalties: 0
      }, c.record);
    });
  }

  const res = await fetch(`http://localhost:8000/api/investigations/${invId}/results`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error("Failed to fetch results");
  }
  const data = await res.json();
  const results = data.results;

  const allCandidates = await loadCandidates();
  const candMap = new Map();
  for (const c of allCandidates) {
    candMap.set(c.candidate_id, c);
  }

  return results.map((sub: any) => {
    const record = candMap.get(sub.candidate_id);
    return mapToUICandidate(sub, record);
  });
}

export async function getRankingMetadata() {
  return {
    totalEvaluated: 100000,
    retrieved: 5000,
    ranked: 1000,
    shortlisted: 100,
    featuresExtracted: 22,
    model: "LightGBM LambdaRank",
    skills: {
      "Search Engineers": 51,
      "NLP Engineers": 24,
      "Applied ML Engineers": 12,
      "Recommendation Engineers": 8,
      "Other": 5
    },
    signals: [
      { name: "FAISS", count: 41, avgRank: 12, avgScore: 92 },
      { name: "Qdrant", count: 28, avgRank: 24, avgScore: 88 },
      { name: "Learning-to-Rank", count: 17, avgRank: 8, avgScore: 95 }
    ],
    rejections: [
      { reason: "Missing Retrieval Experience", count: 450 },
      { reason: "Weak Production Evidence", count: 320 },
      { reason: "Keyword Trap", count: 85 },
      { reason: "Timeline Inconsistency", count: 45 }
    ]
  };
}

export async function getLandingPageData() {
  const rejected = await loadRejectedCases();
  const top100 = await loadTop100();
  
  const trapCandidate = rejected[0]; // keyword trap
  const eliteCandidate = top100[0]; // rank 1

  return {
    trap: mapToUICandidate(trapCandidate.submission, trapCandidate.record),
    elite: mapToUICandidate(eliteCandidate.submission, eliteCandidate.record)
  };
}
