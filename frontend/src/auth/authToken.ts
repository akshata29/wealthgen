// Bridges MSAL token acquisition to the (non-React) API client.
// The AuthButton registers a provider once the user is signed in; the API client
// calls getSearchToken() before requests that need OBO grounding.
type TokenProvider = () => Promise<string | null>

let provider: TokenProvider | null = null

export function setSearchTokenProvider(fn: TokenProvider | null): void {
  provider = fn
}

export async function getSearchToken(): Promise<string | null> {
  if (!provider) return null
  try {
    return await provider()
  } catch {
    return null
  }
}
