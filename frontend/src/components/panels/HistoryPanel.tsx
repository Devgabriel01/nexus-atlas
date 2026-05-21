import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { historyApi } from '../../utils/api'
import { useAppStore } from '../../store/useAppStore'
import { Clock, CheckCircle, XCircle, Loader } from 'lucide-react'

const STATUS_ICON: Record<string, React.ReactNode> = {
  completed: <CheckCircle size={10} className="text-nexus-green" />,
  failed: <XCircle size={10} className="text-nexus-red" />,
  processing: <Loader size={10} className="text-nexus-cyan animate-spin" />,
  pending: <Loader size={10} className="text-nexus-muted" />,
}

export default function HistoryPanel() {
  const { setActiveScanId, setMapCenter, setMapZoom } = useAppStore()

  const { data: history = [], isLoading } = useQuery({
    queryKey: ['history'],
    queryFn: () => historyApi.list().then((r) => r.data),
    refetchInterval: 15_000,
  })

  const handleSelect = (item: any) => {
    setActiveScanId(item.id)
    if (item.center?.lat && item.center?.lon) {
      setMapCenter([item.center.lon, item.center.lat])
      setMapZoom(8)
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-nexus-border">
        <Clock size={14} className="text-nexus-cyan" />
        <span className="font-mono text-xs text-nexus-cyan tracking-widest uppercase">Mission History</span>
        <span className="ml-auto font-mono text-[10px] text-nexus-muted">{history.length} ops</span>
      </div>

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <span className="font-mono text-xs text-nexus-cyan animate-pulse">LOADING...</span>
        </div>
      ) : history.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <span className="font-mono text-xs text-nexus-muted">NO HISTORY</span>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-1 p-2">
          {history.map((item: any, i: number) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.02 }}
              onClick={() => handleSelect(item)}
              className="nexus-panel p-3 cursor-pointer hover:nexus-border-glow transition-all"
            >
              <div className="flex items-center gap-2">
                {STATUS_ICON[item.status] ?? STATUS_ICON.pending}
                <span className="font-mono text-[10px] text-nexus-text font-medium truncate flex-1">
                  {item.name}
                </span>
                <span className="font-mono text-[9px] text-nexus-muted">
                  {item.anomaly_count} ⚠
                </span>
              </div>
              <div className="flex justify-between mt-1">
                <span className="font-mono text-[9px] text-nexus-muted uppercase">{item.scan_type}</span>
                <span className="font-mono text-[9px] text-nexus-muted/60">
                  {new Date(item.created_at).toLocaleDateString()}
                </span>
              </div>
              {item.confidence_score > 0 && (
                <div className="mt-1.5">
                  <div className="h-0.5 bg-nexus-dark rounded-full overflow-hidden">
                    <div
                      className="h-full bg-nexus-cyan transition-all"
                      style={{ width: `${item.confidence_score * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
