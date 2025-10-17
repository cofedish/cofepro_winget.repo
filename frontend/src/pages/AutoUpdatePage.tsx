import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../lib/api'

interface Package {
  id: number
  identifier: string
  name: string
  publisher: string
  is_active: boolean
  auto_update_config?: AutoUpdateConfig
}

interface AutoUpdateConfig {
  id: number
  package_id: number
  enabled: boolean
  architectures: string[]
  installer_types: string[]
  max_versions: number
  last_sync_at?: string
  last_sync_status?: string
  last_sync_message?: string
}

export default function AutoUpdatePage() {
  const queryClient = useQueryClient()
  const [selectedPackage, setSelectedPackage] = useState<Package | null>(null)
  const [showDialog, setShowDialog] = useState(false)

  // Form state
  const [enabled, setEnabled] = useState(true)
  const [architectures, setArchitectures] = useState<string[]>(['x64'])
  const [installerTypes, setInstallerTypes] = useState<string[]>(['exe', 'msi'])
  const [maxVersions, setMaxVersions] = useState(1)

  // Fetch all packages
  const { data: packages, isLoading } = useQuery({
    queryKey: ['packages'],
    queryFn: async () => {
      const response = await api.get('/admin/packages')
      return response.data as Package[]
    },
  })

  // Fetch packages with auto-update configs
  const { data: autoUpdatePackages } = useQuery({
    queryKey: ['auto-update-configs'],
    queryFn: async () => {
      const response = await api.get('/admin/auto-update/configs')
      return response.data as Package[]
    },
  })

  // Create auto-update config
  const createMutation = useMutation({
    mutationFn: async (data: {
      package_id: number
      enabled: boolean
      architectures: string[]
      installer_types: string[]
      max_versions: number
    }) => {
      const response = await api.post('/admin/auto-update/configs', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auto-update-configs'] })
      queryClient.invalidateQueries({ queryKey: ['packages'] })
      setShowDialog(false)
      setSelectedPackage(null)
    },
  })

  // Update auto-update config
  const updateMutation = useMutation({
    mutationFn: async ({
      package_id,
      data,
    }: {
      package_id: number
      data: Partial<AutoUpdateConfig>
    }) => {
      const response = await api.put(`/admin/auto-update/configs/${package_id}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auto-update-configs'] })
      queryClient.invalidateQueries({ queryKey: ['packages'] })
    },
  })

  // Delete auto-update config
  const deleteMutation = useMutation({
    mutationFn: async (package_id: number) => {
      await api.delete(`/admin/auto-update/configs/${package_id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auto-update-configs'] })
      queryClient.invalidateQueries({ queryKey: ['packages'] })
    },
  })

  const handleEnableAutoUpdate = (pkg: Package) => {
    setSelectedPackage(pkg)
    setEnabled(true)
    setArchitectures(['x64'])
    setInstallerTypes(['exe', 'msi'])
    setMaxVersions(1)
    setShowDialog(true)
  }

  const handleSubmit = () => {
    if (!selectedPackage) return

    createMutation.mutate({
      package_id: selectedPackage.id,
      enabled,
      architectures,
      installer_types: installerTypes,
      max_versions: maxVersions,
    })
  }

  const handleToggleEnabled = (pkg: Package) => {
    if (!pkg.auto_update_config) return

    updateMutation.mutate({
      package_id: pkg.id,
      data: {
        enabled: !pkg.auto_update_config.enabled,
      },
    })
  }

  const handleDisableAutoUpdate = (pkg: Package) => {
    if (!confirm(`Отключить автообновление для ${pkg.name}?`)) return
    deleteMutation.mutate(pkg.id)
  }

  const toggleArchitecture = (arch: string) => {
    setArchitectures((prev) =>
      prev.includes(arch) ? prev.filter((a) => a !== arch) : [...prev, arch]
    )
  }

  const toggleInstallerType = (type: string) => {
    setInstallerTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    )
  }

  if (isLoading) {
    return <div className="p-6">Загрузка...</div>
  }

  const packagesWithAutoUpdate = autoUpdatePackages || []
  const packagesWithoutAutoUpdate =
    packages?.filter((pkg) => !packagesWithAutoUpdate.some((p) => p.id === pkg.id)) || []

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Автообновление пакетов</h1>
        <p className="text-gray-600">
          Управление автоматическим обновлением пакетов из публичного репозитория WinGet
        </p>
      </div>

      {/* Packages with auto-update enabled */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">
          Пакеты с автообновлением ({packagesWithAutoUpdate.length})
        </h2>
        <div className="bg-white rounded-lg shadow">
          {packagesWithAutoUpdate.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              Нет пакетов с включенным автообновлением
            </div>
          ) : (
            <div className="divide-y">
              {packagesWithAutoUpdate.map((pkg) => (
                <div key={pkg.id} className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold">{pkg.name}</h3>
                        <span className="text-sm text-gray-500">{pkg.identifier}</span>
                        {pkg.auto_update_config?.enabled ? (
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                            Включено
                          </span>
                        ) : (
                          <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded">
                            Отключено
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{pkg.publisher}</p>
                      {pkg.auto_update_config && (
                        <div className="text-sm text-gray-600">
                          <div>
                            <strong>Архитектуры:</strong>{' '}
                            {pkg.auto_update_config.architectures.join(', ') || 'Все'}
                          </div>
                          <div>
                            <strong>Типы установщиков:</strong>{' '}
                            {pkg.auto_update_config.installer_types.join(', ') || 'Все'}
                          </div>
                          <div>
                            <strong>Макс. версий:</strong> {pkg.auto_update_config.max_versions}
                          </div>
                          {pkg.auto_update_config.last_sync_at && (
                            <div>
                              <strong>Последняя синхронизация:</strong>{' '}
                              {new Date(pkg.auto_update_config.last_sync_at).toLocaleString('ru')}
                              {' - '}
                              <span
                                className={
                                  pkg.auto_update_config.last_sync_status === 'success'
                                    ? 'text-green-600'
                                    : 'text-red-600'
                                }
                              >
                                {pkg.auto_update_config.last_sync_status}
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleToggleEnabled(pkg)}
                        className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                      >
                        {pkg.auto_update_config?.enabled ? 'Выключить' : 'Включить'}
                      </button>
                      <button
                        onClick={() => handleDisableAutoUpdate(pkg)}
                        className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
                      >
                        Удалить
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Packages without auto-update */}
      <div>
        <h2 className="text-xl font-semibold mb-4">
          Доступные пакеты ({packagesWithoutAutoUpdate.length})
        </h2>
        <div className="bg-white rounded-lg shadow">
          {packagesWithoutAutoUpdate.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              Все пакеты уже добавлены в автообновление
            </div>
          ) : (
            <div className="divide-y">
              {packagesWithoutAutoUpdate.map((pkg) => (
                <div key={pkg.id} className="p-4 flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">{pkg.name}</h3>
                    <p className="text-sm text-gray-500">{pkg.identifier}</p>
                    <p className="text-sm text-gray-600">{pkg.publisher}</p>
                  </div>
                  <button
                    onClick={() => handleEnableAutoUpdate(pkg)}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    Включить автообновление
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Config Dialog */}
      {showDialog && selectedPackage && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 max-w-lg w-full">
            <h2 className="text-2xl font-bold mb-4">
              Настройка автообновления: {selectedPackage.name}
            </h2>

            <div className="space-y-4">
              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={enabled}
                    onChange={(e) => setEnabled(e.target.checked)}
                    className="rounded"
                  />
                  <span className="font-medium">Включить автообновление</span>
                </label>
              </div>

              <div>
                <label className="block font-medium mb-2">Архитектуры:</label>
                <div className="space-y-2">
                  {['x64', 'x86', 'arm64'].map((arch) => (
                    <label key={arch} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={architectures.includes(arch)}
                        onChange={() => toggleArchitecture(arch)}
                        className="rounded"
                      />
                      <span>{arch}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block font-medium mb-2">Типы установщиков:</label>
                <div className="space-y-2">
                  {['exe', 'msi', 'msix'].map((type) => (
                    <label key={type} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={installerTypes.includes(type)}
                        onChange={() => toggleInstallerType(type)}
                        className="rounded"
                      />
                      <span>{type.toUpperCase()}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block font-medium mb-2">Максимум версий:</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={maxVersions}
                  onChange={(e) => setMaxVersions(parseInt(e.target.value))}
                  className="w-full px-3 py-2 border rounded"
                />
                <p className="text-sm text-gray-500 mt-1">
                  Количество последних версий для хранения (1-10)
                </p>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={handleSubmit}
                disabled={createMutation.isPending}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {createMutation.isPending ? 'Сохранение...' : 'Сохранить'}
              </button>
              <button
                onClick={() => {
                  setShowDialog(false)
                  setSelectedPackage(null)
                }}
                className="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
