export function useApi() {
  const config = useRuntimeConfig()
  const base = config.public.apiBase

  async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const token = localStorage.getItem('token')
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    }
    if (token) headers['Authorization'] = `Bearer ${token}`

    const res = await fetch(`${base}${path}`, { ...options, headers })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(typeof err.detail === 'string' ? err.detail : JSON.stringify(err.detail))
    }
    if (res.status === 204) return undefined as T
    return res.json()
  }

  return {
    get: <T>(path: string) => request<T>(path),
    post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
    put: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
    delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),

    uploadFile: async <T>(path: string, formData: FormData, onProgress?: (pct: number) => void): Promise<T> => {
      return new Promise((resolve, reject) => {
        const token = localStorage.getItem('token')
        const xhr = new XMLHttpRequest()
        xhr.open('POST', `${base}${path}`)
        if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
        if (onProgress) {
          xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100))
          }
        }
        xhr.timeout = 120000
        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              resolve(xhr.responseText ? JSON.parse(xhr.responseText) : (undefined as T))
            } catch {
              reject(new Error('Upload completed but response could not be parsed'))
            }
          } else {
            try {
              const detail = JSON.parse(xhr.responseText).detail
              reject(new Error(typeof detail === 'string' ? detail : JSON.stringify(detail)))
            } catch {
              reject(new Error('Upload failed'))
            }
          }
        }
        xhr.onerror = () => reject(new Error('Network error'))
        xhr.onabort = () => reject(new Error('Upload cancelled'))
        xhr.ontimeout = () => reject(new Error('Upload timed out while waiting for server response'))
        xhr.send(formData)
      })
    },
  }
}
