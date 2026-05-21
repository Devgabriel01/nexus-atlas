import { motion } from 'framer-motion'
import { useAppStore } from '../../store/useAppStore'
import { useQuery } from '@tanstack/react-query'
import { explorationApi } from '../../utils/api'

export default function StatusBar() {
  const user = useAppStore((s) => s.user)
  const { data } = useQuery({
    queryKey: ['stats'],
    queryFn: () => explorationApi.getStats().then((r) => r.data),
    refetchInterval: 15_000,
  })

  const now = new Date()
  const timeStr = now.toUTCString().slice(17, 25)

  return (
    <div className="h-8 bg-nexus-dark border-b border-nexus-border flex items-center px-4 gap-6 flex-shrink-0">
      {/* Left: brand */}
      <motion.span
        animate={{ opacity: [0.7, 1, 0.7] }}
        transition={{ duration: 4, repeat: Infinity }}
        className="font-mono text-xs text-nexus-cyan text-glow-cyan tracking-widest font-bold"
      >
        NEXUS ATLAS
      </motion.span>

      <div className="flex-1 flex items-center gap-6 overflow-hidden">
        <Stat label="OPERATOR" value={user?.username?.toUpperCase() ?? '---'} />
        <Stat label="SCANS" value={String(data?.total_scans ?? 0)} />
        <Stat label="ANOMALIES" value={String(data?.total_anomalies ?? 0)} color={data?.critical_anomalies ? 'text-nexus-red' : 'text-nexus-green'} />
        <Stat label="CRITICAL" value={String(data?.critical_anomalies ?? 0)} color="text-nexus-red" />
      </div>

      {/* Right: time & status */}
      <div className="flex items-center gap-4">
        <span className="font-mono text-[10px] text-nexus-muted">UTC {timeStr}</span>
        <div className="flex items-center gap-1">
          <motion.div
            animate={{ opacity: [1, 0.3, 1] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="w-1.5 h-1.5 rounded-full bg-nexus-green"
          />
          <span className="font-mono text-[10px] text-nexus-green">ONLINE</span>
        </div>
      </div>
    </div>
  )
}

function Stat({ label, value, color = 'text-nexus-cyan' }: { label: string; value: string; color?: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="font-mono text-[9px] text-nexus-muted uppercase tracking-wider">{label}:</span>
      <span className={`font-mono text-[10px] ${color} font-medium`}>{value}</span>
    </div>
  )
}
