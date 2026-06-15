/** Resolve the backend API base URL, always ending with `/api`. */
export function getApiBase(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const base = raw.replace(/\/$/, '');
  return base.endsWith('/api') ? base : `${base}/api`;
}
