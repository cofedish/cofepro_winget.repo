import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../lib/api'
import { useAuth } from '../lib/auth'

interface User {
  id: number
  username: string
  email: string
  role: string
  is_active: boolean
  created_at: string
}

interface UserFormData {
  username: string
  email: string
  password: string
  role: string
  is_active: boolean
}

export default function UsersPage() {
  const { user: currentUser } = useAuth()
  const queryClient = useQueryClient()
  const [showAddModal, setShowAddModal] = useState(false)
  const [formData, setFormData] = useState<UserFormData>({
    username: '',
    email: '',
    password: '',
    role: 'viewer',
    is_active: true,
  })

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await api.get('/admin/users')
      return response.data
    },
  })

  const createUserMutation = useMutation({
    mutationFn: async (userData: UserFormData) => {
      const response = await api.post('/admin/users', userData)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setShowAddModal(false)
      setFormData({
        username: '',
        email: '',
        password: '',
        role: 'viewer',
        is_active: true,
      })
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createUserMutation.mutate(formData)
  }

  // Only admins can see this page
  if (currentUser?.role !== 'admin') {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600">Доступ запрещен</h2>
          <p className="mt-2 text-muted-foreground">У вас нет прав для просмотра этой страницы.</p>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return <div>Загрузка пользователей...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Пользователи</h1>
        <button
          onClick={() => setShowAddModal(true)}
          className="rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90"
        >
          Добавить пользователя
        </button>
      </div>

      <div className="rounded-lg border bg-card">
        <table className="w-full">
          <thead className="border-b">
            <tr>
              <th className="p-4 text-left">Имя пользователя</th>
              <th className="p-4 text-left">Email</th>
              <th className="p-4 text-left">Роль</th>
              <th className="p-4 text-left">Статус</th>
              <th className="p-4 text-left">Создан</th>
            </tr>
          </thead>
          <tbody>
            {users?.map((user: User) => (
              <tr key={user.id} className="border-b hover:bg-muted/50">
                <td className="p-4 font-medium">{user.username}</td>
                <td className="p-4">{user.email}</td>
                <td className="p-4">
                  <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                    user.role === 'admin' ? 'bg-purple-100 text-purple-700' :
                    user.role === 'maintainer' ? 'bg-blue-100 text-blue-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {user.role}
                  </span>
                </td>
                <td className="p-4">
                  <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                    user.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}>
                    {user.is_active ? 'Активен' : 'Неактивен'}
                  </span>
                </td>
                <td className="p-4 text-sm text-muted-foreground">
                  {new Date(user.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add User Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold mb-4">Добавить нового пользователя</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Имя пользователя</label>
                <input
                  type="text"
                  required
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  className="w-full rounded-md border bg-background px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Email</label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="w-full rounded-md border bg-background px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Пароль</label>
                <input
                  type="password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full rounded-md border bg-background px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Роль</label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  className="w-full rounded-md border bg-background px-3 py-2"
                >
                  <option value="viewer">Зритель</option>
                  <option value="maintainer">Редактор</option>
                  <option value="admin">Администратор</option>
                </select>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  className="mr-2"
                />
                <label htmlFor="is_active" className="text-sm font-medium">Активен</label>
              </div>
              <div className="flex gap-2 pt-4">
                <button
                  type="submit"
                  disabled={createUserMutation.isPending}
                  className="flex-1 rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {createUserMutation.isPending ? 'Создание...' : 'Создать пользователя'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 rounded-md border px-4 py-2 hover:bg-muted"
                >
                  Отмена
                </button>
              </div>
              {createUserMutation.isError && (
                <p className="text-sm text-red-600">
                  Ошибка: {(createUserMutation.error as any)?.response?.data?.detail || 'Не удалось создать пользователя'}
                </p>
              )}
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
