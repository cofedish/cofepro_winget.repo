import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../lib/api'

export default function UploadPage() {
  const queryClient = useQueryClient()
  const [uploadMethod, setUploadMethod] = useState<'file' | 'url'>('file')

  // Form data
  const [packageId, setPackageId] = useState('')
  const [packageName, setPackageName] = useState('')
  const [publisher, setPublisher] = useState('')
  const [version, setVersion] = useState('')
  const [description, setDescription] = useState('')

  // File/URL
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [sourceUrl, setSourceUrl] = useState('')

  // Optional fields
  const [architecture, setArchitecture] = useState('x64')
  const [installerType, setInstallerType] = useState('exe')

  const uploadMutation = useMutation({
    mutationFn: async () => {
      // Create package
      const pkgResponse = await api.post('/admin/packages', {
        identifier: packageId,
        name: packageName,
        publisher: publisher,
        description: description || undefined,
      })

      const packageDbId = pkgResponse.data.id

      // Create version
      const verResponse = await api.post('/admin/versions', {
        package_id: packageDbId,
        version: version,
      })

      const versionId = verResponse.data.id

      // Upload installer
      if (uploadMethod === 'file' && selectedFile) {
        const formData = new FormData()
        formData.append('file', selectedFile)

        await api.post(
          `/admin/upload?version_id=${versionId}&architecture=${architecture}&installer_type=${installerType}`,
          formData,
          { headers: { 'Content-Type': 'multipart/form-data' } }
        )
      } else if (uploadMethod === 'url' && sourceUrl) {
        await api.post('/admin/upload-from-url', {
          version_id: versionId,
          source_url: sourceUrl,
          architecture: architecture,
          installer_type: installerType,
        })
      }

      return { packageDbId }
    },
    onSuccess: () => {
      alert('Package uploaded successfully!')
      // Reset form
      setPackageId('')
      setPackageName('')
      setPublisher('')
      setVersion('')
      setDescription('')
      setSelectedFile(null)
      setSourceUrl('')
      queryClient.invalidateQueries({ queryKey: ['packages'] })
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail || 'Upload failed'
      alert(`Error: ${detail}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!packageId || !packageName || !publisher || !version) {
      alert('Please fill in all required fields')
      return
    }

    if (uploadMethod === 'file' && !selectedFile) {
      alert('Please select a file')
      return
    }

    if (uploadMethod === 'url' && !sourceUrl) {
      alert('Please enter a URL')
      return
    }

    uploadMutation.mutate()
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Upload Package</h1>
        <p className="text-muted-foreground mt-2">
          Add a new package to the repository. Fill in the package information and upload the installer file.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Package Information */}
        <div className="rounded-lg border bg-card p-6 space-y-4">
          <h2 className="text-xl font-semibold">Package Information</h2>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium mb-1">
                Package ID * <span className="text-xs text-muted-foreground">(e.g. Publisher.AppName)</span>
              </label>
              <input
                type="text"
                required
                value={packageId}
                onChange={(e) => setPackageId(e.target.value)}
                placeholder="MyCompany.MyApp"
                className="w-full rounded-md border bg-background px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Package Name *</label>
              <input
                type="text"
                required
                value={packageName}
                onChange={(e) => setPackageName(e.target.value)}
                placeholder="My Application"
                className="w-full rounded-md border bg-background px-3 py-2"
              />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium mb-1">Publisher *</label>
              <input
                type="text"
                required
                value={publisher}
                onChange={(e) => setPublisher(e.target.value)}
                placeholder="My Company"
                className="w-full rounded-md border bg-background px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Version *</label>
              <input
                type="text"
                required
                value={version}
                onChange={(e) => setVersion(e.target.value)}
                placeholder="1.0.0"
                className="w-full rounded-md border bg-background px-3 py-2"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Description (optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Brief description of the package"
              className="w-full rounded-md border bg-background px-3 py-2"
              rows={2}
            />
          </div>
        </div>

        {/* Upload Method */}
        <div className="rounded-lg border bg-card p-6 space-y-4">
          <h2 className="text-xl font-semibold">Installer File</h2>

          <div className="flex gap-2 mb-4">
            <button
              type="button"
              onClick={() => setUploadMethod('file')}
              className={`px-4 py-2 rounded-md ${
                uploadMethod === 'file' ? 'bg-primary text-primary-foreground' : 'bg-muted'
              }`}
            >
              Upload File
            </button>
            <button
              type="button"
              onClick={() => setUploadMethod('url')}
              className={`px-4 py-2 rounded-md ${
                uploadMethod === 'url' ? 'bg-primary text-primary-foreground' : 'bg-muted'
              }`}
            >
              From URL
            </button>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium mb-1">Architecture</label>
              <select
                value={architecture}
                onChange={(e) => setArchitecture(e.target.value)}
                className="w-full rounded-md border bg-background px-3 py-2"
              >
                <option value="x64">x64 (64-bit)</option>
                <option value="x86">x86 (32-bit)</option>
                <option value="arm">ARM</option>
                <option value="arm64">ARM64</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Installer Type</label>
              <select
                value={installerType}
                onChange={(e) => setInstallerType(e.target.value)}
                className="w-full rounded-md border bg-background px-3 py-2"
              >
                <option value="exe">EXE</option>
                <option value="msi">MSI</option>
                <option value="msix">MSIX</option>
                <option value="inno">Inno Setup</option>
                <option value="nullsoft">NSIS</option>
                <option value="portable">Portable</option>
              </select>
            </div>
          </div>

          {uploadMethod === 'file' ? (
            <div>
              <label className="block text-sm font-medium mb-1">Select File *</label>
              <input
                type="file"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                className="w-full rounded-md border bg-background px-3 py-2"
                accept=".exe,.msi,.msix"
              />
              {selectedFile && (
                <p className="mt-1 text-sm text-muted-foreground">
                  {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                </p>
              )}
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium mb-1">Installer URL *</label>
              <input
                type="url"
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                placeholder="https://example.com/installer.exe"
                className="w-full rounded-md border bg-background px-3 py-2"
              />
            </div>
          )}
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={uploadMutation.isPending}
          className="w-full rounded-md bg-primary px-6 py-3 text-primary-foreground font-medium hover:bg-primary/90 disabled:opacity-50"
        >
          {uploadMutation.isPending ? 'Uploading...' : 'Upload Package'}
        </button>
      </form>

      {/* Help Text */}
      <div className="rounded-lg border bg-muted/50 p-4">
        <h3 className="font-semibold mb-2">Need help?</h3>
        <ul className="text-sm text-muted-foreground space-y-1">
          <li>• Package ID should follow format: Publisher.ApplicationName</li>
          <li>• Version should follow semantic versioning (e.g. 1.0.0)</li>
          <li>• For mirrored packages from WinGet, use Settings → Allow List</li>
        </ul>
      </div>
    </div>
  )
}
