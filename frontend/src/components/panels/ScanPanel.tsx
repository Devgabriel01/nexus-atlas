import { useState } from 'react'
import { motion } from 'framer-motion'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { scanApi } from '../../utils/api'
import { useAppStore } from '../../store/useAppStore'
import toast from 'react-hot-toast'
import { ScanLine, MapPin, Calendar } from 'lucide-react'

export default function ScanPanel() {
  const qc = useQueryClient()
  const { selectedBounds, setSelectedBounds, setScanDrawMode, pushLog, setActiveScanId } = useAppStore()

  const [form, setForm] = useState({
    name: '',
    description: '',
    scan_type: 'full',
    date_start: '2023-01-01',
    date_end: '2024-01-01',
  })

  const mutation = useMutation({
    mutationFn: (data: any) => scanApi.create(data),
    onSuccess: (res) => {
      toast.success(`Scan initiated: ${res.data.id.slice(0, 8)}`)
      pushLog(`Scan launched: ${form.name} [${res.data.id.slice(0, 8)}]`)
      setActiveScanId(res.data.id)
      qc.invalidateQueries({ queryKey: ['scans'] })
      qc.invalidateQueries({ queryKey: ['stats'] })
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || 'Scan failed to start')
    },
  })

  const handleLaunch = () => {
    if (!selectedBounds) {
      toast.error('Select a region on the map first')
      return
    }
    if (!form.name.trim()) {
      toast.error('Scan name required')
      return
    }
    mutation.mutate({ ...form, ...selectedBounds })
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto p-4 space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <ScanLine size={14} className="text-nexus-cyan" />
        <span className="font-mono text-xs text-nexus-cyan tracking-widest uppercase">Scan Configuration</span>
      </div>

      {/* Region selector */}
      <div>
        <label className="nexus-label">Target Region</label>
        <div className="nexus-panel p-3 nexus-border-glow space-y-1">
          {selectedBounds ? (
            <>
              <div className="font-mono text-[10px] text-nexus-green">◆ REGION LOCKED</div>
              <div className="font-mono text-[10px] text-nexus-text">
                N {selectedBounds.lat_max.toFixed(4)}° / S {selectedBounds.lat_min.toFixed(4)}°
              </div>
              <div className="font-mono text-[10px] text-nexus-text">
                E {selectedBounds.lon_max.toFixed(4)}° / W {selectedBounds.lon_min.toFixed(4)}°
              </div>
              <button
                onClick={() => setSelectedBounds(null)}
                className="nexus-btn text-[10px] mt-1 text-nexus-red border-nexus-red"
              >
                CLEAR
              </button>
            </>
          ) : (
            <div className="space-y-2">
              <div className="font-mono text-[10px] text-nexus-muted">No region selected</div>
              <button
                onClick={() => setScanDrawMode(true)}
                className="nexus-btn-primary text-[10px] w-full"
              >
                <MapPin size={10} className="inline mr-1" />
                DRAW ON MAP
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Scan name */}
      <div>
        <label className="nexus-label">Mission Name</label>
        <input
          className="nexus-input"
          placeholder="e.g. AMAZON-WATCH-01"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value.toUpperCase() })}
        />
      </div>

      {/* Scan type */}
      <div>
        <label className="nexus-label">Analysis Mode</label>
        <select
          className="nexus-input"
          value={form.scan_type}
          onChange={(e) => setForm({ ...form, scan_type: e.target.value })}
        >
          <option value="full">FULL SPECTRUM</option>
          <option value="temporal">TEMPORAL CHANGE</option>
          <option value="anomaly">ANOMALY DETECTION</option>
          <option value="ndvi">VEGETATION (NDVI)</option>
          <option value="structure">STRUCTURE ANALYSIS</option>
        </select>
      </div>

      {/* Date range */}
      <div>
        <label className="nexus-label">
          <Calendar size={10} className="inline mr-1" />
          Time Window
        </label>
        <div className="flex gap-2">
          <input
            type="date"
            className="nexus-input text-[11px]"
            value={form.date_start}
            onChange={(e) => setForm({ ...form, date_start: e.target.value })}
          />
          <input
            type="date"
            className="nexus-input text-[11px]"
            value={form.date_end}
            onChange={(e) => setForm({ ...form, date_end: e.target.value })}
          />
        </div>
      </div>

      {/* Description */}
      <div>
        <label className="nexus-label">Notes</label>
        <textarea
          className="nexus-input resize-none"
          rows={3}
          placeholder="Mission briefing..."
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />
      </div>

      {/* Launch button */}
      <motion.button
        onClick={handleLaunch}
        disabled={mutation.isPending}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.97 }}
        className="nexus-btn-primary w-full py-3 text-sm tracking-widest"
      >
        {mutation.isPending ? (
          <span className="animate-pulse">◆ SCANNING...</span>
        ) : (
          '▶ LAUNCH SCAN'
        )}
      </motion.button>
    </div>
  )
}
