import { reactive } from 'vue'

export const session = reactive({ user: null, ready: false, error: '', csrf: '' })
let sessionRequest

export class ApiError extends Error {
  constructor(message, status, fields = {}) {
    super(message)
    this.status = status
    this.fields = fields
  }
}

export async function loadSession(force = false) {
  if (session.ready && !force) return session.user
  if (sessionRequest) return sessionRequest
  sessionRequest = (async () => {
    try {
      const data = await api('/session', { skipSession: true })
      session.user = data.user
      session.csrf = data.csrf_token
      session.ready = true
      session.error = ''
      return session.user
    } catch (error) {
      session.error = error.message
      throw error
    } finally {
      sessionRequest = null
    }
  })()
  return sessionRequest
}

export async function api(path, options = {}) {
  const { method = 'GET', body, skipSession = false } = options
  if (method !== 'GET' && !skipSession && !session.csrf) await loadSession(true)
  let response
  try {
    response = await fetch(`/api${path}`, {
      method,
      credentials: 'same-origin',
      headers: {
        Accept: 'application/json',
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(method !== 'GET' ? { 'X-CSRFToken': session.csrf } : {}),
      },
      ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
    })
  } catch {
    throw new ApiError('No pudimos conectar con JAGE. Revisa tu conexión e inténtalo otra vez.', 0)
  }
  const isJson = response.headers.get('content-type')?.includes('application/json')
  const data = isJson ? await response.json() : {}
  if (!response.ok) {
    if (response.status === 401) session.user = null
    if (String(data.code || '').startsWith('csrf_') || /csrf/i.test(data.error || '')) {
      session.csrf = ''
      if (!skipSession) await loadSession(true).catch(() => {})
      throw new ApiError(
        'Tu sesión de seguridad se renovó. Revisa los datos y vuelve a pulsar el botón.',
        response.status,
      )
    }
    throw new ApiError(
      data.error || 'No pudimos completar la operación. Inténtalo de nuevo.',
      response.status,
      data.fields,
    )
  }
  if (!isJson) throw new ApiError('El servicio no está disponible. Inténtalo más tarde.', 503)
  if (data.csrf_token) session.csrf = data.csrf_token
  return data
}

export function accountPath() {
  return session.user?.role === 'admin'
    ? '/administracion'
    : session.user?.role === 'driver'
      ? '/conductor'
      : '/mis-reservas'
}

export function operationKey() {
  return crypto.randomUUID()
}
