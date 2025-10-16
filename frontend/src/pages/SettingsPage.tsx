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
      alert('Allow list saved successfully! Restart the updater to apply changes.')
      queryClient.invalidateQueries({ queryKey: ['allow-list'] })
    },
    onError: (error: any) => {
      alert(`Error: ${error?.response?.data?.detail || 'Failed to save'}`)
    },
  })

  const triggerUpdaterMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/system/updater/trigger')
      return response.data
    },
    onSuccess: () => {
      alert('Updater restarted successfully! Synchronization will begin shortly.')
    },
    onError: (error: any) => {
      alert(`Error: ${error?.response?.data?.detail || 'Failed to trigger updater'}`)
    },
  })

  if (user?.role !== 'admin') {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600">Access Denied</h2>
          <p className="mt-2 text-muted-foreground">You don't have permission to view this page.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>

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
          Allow List
        </button>
        <button
          onClick={() => setActiveTab('updater')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'updater'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Updater
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'audit'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Audit Logs
        </button>
      </div>

      {/* Allow List Tab */}
      {activeTab === 'allowlist' && (
        <div className="space-y-4">
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-xl font-semibold mb-4">Package Allow List</h2>
            <p className="text-muted-foreground mb-4">
              Configure which packages should be automatically mirrored from the public WinGet repository.
              Add package identifiers, architectures, installer types, and version limits.
            </p>

            {allowListLoading ? (
              <div className="text-center p-8">Loading...</div>
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
                    {saveAllowListMutation.isPending ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button
                    onClick={() => queryClient.invalidateQueries({ queryKey: ['allow-list'] })}
                    className="rounded-md border px-6 py-2 hover:bg-muted"
                  >
                    Reset
                  </button>
                </div>
              </>
            )}
          </div>

          <div className="rounded-lg border bg-muted/50 p-4">
            <h3 className="font-semibold mb-2">Example Configuration</h3>
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
            <h2 className="text-xl font-semibold mb-4">Updater Service</h2>
            <p className="text-muted-foreground mb-6">
              The updater automatically synchronizes packages from the public WinGet repository based on your allow list.
              It runs periodically in the background.
            </p>

            <div className="space-y-4">
              <div className="rounded-lg border p-4">
                <h3 className="font-semibold mb-2">Manual Synchronization</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Click the button below to restart the updater service and trigger an immediate synchronization.
                  This is useful after updating the allow list.
                </p>
                <button
                  onClick={() => triggerUpdaterMutation.mutate()}
                  disabled={triggerUpdaterMutation.isPending}
                  className="rounded-md bg-primary px-6 py-2 text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
                >
                  {triggerUpdaterMutation.isPending ? 'Triggering...' : 'Trigger Sync Now'}
                </button>
              </div>

              <div className="rounded-lg border p-4">
                <h3 className="font-semibold mb-2">How It Works</h3>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>• Updater reads the allow list configuration</li>
                  <li>• Fetches package manifests from WinGet Community repository</li>
                  <li>• Downloads installer files and verifies SHA256 checksums</li>
                  <li>• Stores installers in S3/MinIO</li>
                  <li>• Creates or updates package records in the database</li>
                  <li>• Marked as "Mirrored" packages in the Packages list</li>
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
            <div className="p-8 text-center">Loading audit logs...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="border-b">
                  <tr>
                    <th className="p-4 text-left">Timestamp</th>
                    <th className="p-4 text-left">User</th>
                    <th className="p-4 text-left">Action</th>
                    <th className="p-4 text-left">Entity</th>
                    <th className="p-4 text-left">Identifier</th>
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
