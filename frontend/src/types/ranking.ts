export interface SubmissionRow {
  candidate_id: string;
  rank: number;
  score: number;
  reasoning: string;
}

export interface CandidateProfile {
  anonymized_name?: string;
  headline?: string;
  summary?: string;
  current_title?: string;
  current_company?: string;
  years_of_experience?: number;
}

export interface CandidateSkill {
  name: string;
  proficiency: string;
  duration_months?: number;
}

export interface CareerHistoryItem {
  company: string;
  title: string;
  start_date: string;
  end_date: string | null;
  duration_months: number;
  description?: string;
}

export interface CandidateRecord {
  candidate_id: string;
  profile?: CandidateProfile;
  skills?: CandidateSkill[];
  career_history?: CareerHistoryItem[];
  redrob_signals?: {
    recruiter_response_rate?: number;
    notice_period_days?: number;
  };
}

export interface DemoCases {
  keywordTrap: string;
  secondaryTrap: string;
  eliteCandidate: string;
}
