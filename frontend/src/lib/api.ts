// All HTTP requests go through this module. No scattered fetch() in components/pages.

const API_BASE =
  (import.meta.env.VITE_API_URL as string | undefined) ?? '/api'

export class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, message: string, body: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

/**
 * Low-level fetch wrapper. Attaches bearer token, handles 401, throws ApiError on non-2xx.
 * Prefer the `api` object or `endpoints` over calling this directly.
 */
export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers: Record<string, string> = {
    ...(init.headers as Record<string, string> | undefined),
  }
  if (!(init.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }

  const url = path.startsWith('http') ? path : `${API_BASE}${path}`
  const response = await fetch(url, { ...init, headers })

  if (!response.ok) {
    let body: unknown = null
    let message = response.statusText
    try {
      body = await response.json()
      if (body && typeof body === 'object' && 'detail' in body) {
        message = String((body as { detail: unknown }).detail)
      }
    } catch {
      // body is not JSON — keep statusText as message
    }
    throw new ApiError(response.status, message, body)
  }

  // Treat 204 No Content as void
  if (response.status === 204) return undefined as unknown as T

  try {
    return (await response.json()) as T
  } catch {
    throw new ApiError(
      0,
      'Response was not JSON — check VITE_API_URL configuration',
      null,
    )
  }
}

/** Typed HTTP helpers. Use these (or the endpoints facade below) in pages/components. */
export const api = {
  get<T>(path: string): Promise<T> {
    return apiFetch<T>(path, { method: 'GET' })
  },

  post<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
    return apiFetch<T>(path, {
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    })
  },

  put<T>(path: string, body?: unknown): Promise<T> {
    return apiFetch<T>(path, {
      method: 'PUT',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  },

  patch<T>(path: string, body?: unknown): Promise<T> {
    return apiFetch<T>(path, {
      method: 'PATCH',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  },

  delete<T>(path: string): Promise<T> {
    return apiFetch<T>(path, { method: 'DELETE' })
  },

  upload<T>(path: string, formData: FormData): Promise<T> {
    return apiFetch<T>(path, { method: 'POST', body: formData })
  },
}

/**
 * Typed wrappers for every backend route.
 * Pages call endpoints.xxx() — never api.get('/path') directly.
 * Keep all API URLs here, not in components or routes.ts.
 */
export interface SyncStatus {
  last_synced_at: string | null
  last_sync_status: string | null
  sync_in_progress: boolean
  row_counts: Record<string, number>
}

export const endpoints = {
  chat: (message: string, signal?: AbortSignal) =>
    api.post<{ answer: string }>('/chat', { message }, signal),
  triggerSync: () => api.post<{ status: string }>('/sync'),
  syncStatus: () => api.get<SyncStatus>('/status'),
}
