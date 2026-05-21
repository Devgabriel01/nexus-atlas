import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { scanApi } from '../utils/api'
import { useAppStore } from '../store/useAppStore'

export function useScanPolling() {
  const { activeScanId, pushLog, setActiveScanId } = useAppStore()
  const qc = useQueryClient()
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!activeScanId) return

    const poll = async () => {
      try {
        const res = await scanApi.getStatus(activeScanId)
        const { status, progress, message, anomaly_count } = res.data

        pushLog(`[${activeScanId.slice(0, 8)}] ${status.toUpperCase()} — ${message} (${progress}%)`)

        if (status === 'completed') {
          pushLog(`Scan complete. ${anomaly_count} anomalies detected.`)
          qc.invalidateQueries({ queryKey: ['scans'] })
          qc.invalidateQueries({ queryKey: ['anomalies'] })
          qc.invalidateQueries({ queryKey: ['stats'] })
          qc.invalidateQueries({ queryKey: ['history'] })
          clearInterval(intervalRef.current!)
          intervalRef.current = null
        } else if (status === 'failed') {
          pushLog(`Scan FAILED.`)
          clearInterval(intervalRef.current!)
          intervalRef.current = null
        }
      } catch {
        // polling silently fails if network is down
      }
    }

    intervalRef.current = setInterval(poll, 3000)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [activeScanId, pushLog, qc])
}
