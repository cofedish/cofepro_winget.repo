import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'

export default function DashboardPage() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get('/admin/dashboard/stats')
      return response.data
    },
  })

  if (isLoading) {
    return <div>Загрузка...</div>
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Панель управления</h1>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-sm font-medium text-muted-foreground">Всего пакетов</h3>
          <p className="mt-2 text-3xl font-bold">{stats?.total_packages || 0}</p>
        </div>

        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-sm font-medium text-muted-foreground">Всего версий</h3>
          <p className="mt-2 text-3xl font-bold">{stats?.total_versions || 0}</p>
        </div>

        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-sm font-medium text-muted-foreground">Всего установщиков</h3>
          <p className="mt-2 text-3xl font-bold">{stats?.total_installers || 0}</p>
        </div>

        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-sm font-medium text-muted-foreground">Использовано места</h3>
          <p className="mt-2 text-3xl font-bold">{formatBytes(stats?.total_size_bytes || 0)}</p>
        </div>

        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-sm font-medium text-muted-foreground">Зеркалированных пакетов</h3>
          <p className="mt-2 text-3xl font-bold">{stats?.mirrored_packages || 0}</p>
        </div>

        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-sm font-medium text-muted-foreground">Ручных пакетов</h3>
          <p className="mt-2 text-3xl font-bold">{stats?.manual_packages || 0}</p>
        </div>

        <div className="rounded-lg border bg-card p-6">
          <h3 className="text-sm font-medium text-muted-foreground">Недавних обновлений</h3>
          <p className="mt-2 text-3xl font-bold">{stats?.recent_updates || 0}</p>
          <p className="mt-1 text-xs text-muted-foreground">За последние 7 дней</p>
        </div>
      </div>

      <div className="rounded-lg border bg-card p-6">
        <h2 className="text-xl font-bold mb-4">Быстрый старт</h2>
        <div className="space-y-2">
          <p>Чтобы добавить этот репозиторий в ваш клиент WinGet, выполните:</p>
          <pre className="bg-muted p-4 rounded overflow-x-auto">
            <code>winget source add -n Private -t Microsoft.Rest -a {window.location.origin}</code>
          </pre>
          <p className="text-sm text-muted-foreground mt-4">
            Затем ищите и устанавливайте пакеты, используя <code className="bg-muted px-1">winget search</code> и <code className="bg-muted px-1">winget install</code>
          </p>
        </div>
      </div>
    </div>
  )
}
