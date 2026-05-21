import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { anomalyApi } from '../../utils/api'
import { AlertTriangle, MapPin } from 'lucide-react'
import { useAppStore } from '../../store/useAppStore'

const SEVERITY_COLOR: Record<string, string> = {
  critical: 'text-nexus-red',
  high: 'text-nexus-orange',
  medium: 'text-yellow-400',
  low: 'text-nexus-green',
}

export default function AnomaliesPanel() {
  const { activeScanId, setMapCenter, setMapZoom } = useAppStore()

  const { data: anomalies = [], isLoading } = useQuery({
    queryKey: ['anomalies', activeScanId],
    queryFn: () =>
      anomalyApi
        .list(activeScanId ? { scan_id: activeScanId, limit: 100 } : { limit: 100 })
        .then((r) => r.data),
    refetchInterval: 10_000,
  })

  const handleLocate = (a: any) => {
    setMapCenter([a.longitude, a.latitude])
    setMapZoom(12)
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-nexus-border">
        <AlertTriangle size={14} className="text-nexus-orange" />
        <span className="font-mono text-xs text-nexus-cyan tracking-widest uppercase">Anomaly Detection</span>
        <span className="ml-auto font-mono text-xs text-nexus-muted">{anomalies.length} found</span>
      </div>

      {isLoading ? (
        <div className="flex-1 flex items-center justify-center">
          <span className="font-mono text-xs text-nexus-cyan animate-pulse">SCANNING...</span>
        </div>
      ) : anomalies.length === 0 ? (
        <div className="flex-1 flex items-center justify-center text-center px-4">
          <div>
            <div className="text-nexus-muted font-mono text-xs">NO ANOMALIES DETECTED</div>
            <div className="text-nexus-muted/50 font-mono text-[10px] mt-1">Launch a scan to begin analysis</div>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-1 p-2">
          {anomalies.map((a: any, i: number) => (
            <motion.div
              key={a.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.03 }}
              className="nexus-panel p-3 cursor-pointer hover:nexus-border-glow transition-all"
              onClick={() => handleLocate(a)}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`font-mono text-[10px] uppercase font-bold ${SEVERITY_COLOR[a.severity] || 'text-nexus-text'}`}>
                      [{a.severity}]
                    </span>
                    <span className="font-mono text-[10px] text-nexus-text truncate">
                      {a.anomaly_type.replace(/_/g, ' ')}
                    </span>
                  </div>
                  {a.description && (
                    <div className="font-mono text-[9px] text-nexus-muted mt-0.5 truncate">{a.description}</div>
                  )}
                  <div className="font-mono text-[9px] text-nexus-muted/60 mt-0.5">
                    {a.latitude.toFixed(4)}°, {a.longitude.toFixed(4)}°
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <div className="font-mono text-[9px] text-nexus-cyan">
                    {(a.confidence * 100).toFixed(0)}%
                  </div>
                  <MapPin size={10} className="text-nexus-muted" />
                </div>
              </div>
              {a.ai_interpretation && (
                <div className="mt-2 pt-2 border-t border-nexus-border/50">
                  <div className="font-mono text-[9px] text-nexus-green/80 leading-relaxed line-clamp-2">
                    ◆ {a.ai_interpretation}
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
