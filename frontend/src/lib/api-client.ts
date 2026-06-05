const API_BASE = "http://localhost:8000/api"

export async function apiRequest<T = unknown>(
  endpoint: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: ["Bearer", token].join(" ") } : {}),
      ...options.headers,
    },
  })

  if (!res.ok) {
    const error = await res.text()
    throw new Error(error || `Request failed with status ${res.status}`)
  }

  return res.json() as Promise<T>
}
