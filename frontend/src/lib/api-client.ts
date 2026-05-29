const API_BASE = "http://localhost:8000/api"

export async function apiRequest<T = unknown>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const user = localStorage.getItem("signalhire_user")
  let token = ""
  if (user) {
    const parsed = JSON.parse(user)
    token = parsed.id
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
      ...options.headers,
    },
  })

  if (!res.ok) {
    const error = await res.text()
    throw new Error(error || `Request failed with status ${res.status}`)
  }

  return res.json() as Promise<T>
}