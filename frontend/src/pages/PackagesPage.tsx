import { useQuery } from '@tanstack/react-query'
import api from '../lib/api'

export default function PackagesPage() {
  const { data: packages, isLoading } = useQuery({
    queryKey: ['packages'],
    queryFn: async () => {
      const response = await api.get('/admin/packages')
      return response.data
    },
  })

  if (isLoading) {
    return <div>Загрузка пакетов...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Пакеты</h1>
        <p className="text-muted-foreground mt-2">
          Просмотр всех пакетов в репозитории. <strong>Зеркалированные</strong> пакеты автоматически синхронизируются из WinGet.
          <strong> Ручные</strong> пакеты загружены вами.
        </p>
      </div>

      <div className="rounded-lg border bg-card">
        <table className="w-full">
          <thead className="border-b">
            <tr>
              <th className="p-4 text-left">Идентификатор</th>
              <th className="p-4 text-left">Название</th>
              <th className="p-4 text-left">Издатель</th>
              <th className="p-4 text-left">Тип</th>
              <th className="p-4 text-left">Статус</th>
            </tr>
          </thead>
          <tbody>
            {packages?.map((pkg: any) => (
              <tr key={pkg.id} className="border-b hover:bg-muted/50">
                <td className="p-4 font-mono text-sm">{pkg.identifier}</td>
                <td className="p-4">{pkg.name}</td>
                <td className="p-4">{pkg.publisher}</td>
                <td className="p-4">
                  <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                    pkg.is_mirrored ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
                  }`}>
                    {pkg.is_mirrored ? 'Зеркалированный' : 'Ручной'}
                  </span>
                </td>
                <td className="p-4">
                  <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                    pkg.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {pkg.is_active ? 'Активен' : 'Неактивен'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
