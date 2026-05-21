import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { reportApi } from '../../utils/api'
import { useAppStore } from '../../store/useAppStore'
import { FileText, Download } from 'lucide-react'
import toast from 'react-hot-toast'

const THREAT_COLOR: Record<string, string> = {
  critical: 'text-nexus-red',
  high: 'text-nexus-orange',
  medium: 'text-yellow-400',
  low: 'text-nexus-green',
}

export default function ReportsPanel() {
  const qc = useQueryClient()
  const { activeScanId, pushLog } = useAppStore()
  const [newTitle, setNewTitle] = useState('')

  const { data: reports = [] } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportApi.list().then((r) => r.data),
    refetchInterval: 20_000,
  })

  const createMutation = useMutation({
    mutationFn: () =>
      reportApi.create({
        scan_id: activeScanId!,
        title: newTitle || `REPORT-${new Date().toISOString().slice(0, 10)}`,
      }),
    onSuccess: () => {
      toast.success('Report generation started')
      pushLog('Report generation initiated')
      setNewTitle('')
      qc.invalidateQueries({ queryKey: ['reports'] })
    },
    onError: () => toast.error('Failed to generate report'),
  })

  const downloadPdf = async (id: string) => {
    try {
      const res = await reportApi.downloadPdf(id)
      const url = URL.createObjectURL(new Blob([res.data]))
      const a = document.createElement('a')
      a.href = url
      a.download = `report_${id.slice(0, 8)}.pdf`
      a.click()
    } catch {
      toast.error('PDF not available yet')
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-nexus-border">
        <FileText size={14} className="text-nexus-cyan" />
        <span className="font-mono text-xs text-nexus-cyan tracking-widest uppercase">Reports</span>
      </div>

      {/* Generate new report */}
      {activeScanId && (
        <div className="p-3 border-b border-nexus-border space-y-2">
          <input
            className="nexus-input text-[11px]"
            placeholder="Report title..."
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
          />
          <button
            onClick={() => createMutation.mutate()}
            disabled={createMutation.isPending}
            className="nexus-btn-primary w-full text-xs py-2"
          >
            {createMutation.isPending ? 'GENERATING...' : '▶ GENERATE REPORT'}
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto space-y-1 p-2">
        {reports.map((r: any, i: number) => (
          <motion.div
            key={r.id}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: i * 0.04 }}
            className="nexus-panel p-3"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="font-mono text-[10px] text-nexus-text font-medium truncate">{r.title}</div>
                {r.threat_level && (
                  <div className={`font-mono text-[9px] mt-0.5 ${THREAT_COLOR[r.threat_level] || 'text-nexus-text'}`}>
                    THREAT: {r.threat_level.toUpperCase()}
                  </div>
                )}
                <div className="font-mono text-[9px] text-nexus-muted/60 mt-0.5">
                  {new Date(r.created_at).toLocaleDateString()}
                </div>
              </div>
              {r.pdf_path && (
                <button
                  onClick={() => downloadPdf(r.id)}
                  className="text-nexus-cyan hover:text-nexus-green transition-colors"
                  title="Download PDF"
                >
                  <Download size={12} />
                </button>
              )}
            </div>
            {r.summary && (
              <div className="mt-2 font-mono text-[9px] text-nexus-muted line-clamp-2">{r.summary}</div>
            )}
          </motion.div>
        ))}

        {reports.length === 0 && (
          <div className="flex items-center justify-center h-32">
            <span className="font-mono text-xs text-nexus-muted">NO REPORTS</span>
          </div>
        )}
      </div>
    </div>
  )
}
