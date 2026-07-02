import { useRef, useState } from 'react'
import { UploadCloud } from 'lucide-react'

interface PdfUploadProps {
  onFilesSelected: (files: File[]) => void
  needsReview?: string[]
}

/** Drag-and-drop PDF selector; shows low-confidence extraction flags. */
export default function PdfUpload({ onFilesSelected, needsReview }: PdfUploadProps) {
  const [dragOver, setDragOver] = useState(false)
  const [names, setNames] = useState<string[]>([])
  const inputRef = useRef<HTMLInputElement>(null)

  function handleFiles(list: FileList | null) {
    if (!list) return
    const files = Array.from(list).filter((f) => f.type === 'application/pdf')
    setNames(files.map((f) => f.name))
    onFilesSelected(files)
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragOver(false)
          handleFiles(e.dataTransfer.files)
        }}
        className={[
          'flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-8 cursor-pointer transition-colors',
          dragOver ? 'border-accent bg-accent/5' : 'border-border hover:border-accent/50',
        ].join(' ')}
      >
        <UploadCloud size={24} className="text-gray-500" />
        <div className="text-sm text-gray-400">
          Drop fund fact sheets / manager PDFs here, or click to browse
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
      </div>

      {names.length > 0 && (
        <ul className="mt-3 space-y-1 text-xs text-gray-400">
          {names.map((n) => (
            <li key={n}>• {n}</li>
          ))}
        </ul>
      )}

      {needsReview && needsReview.length > 0 && (
        <div className="mt-3 badge-warning">
          {needsReview.length} low-confidence extraction(s) flagged for review
        </div>
      )}
    </div>
  )
}
