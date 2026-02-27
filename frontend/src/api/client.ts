const BASE = '/api'

interface ApiResponse<T> {
  data: T
  code: number
  message: string
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options)
  const json: ApiResponse<T> = await res.json()
  if (json.code !== 200) {
    throw new Error(json.message ?? `API error ${json.code}`)
  }
  return json.data
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}
