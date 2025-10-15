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
    return <div>Loading packages...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Packages</h1>
        <button className="rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90">
          Add Package
        </button>
      </div>

      <div className="rounded-lg border bg-card">
        <table className="w-full">
          <thead className="border-b">
            <tr>
              <th className="p-4 text-left">Identifier</th>
              <th className="p-4 text-left">Name</th>
              <th className="p-4 text-left">Publisher</th>
              <th className="p-4 text-left">Type</th>
              <th className="p-4 text-left">Status</th>
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
                    {pkg.is_mirrored ? 'Mirrored' : 'Manual'}
                  </span>
                </td>
                <td className="p-4">
                  <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                    pkg.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {pkg.is_active ? 'Active' : 'Inactive'}
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
