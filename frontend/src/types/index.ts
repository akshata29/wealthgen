// Shared API types.
export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

export type AsyncState<T> =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'success'; data: T }
  | { status: 'error'; error: string }
