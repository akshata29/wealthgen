// Advisor sign-in control shown in the top bar. Registers the delegated Search
// token provider (used for OBO grounding) once a user is authenticated.
import { useEffect } from 'react'
import { useMsal, useIsAuthenticated } from '@azure/msal-react'
import { InteractionRequiredAuthError } from '@azure/msal-browser'
import { LogIn, LogOut, UserCircle2 } from 'lucide-react'
import { loginRequest, searchRequest } from '@/auth/msalConfig'
import { setSearchTokenProvider } from '@/auth/authToken'

export default function AuthButton() {
  const { instance, accounts } = useMsal()
  const isAuthenticated = useIsAuthenticated()
  const account = accounts[0]

  // Register a provider that silently acquires the delegated Search token.
  useEffect(() => {
    if (!isAuthenticated || !account) {
      setSearchTokenProvider(null)
      return
    }
    setSearchTokenProvider(async () => {
      try {
        const res = await instance.acquireTokenSilent({ ...searchRequest, account })
        return res.accessToken
      } catch (err) {
        if (err instanceof InteractionRequiredAuthError) {
          const res = await instance.acquireTokenPopup(searchRequest)
          return res.accessToken
        }
        throw err
      }
    })
    return () => setSearchTokenProvider(null)
  }, [instance, account, isAuthenticated])

  const signIn = async () => {
    const res = await instance.loginPopup(loginRequest)
    instance.setActiveAccount(res.account)
  }

  const signOut = () => instance.logoutPopup({ account })

  if (!isAuthenticated) {
    return (
      <button onClick={signIn} className="btn-primary flex items-center gap-2 text-xs px-3 py-1.5">
        <LogIn className="w-3.5 h-3.5" />
        Sign in
      </button>
    )
  }

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-1.5 bg-surface-50 border border-border rounded-full px-3 py-1">
        <UserCircle2 className="w-4 h-4 text-accent" />
        <span className="text-xs text-gray-300 max-w-[180px] truncate">
          {account?.name ?? account?.username}
        </span>
      </div>
      <button
        onClick={signOut}
        title="Sign out"
        className="text-gray-400 hover:text-gray-100 p-1.5 rounded-md hover:bg-surface-50"
      >
        <LogOut className="w-4 h-4" />
      </button>
    </div>
  )
}
