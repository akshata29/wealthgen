import { useState } from 'react'
import { Download, FileText, Mail, FileType } from 'lucide-react'
import * as api from '@/utils/apiClient'

interface ExportMenuProps {
  commentaryId: string
  mandateId: string
}

/** Export controls — download the approved brief as PDF / Word or as an email. */
export default function ExportMenu({ commentaryId, mandateId }: ExportMenuProps) {
  const [email, setEmail] = useState('')
  const [showEmail, setShowEmail] = useState(false)

  return (
    <div className="card space-y-3">
      <div className="flex items-center gap-2">
        <Download size={16} className="text-gray-400" />
        <h3 className="text-sm font-semibold text-gray-100">Export</h3>
      </div>
      <div className="flex flex-wrap gap-2">
        <a className="btn-secondary" href={api.exportUrl(commentaryId, mandateId, 'pdf')} download>
          <span className="inline-flex items-center gap-2">
            <FileText size={14} /> PDF
          </span>
        </a>
        <a className="btn-secondary" href={api.exportUrl(commentaryId, mandateId, 'docx')} download>
          <span className="inline-flex items-center gap-2">
            <FileType size={14} /> Word
          </span>
        </a>
        <button className="btn-secondary" onClick={() => setShowEmail((v) => !v)}>
          <span className="inline-flex items-center gap-2">
            <Mail size={14} /> Email
          </span>
        </button>
      </div>
      {showEmail && (
        <div className="flex items-center gap-2">
          <input
            className="input"
            type="email"
            placeholder="client@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <a
            className={email ? 'btn-primary' : 'btn-primary pointer-events-none opacity-50'}
            href={email ? api.emailExportUrl(commentaryId, mandateId, email) : undefined}
            download
          >
            Download .eml
          </a>
        </div>
      )}
    </div>
  )
}
