const POLL_INTERVAL_MS = 1500;

type TaskStatus = {
  status: string;
  error?: string | null;
  result?: { error?: string; parsed?: boolean } | null;
};

type JobCandidatesStatus = {
  ready: boolean;
  ready_count: number;
  total: number;
  processing_count: number;
  failed_count: number;
  failures: Array<{ candidate_id: string; error: string }>;
};

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = (err as { detail?: string }).detail;
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export async function waitForTasks(
  apiBase: string,
  taskIds: string[],
  timeoutMs = 120_000,
): Promise<void> {
  if (taskIds.length === 0) return;

  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    const statuses: TaskStatus[] = await Promise.all(
      taskIds.map(async (id) => {
        const res = await fetch(`${apiBase}/tasks/${id}`);
        if (!res.ok) return { status: 'pending' };
        return res.json();
      }),
    );

    const allDone = statuses.every(
      (s) => s.status === 'completed' || s.status === 'failed',
    );

    if (allDone) {
      const failed = statuses.filter((s) => s.status === 'failed');
      const parseErrors = statuses.filter(
        (s) => s.status === 'completed' && s.result?.error,
      );

      if (failed.length > 0 || parseErrors.length > 0) {
        const message = [
          ...failed.map((s) => s.error),
          ...parseErrors.map((s) => s.result?.error),
        ]
          .filter(Boolean)
          .join('; ');
        throw new Error(message || `Resume parsing failed for ${failed.length + parseErrors.length} file(s)`);
      }
      return;
    }

    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
  }

  throw new Error('Resume parsing timed out. Please try again.');
}

export async function waitForJobCandidates(
  apiBase: string,
  jobId: string,
  timeoutMs = 30_000,
): Promise<JobCandidatesStatus> {
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    const status = await fetchJson<JobCandidatesStatus>(
      `${apiBase}/jobs/${jobId}/candidates-status`,
    );

    if (status.failed_count > 0 && status.ready_count === 0) {
      const message = status.failures
        .map((f) => f.error)
        .filter(Boolean)
        .join('; ');
      throw new Error(message || 'Resume parsing failed.');
    }

    if (status.ready) {
      return status;
    }

    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
  }

  throw new Error(
    'Resumes are still processing. Please wait a moment and try again.',
  );
}

export async function startRanking(
  apiBase: string,
  jobId: string,
): Promise<void> {
  const rankUrl = `${apiBase}/rankings/${jobId}`;
  const rankRes = await fetch(rankUrl, { method: 'POST' });

  if (rankRes.ok) return;

  const err = await rankRes.json().catch(() => ({}));
  const detail =
    typeof (err as { detail?: string }).detail === 'string'
      ? (err as { detail: string }).detail
      : 'Failed to start ranking';

  throw new Error(detail);
}

export async function waitForRankingComplete(
  apiBase: string,
  jobId: string,
  timeoutMs = 120_000,
): Promise<void> {
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    const res = await fetch(`${apiBase}/rankings/${jobId}/latest`, {
      cache: 'no-store',
    });
    if (res.ok) {
      const data = await res.json();
      if (data.status === 'completed') return;
      if (data.status === 'failed') {
        throw new Error(data.error || 'Ranking failed');
      }
    }
    await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));
  }

  throw new Error('Ranking timed out. Please try again.');
}

export async function runHackathonDemo(apiBase: string): Promise<{
  job_id: string;
  task_ids: string[];
  resume_count: number;
}> {
  const res = await fetch(`${apiBase}/jobs/hackathon-demo`, { method: 'POST' });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(
      (err as { detail?: string }).detail || 'Failed to load hackathon demo data',
    );
  }
  return res.json();
}
