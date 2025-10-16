import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../lib/api'
import { useAuth } from '../lib/auth'

interface AuditLog {
  id: number
  user_id: number
  action: string
  entity_type: string
  entity_id?: number
  entity_identifier?: string
  ip_address?: string
  timestamp: string
}

export default function SettingsPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'audit' | 'allowlist' | 'updater'>('allowlist')
  const [allowListContent, setAllowListContent] = useState('')

  const { data: auditLogs, isLoading: auditLoading } = useQuery({
    queryKey: ['audit-logs'],
    queryFn: async () => {
      const response = await api.get('/admin/audit-logs?limit=50')
      return response.data
    },
    enabled: user?.role === 'admin' && activeTab === 'audit',
  })

  const { isLoading: allowListLoading } = useQuery({
    queryKey: ['allow-list'],
    queryFn: async () => {
      const response = await api.get('/system/allow-list')
      const data = response.data
      setAllowListContent(data.content)
      return data
    },
    enabled: user?.role === 'admin' && activeTab === 'allowlist',
  })

  const saveAllowListMutation = useMutation({
    mutationFn: async (content: string) => {
      const response = await api.post('/system/allow-list', { content })
      return response.data
    },
    onSuccess: () => {
      alert('Список разрешений успешно сохранен! Перезапустите службу обновления для применения изменений.')
      queryClient.invalidateQueries({ queryKey: ['allow-list'] })
    },
    onError: (error: any) => {
      alert(`Ошибка: ${error?.response?.data?.detail || 'Не удалось сохранить'}`)
    },
  })

  const triggerUpdaterMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/system/updater/trigger')
      return response.data
    },
    onSuccess: () => {
      alert('Служба обновления успешно перезапущена! Синхронизация начнется в ближайшее время.')
    },
    onError: (error: any) => {
      alert(`Ошибка: ${error?.response?.data?.detail || 'Не удалось запустить службу обновления'}`)
    },
  })

  if (user?.role !== 'admin') {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600">Доступ запрещен</h2>
          <p className="mt-2 text-muted-foreground">У вас нет прав для просмотра этой страницы.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Настройки</h1>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('allowlist')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'allowlist'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Список разрешений
        </button>
        <button
          onClick={() => setActiveTab('updater')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'updater'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Служба обновления
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'audit'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Журнал аудита
        </button>
      </div>

      {/* Allow List Tab */}
      {activeTab === 'allowlist' && (
        <div className="space-y-4">
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-xl font-semibold mb-4">Список разрешенных пакетов</h2>
            <p className="text-muted-foreground mb-4">
              Настройте, какие пакеты должны автоматически зеркалироваться из публичного репозитория WinGet.
              Добавьте идентификаторы пакетов, архитектуры, типы установщиков и лимиты версий.
            </p>

            {allowListLoading ? (
              <div className="text-center p-8">Загрузка...</div>
            ) : (
              <>
                <textarea
                  value={allowListContent}
                  onChange={(e) => setAllowListContent(e.target.value)}
                  className="w-full h-96 rounded-md border bg-background px-4 py-3 font-mono text-sm"
                  placeholder='{\n  "packages": []\n}'
                />

                <div className="flex gap-2 mt-4">
                  <button
                    onClick={() => saveAllowListMutation.mutate(allowListContent)}
                    disabled={saveAllowListMutation.isPending}
                    className="rounded-md bg-primary px-6 py-2 text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                  >
                    {saveAllowListMutation.isPending ? 'Сохранение...' : 'Сохранить изменения'}
                  </button>
                  <button
                    onClick={() => queryClient.invalidateQueries({ queryKey: ['allow-list'] })}
                    className="rounded-md border px-6 py-2 hover:bg-muted"
                  >
                    Сбросить
                  </button>
                </div>
              </>
            )}
          </div>

          <div className="rounded-lg border bg-muted/50 p-4">
            <h3 className="font-semibold mb-2">Пример конфигурации</h3>
            <pre className="text-sm overflow-x-auto bg-background p-3 rounded">
{`{
  "packages": [
    {
      "package_identifier": "7zip.7zip",
      "architectures": ["x64", "x86"],
      "installer_types": ["exe", "msi"],
      "max_versions": 3
    },
    {
      "package_identifier": "VideoLAN.VLC",
      "architectures": ["x64"],
      "installer_types": ["msi"],
      "max_versions": 2
    }
  ]
}`}
            </pre>
          </div>
        </div>
      )}

      {/* Updater Tab */}
      {activeTab === 'updater' && (
        <div className="space-y-4">
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-xl font-semibold mb-4">Служба обновления</h2>
            <p className="text-muted-foreground mb-6">
              Служба обновления автоматически синхронизирует пакеты из публичного репозитория WinGet на основе вашего списка разрешений.
              Она работает периодически в фоновом режиме.
            </p>

            <div className="space-y-4">
              <div className="rounded-lg border p-4">
                <h3 className="font-semibold mb-2">Ручная синхронизация</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Нажмите кнопку ниже, чтобы перезапустить службу обновления и запустить немедленную синхронизацию.
                  Это полезно после обновления списка разрешений.
                </p>
                <button
                  onClick={() => triggerUpdaterMutation.mutate()}
                  disabled={triggerUpdaterMutation.isPending}
                  className="rounded-md bg-primary px-6 py-2 text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {triggerUpdaterMutation.isPending ? 'Запуск...' : 'Запустить синхронизацию'}
                </button>
              </div>

              <div className="rounded-lg border p-4">
                <h3 className="font-semibold mb-2">Как это работает</h3>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Служба обновления читает конфигурацию списка разрешений</li>
                  <li>• Получает манифесты пакетов из репозитория WinGet Community</li>
                  <li>• Загружает файлы установщиков и проверяет контрольные суммы SHA256</li>
                  <li>• Сохраняет установщики в S3/MinIO</li>
                  <li>• Создает или обновляет записи пакетов в базе данных</li>
                  <li>• Помечает пакеты как "Зеркалированные" в списке пакетов</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Audit Logs Tab */}
      {activeTab === 'audit' && (
        <div className="rounded-lg border bg-card">
          {auditLoading ? (
            <div className="p-8 text-center">Загрузка журнала аудита...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b">
                  <tr>
                    <th className="p-4 text-left">Время</th>
                    <th className="p-4 text-left">Пользователь</th>
                    <th className="p-4 text-left">Действие</th>
                    <th className="p-4 text-left">Сущность</th>
                    <th className="p-4 text-left">Идентификатор</th>
                    <th className="p-4 text-left">IP</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs?.map((log: AuditLog) => (
                    <tr key={log.id} className="border-b hover:bg-muted/50">
                      <td className="p-4 text-sm">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="p-4 text-sm">User #{log.user_id}</td>
                      <td className="p-4">
                        <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                          log.action === 'create' ? 'bg-green-100 text-green-700' :
                          log.action === 'update' ? 'bg-blue-100 text-blue-700' :
                          log.action === 'delete' ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {log.action}
                        </span>
                      </td>
                      <td className="p-4 text-sm">{log.entity_type}</td>
                      <td className="p-4 text-sm font-mono">{log.entity_identifier || '-'}</td>
                      <td className="p-4 text-sm text-muted-foreground">{log.ip_address || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
