import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../lib/api'

export default function UploadPage() {
  const queryClient = useQueryClient()
  const [uploadMethod, setUploadMethod] = useState<'file' | 'url'>('file')
  const [isExtractingMetadata, setIsExtractingMetadata] = useState(false)

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

  // Auto-extract metadata when file is selected
  useEffect(() => {
    if (selectedFile && uploadMethod === 'file') {
      extractMetadataFromFile(selectedFile)
    }
  }, [selectedFile])

  // Extract metadata from file
  const extractMetadataFromFile = async (file: File) => {
    setIsExtractingMetadata(true)
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await api.post('/admin/extract-metadata', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      const metadata = response.data

      // Auto-fill form fields if metadata is available
      if (metadata.product_name && !packageName) {
        setPackageName(metadata.product_name)
      }
      if (metadata.publisher && !publisher) {
        setPublisher(metadata.publisher)
      }
      if (metadata.version && !version) {
        setVersion(metadata.version)
      }
      if (metadata.description && !description) {
        setDescription(metadata.description)
      }

      // Auto-generate package ID if not set
      if (metadata.publisher && metadata.product_name && !packageId) {
        const id = `${metadata.publisher.replace(/\s+/g, '')}.${metadata.product_name.replace(/\s+/g, '')}`
        setPackageId(id)
      }
    } catch (error) {
      console.error('Failed to extract metadata:', error)
    } finally {
      setIsExtractingMetadata(false)
    }
  }

  // Extract metadata from URL
  const extractMetadataFromUrl = async () => {
    if (!sourceUrl) return

    setIsExtractingMetadata(true)
    try {
      const response = await api.post('/admin/extract-metadata-from-url', {
        url: sourceUrl,
      })

      const metadata = response.data

      // Auto-fill form fields if metadata is available
      if (metadata.product_name && !packageName) {
        setPackageName(metadata.product_name)
      }
      if (metadata.publisher && !publisher) {
        setPublisher(metadata.publisher)
      }
      if (metadata.version && !version) {
        setVersion(metadata.version)
      }
      if (metadata.description && !description) {
        setDescription(metadata.description)
      }

      // Auto-generate package ID if not set
      if (metadata.publisher && metadata.product_name && !packageId) {
        const id = `${metadata.publisher.replace(/\s+/g, '')}.${metadata.product_name.replace(/\s+/g, '')}`
        setPackageId(id)
      }

      alert('Метаданные успешно извлечены!')
    } catch (error) {
      console.error('Failed to extract metadata:', error)
      alert('Не удалось извлечь метаданные из URL')
    } finally {
      setIsExtractingMetadata(false)
    }
  }

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
      alert('Пакет успешно загружен!')
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
      const detail = error?.response?.data?.detail || 'Ошибка загрузки'
      alert(`Ошибка: ${detail}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!packageId || !packageName || !publisher || !version) {
      alert('Пожалуйста, заполните все обязательные поля')
      return
    }

    if (uploadMethod === 'file' && !selectedFile) {
      alert('Пожалуйста, выберите файл')
      return
    }

    if (uploadMethod === 'url' && !sourceUrl) {
      alert('Пожалуйста, введите URL')
      return
    }

    uploadMutation.mutate()
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Загрузка пакета</h1>
        <p className="text-muted-foreground mt-2">
          Добавить новый пакет в репозиторий. Метаданные будут автоматически извлечены из установочного файла.
        </p>
      </div>

      {isExtractingMetadata && (
        <div className="rounded-lg border bg-blue-50 dark:bg-blue-950 p-4">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            🔍 Извлекаем метаданные из файла...
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Upload Method */}
        <div className="rounded-lg border bg-card p-6 space-y-4">
          <h2 className="text-xl font-semibold">Установочный файл</h2>

          <div className="flex gap-2 mb-4">
            <button
              type="button"
              onClick={() => setUploadMethod('file')}
              className={`px-4 py-2 rounded-md ${
                uploadMethod === 'file' ? 'bg-primary text-primary-foreground' : 'bg-muted'
              }`}
            >
              Загрузить файл
            </button>
            <button
              type="button"
              onClick={() => setUploadMethod('url')}
              className={`px-4 py-2 rounded-md ${
                uploadMethod === 'url' ? 'bg-primary text-primary-foreground' : 'bg-muted'
              }`}
            >
              Из URL
            </button>
          </div>

          {uploadMethod === 'file' ? (
            <div>
              <label className="block text-sm font-medium mb-1">Выберите файл *</label>
              <input
                type="file"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                className="w-full rounded-md border bg-background px-3 py-2"
                accept=".exe,.msi,.msix"
              />
              {selectedFile && (
                <p className="mt-1 text-sm text-muted-foreground">
                  {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} МБ)
                </p>
              )}
              <p className="mt-1 text-xs text-muted-foreground">
                Метаданные будут автоматически извлечены из файла
              </p>
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium mb-1">URL установщика *</label>
              <div className="flex gap-2">
                <input
                  type="url"
                  value={sourceUrl}
                  onChange={(e) => setSourceUrl(e.target.value)}
                  placeholder="https://example.com/installer.exe"
                  className="flex-1 rounded-md border bg-background px-3 py-2"
                />
                <button
                  type="button"
                  onClick={extractMetadataFromUrl}
                  disabled={!sourceUrl || isExtractingMetadata}
                  className="px-4 py-2 rounded-md bg-secondary hover:bg-secondary/80 disabled:opacity-50"
                >
                  {isExtractingMetadata ? 'Извлечение...' : 'Извлечь метаданные'}
                </button>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Нажмите кнопку для извлечения метаданных из файла по URL
              </p>
            </div>
          )}

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium mb-1">Архитектура</label>
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
              <label className="block text-sm font-medium mb-1">Тип установщика</label>
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
        </div>

        {/* Package Information */}
        <div className="rounded-lg border bg-card p-6 space-y-4">
          <h2 className="text-xl font-semibold">Информация о пакете</h2>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium mb-1">
                ID пакета * <span className="text-xs text-muted-foreground">(напр. Publisher.AppName)</span>
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
              <label className="block text-sm font-medium mb-1">Название пакета *</label>
              <input
                type="text"
                required
                value={packageName}
                onChange={(e) => setPackageName(e.target.value)}
                placeholder="Моё приложение"
                className="w-full rounded-md border bg-background px-3 py-2"
              />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="block text-sm font-medium mb-1">Издатель *</label>
              <input
                type="text"
                required
                value={publisher}
                onChange={(e) => setPublisher(e.target.value)}
                placeholder="Моя компания"
                className="w-full rounded-md border bg-background px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Версия *</label>
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
            <label className="block text-sm font-medium mb-1">Описание (опционально)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Краткое описание пакета"
              className="w-full rounded-md border bg-background px-3 py-2"
              rows={2}
            />
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={uploadMutation.isPending || isExtractingMetadata}
          className="w-full rounded-md bg-primary px-6 py-3 text-primary-foreground font-medium hover:bg-primary/90 disabled:opacity-50"
        >
          {uploadMutation.isPending ? 'Загрузка...' : 'Загрузить пакет'}
        </button>
      </form>

      {/* Help Text */}
      <div className="rounded-lg border bg-muted/50 p-4">
        <h3 className="font-semibold mb-2">Нужна помощь?</h3>
        <ul className="text-sm text-muted-foreground space-y-1">
          <li>• ID пакета должен следовать формату: Издатель.НазваниеПриложения</li>
          <li>• Версия должна следовать семантическому версионированию (напр. 1.0.0)</li>
          <li>• Метаданные (название, издатель, версия) автоматически извлекаются из установочного файла</li>
          <li>• Для зеркалируемых пакетов из WinGet используйте Настройки → Allow List</li>
        </ul>
      </div>
    </div>
  )
}
