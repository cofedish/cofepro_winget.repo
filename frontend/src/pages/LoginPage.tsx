import { useState } from 'react'
import { useAuth } from '../lib/auth'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(username, password)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Ошибка входа')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 dark:bg-gray-900">
      <div className="w-full max-w-md space-y-8 rounded-lg bg-white p-8 shadow-lg dark:bg-gray-800">
        <div className="text-center">
          <h1 className="text-3xl font-bold">Приватный репозиторий WinGet</h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">Войдите, чтобы продолжить</p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          {error && (
            <div className="rounded bg-red-50 p-3 text-sm text-red-600 dark:bg-red-900/20">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="username" className="block text-sm font-medium">
              Имя пользователя
            </label>
            <input
              id="username"
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1 block w-full rounded-md border px-3 py-2 focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium">
              Пароль
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full rounded-md border px-3 py-2 focus:border-blue-500 focus:outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Вход...' : 'Войти'}
          </button>
        </form>
      </div>
    </div>
  )
}
