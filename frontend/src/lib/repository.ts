'use server';

import fs from 'fs';
import path from 'path';
import { SubmissionRow, CandidateRecord } from '../types/ranking';

const ROOT_DIR = path.resolve(process.cwd(), '..');
const SUBMISSION_PATH = path.join(ROOT_DIR, 'submission.csv');
const CANDIDATES_PATH = path.join(ROOT_DIR, '[PUB] India_runs_data_and_ai_challenge', 'India_runs_data_and_ai_challenge', 'candidates.jsonl');
const DEMO_CASES_PATH = path.join(process.cwd(), 'src/lib/demo_cases.json');

function parseCSV(content: string): SubmissionRow[] {
  const lines = content.trim().split('\n');
  const rows: SubmissionRow[] = [];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim()) continue;
    
    const parts = line.split(',');
    const candidate_id = parts[0];
    const rank = parseInt(parts[1], 10);
    const score = parseFloat(parts[2]);
    
    let reasoning = parts.slice(3).join(',');
    if (reasoning.startsWith('"') && reasoning.endsWith('"')) {
      reasoning = reasoning.slice(1, -1);
    }
    
    rows.push({ candidate_id, rank, score, reasoning });
  }
  return rows;
}

export async function loadSubmission(): Promise<SubmissionRow[]> {
  const content = await fs.promises.readFile(SUBMISSION_PATH, 'utf-8');
  return parseCSV(content);
}

export async function loadCandidates(ids?: string[]): Promise<CandidateRecord[]> {
  const content = await fs.promises.readFile(CANDIDATES_PATH, 'utf-8');
  const lines = content.trim().split('\n');
  const records: CandidateRecord[] = [];
  
  const idSet = ids ? new Set(ids) : null;
  
  for (const line of lines) {
    if (!line.trim()) continue;
    try {
      const cand: CandidateRecord = JSON.parse(line);
      if (!idSet || idSet.has(cand.candidate_id)) {
        records.push(cand);
      }
    } catch (e) {
      // ignore malformed lines
    }
  }
  return records;
}

export async function loadCandidateById(id: string): Promise<CandidateRecord | null> {
  const cands = await loadCandidates([id]);
  return cands.length > 0 ? cands[0] : null;
}

export async function loadTop100(): Promise<{ submission: SubmissionRow; record: CandidateRecord | null }[]> {
  const submission = await loadSubmission();
  const topIds = submission.map((s) => s.candidate_id);
  const records = await loadCandidates(topIds);
  
  const recordMap = new Map(records.map((r) => [r.candidate_id, r]));
  
  return submission.map((sub) => ({
    submission: sub,
    record: recordMap.get(sub.candidate_id) || null,
  }));
}

export async function loadRejectedCases(): Promise<{ submission: SubmissionRow; record: CandidateRecord | null }[]> {
  const demoCases = JSON.parse(await fs.promises.readFile(DEMO_CASES_PATH, 'utf-8'));
  const ids = [demoCases.keywordTrap, demoCases.secondaryTrap];
  const records = await loadCandidates(ids);
  
  return records.map((record, idx) => ({
    submission: {
      candidate_id: record.candidate_id,
      rank: 300 + idx, // Unranked
      score: idx === 0 ? 0.31 : 0.18, 
      reasoning: "Keyword matched but failed infrastructure extraction."
    },
    record
  }));
}
