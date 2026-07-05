const BROWSER_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
const SERVER_URL = process.env.API_URL || 'http://backend:8000/api/v1'
const API_URL = typeof window === 'undefined' ? SERVER_URL : BROWSER_URL

class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function handleResponse(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(body.detail || res.statusText, res.status)
  }
  return res.json()
}

async function refreshToken(): Promise<string | null> {
  try {
    const res = await fetch(`${API_URL}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    })
    if (!res.ok) return null
    const data = await res.json()
    return data.access_token
  } catch {
    return null
  }
}

async function request<T>(
  method: string,
  path: string,
  body?: any,
  opts?: { formData?: boolean; headers?: Record<string, string> }
): Promise<T> {
  const headers: Record<string, string> = { ...opts?.headers }
  if (!opts?.formData) {
    headers['Content-Type'] = 'application/json'
  }

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: opts?.formData ? body : body ? JSON.stringify(body) : undefined,
    credentials: 'include',
  })

  if (res.status === 401) {
    const newToken = await refreshToken()
    if (newToken) {
      headers['Authorization'] = `Bearer ${newToken}`
      const retryHeaders = { ...opts?.headers, ...headers }
      const retryRes = await fetch(`${API_URL}${path}`, {
        method,
        headers: retryHeaders,
        body: opts?.formData ? body : body ? JSON.stringify(body) : undefined,
        credentials: 'include',
      })
      return handleResponse(retryRes)
    }
    throw new ApiError('Unauthorized', 401)
  }

  return handleResponse(res)
}

export const api = {
  get: <T>(path: string, params?: Record<string, any>) => {
    const qs = params ? '?' + new URLSearchParams(
      Object.entries(params).filter(([_, v]) => v !== undefined && v !== '').map(([k, v]) => [k, String(v)])
    ).toString() : ''
    return request<T>('GET', `${path}${qs}`)
  },

  post: <T>(path: string, body?: any) => request<T>('POST', path, body),

  patch: <T>(path: string, body?: any) => request<T>('PATCH', path, body),

  del: <T>(path: string) => request<T>('DELETE', path),

  postForm: <T>(path: string, formData: FormData, opts?: { headers?: Record<string, string> }) =>
    request<T>('POST', path, formData, { formData: true, ...opts }),

  patchForm: <T>(path: string, formData: FormData) =>
    request<T>('PATCH', path, formData, { formData: true }),
}
