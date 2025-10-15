import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'

export default function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen">
      <aside className="w-64 border-r bg-card">
        <div className="p-6">
          <h2 className="text-xl font-bold">WinGet Repo</h2>
        </div>
        <nav className="space-y-1 px-3">
          <Link
            to="/"
            className="block rounded-md px-3 py-2 text-sm font-medium hover:bg-muted"
          >
            Dashboard
          </Link>
          <Link
            to="/packages"
            className="block rounded-md px-3 py-2 text-sm font-medium hover:bg-muted"
          >
            Packages
          </Link>
        </nav>
      </aside>

      <div className="flex-1">
        <header className="border-b bg-card">
          <div className="flex h-16 items-center justify-between px-6">
            <div></div>
            <div className="flex items-center gap-4">
              <span className="text-sm">{user?.username}</span>
              <button
                onClick={handleLogout}
                className="rounded-md bg-secondary px-3 py-1 text-sm hover:bg-secondary/80"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        <main className="p-6">{children}</main>
      </div>
    </div>
  )
}
