import { create } from "zustand";

export interface CareerStep {
  role: string;
  company: string;
  year: number;
}

export interface DecisionPath {
  enteredVia: string;
  rankedBecause: string[];
  penalizedBecause: string[];
}

export interface Evidence {
  retrieval: string[];
  ranking: string[];
  recruiter: string[];
}

export interface Scores {
  experience_affinity: number;
  skill_depth: number;
  credential_affinity: number;
  availability_affinity: number;
  responsiveness_affinity: number;
  trajectory_affinity: number;
  domain_authenticity: number;
}

export interface FinalScores {
  final: number;
  titleAffinity: number;
  skillAffinity: number;
  careerAffinity: number;
  experienceAffinity: number;
  skillDepth: number;
  domainAuthenticity: number;
  quality: number;
  penalties: number;
}

export interface WhyNotRanked {
  missing: string[];
  weak: string[];
  strong: string[];
  wouldImprove: string[];
}

export interface Candidate {
  id: string;
  name: string;
  title: string;
  company: string;
  trajectory: string[];
  rank: number;
  matchScore: number;
  whyHere: string[];
  risks: string[];
  decisionPath: DecisionPath;
  evidence: Evidence;
  career: CareerStep[];
  scores: Scores;
  finalScores: FinalScores;
  narrative: string;
  whyNotRanked?: WhyNotRanked;
}

export interface WorkspaceState {
  candidates: Candidate[];
  rejectedCandidates: Candidate[];
  shortlist: Candidate[];
  selectedCandidate: Candidate | null;
  comparisonCandidate: Candidate | null;
  isLoaded: boolean;
  isProcessing: boolean;
  rankingMetadata: any;
  setCandidates: (candidates: Candidate[]) => void;
  setSelectedCandidate: (candidate: Candidate | null) => void;
  setComparisonCandidate: (candidate: Candidate | null) => void;
  setRankingMetadata: (meta: any) => void;
  clearComparison: () => void;
  setIsLoaded: (loaded: boolean) => void;
  setIsProcessing: (processing: boolean) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  candidates: [],
  rejectedCandidates: [],
  shortlist: [],
  selectedCandidate: null,
  comparisonCandidate: null,
  isLoaded: false,
  isProcessing: false,
  rankingMetadata: null,

  setCandidates: (candidates) => set({ 
    candidates,
    shortlist: candidates.filter(c => c.rank <= 100),
    rejectedCandidates: candidates.filter(c => c.rank > 100)
  }),
  setSelectedCandidate: (candidate) => set({ selectedCandidate: candidate }),
  setComparisonCandidate: (candidate) => set({ comparisonCandidate: candidate }),
  setRankingMetadata: (rankingMetadata) => set({ rankingMetadata }),
  clearComparison: () => set({ comparisonCandidate: null }),
  setIsLoaded: (isLoaded) => set({ isLoaded }),
  setIsProcessing: (isProcessing) => set({ isProcessing }),
}));
