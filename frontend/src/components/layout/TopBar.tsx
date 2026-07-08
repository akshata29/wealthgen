import { useLocation } from 'react-router-dom'
import AuthButton from '@/auth/AuthButton'

const TITLES: Record<string, string> = {
  '/': 'Generate Commentary',
  '/generate': 'Generate Commentary',
  '/review': 'Review & Approve',
  '/workflow': 'Workflow',
  '/architecture': 'Architecture',
  '/demo': 'Demo Flow',
  '/settings': 'Settings',
}

export default function TopBar() {
  const { pathname } = useLocation()
  const base = '/' + pathname.split('/')[1]
  const title = TITLES[base] ?? 'WealthGen'

  return (
    <header className="h-16 flex items-center justify-between px-6 bg-surface-100 border-b border-border shrink-0">
      <div className="flex items-center gap-3">
        <h1 className="text-base font-semibold text-gray-100">{title}</h1>
        <span className="badge-gold">Foundry IQ · Grounded</span>
      </div>
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 bg-surface-50 border border-border rounded-full px-3 py-1">
          <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
          <span className="text-xs text-gray-400">Agents online</span>
        </div>
        <AuthButton />
      </div>
    </header>
  )
}
