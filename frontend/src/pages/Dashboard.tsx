import { motion, AnimatePresence } from 'framer-motion'
import { useAppStore } from '../store/useAppStore'
import StatusBar from '../components/ui/StatusBar'
import NexusMap from '../components/map/NexusMap'
import Terminal from '../components/ui/Terminal'
import RadarWidget from '../components/ui/RadarWidget'
import ScanPanel from '../components/panels/ScanPanel'
import AnomaliesPanel from '../components/panels/AnomaliesPanel'
import HistoryPanel from '../components/panels/HistoryPanel'
import ExplorePanel from '../components/panels/ExplorePanel'
import ReportsPanel from '../components/panels/ReportsPanel'
import { useQuery } from '@tanstack/react-query'
import { explorationApi } from '../utils/api'
import {
  ScanLine, AlertTriangle, Clock, Globe, FileText,
  Terminal as TerminalIcon, LogOut, Map, Satellite, Moon,
} from 'lucide-react'
import type { SidePanel } from '../store/useAppStore'

const NAV_ITEMS: { id: SidePanel; label: string; icon: React.ReactNode }[] = [
  { id: 'scan', label: 'SCAN', icon: <ScanLine size={16} /> },
  { id: 'anomalies', label: 'ANOMALIES', icon: <AlertTriangle size={16} /> },
  { id: 'explore', label: 'EXPLORE', icon: <Globe size={16} /> },
  { id: 'reports', label: 'REPORTS', icon: <FileText size={16} /> },
  { id: 'history', label: 'HISTORY', icon: <Clock size={16} /> },
]

const MAP_VIEWS = [
  { id: 'dark' as const, icon: <Moon size={12} />, label: 'DARK' },
  { id: 'satellite' as const, icon: <Satellite size={12} />, label: 'SAT' },
]

const PANEL_COMPONENTS: Record<string, React.ReactNode> = {
  scan: <ScanPanel />,
  anomalies: <AnomaliesPanel />,
  explore: <ExplorePanel />,
  reports: <ReportsPanel />,
  history: <HistoryPanel />,
}

export default function Dashboard() {
  const {
    activePanel, setActivePanel,
    mapView, setMapView,
    terminalOpen, setTerminalOpen,
    logout, user,
  } = useAppStore()

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => explorationApi.getStats().then((r) => r.data),
    refetchInterval: 30_000,
  })

  return (
    <div className="flex flex-col h-screen bg-nexus-black overflow-hidden">
      {/* Top status bar */}
      <StatusBar />

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar — navigation */}
        <div className="w-14 bg-nexus-dark border-r border-nexus-border flex flex-col items-center py-3 gap-1 z-10">
          {NAV_ITEMS.map((item) => (
            <motion.button
              key={item.id}
              onClick={() => setActivePanel(activePanel === item.id ? null : item.id)}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              title={item.label}
              className={`w-10 h-10 rounded flex items-center justify-center transition-all duration-200 ${
                activePanel === item.id
                  ? 'bg-nexus-cyan/15 text-nexus-cyan shadow-nexus-cyan border border-nexus-cyan/30'
                  : 'text-nexus-muted hover:text-nexus-text hover:bg-nexus-panel'
              }`}
            >
              {item.icon}
            </motion.button>
          ))}

          <div className="flex-1" />

          {/* Map view toggles */}
          <div className="space-y-1 mb-2">
            {MAP_VIEWS.map((v) => (
              <button
                key={v.id}
                onClick={() => setMapView(v.id)}
                title={v.label}
                className={`w-10 h-10 rounded flex items-center justify-center transition-all ${
                  mapView === v.id ? 'text-nexus-cyan bg-nexus-cyan/10' : 'text-nexus-muted hover:text-nexus-text'
                }`}
              >
                {v.icon}
              </button>
            ))}
          </div>

          {/* Terminal toggle */}
          <button
            onClick={() => setTerminalOpen(!terminalOpen)}
            title="CONSOLE"
            className={`w-10 h-10 rounded flex items-center justify-center transition-all ${
              terminalOpen ? 'text-nexus-green bg-nexus-green/10' : 'text-nexus-muted hover:text-nexus-text'
            }`}
          >
            <TerminalIcon size={16} />
          </button>

          {/* Logout */}
          <button
            onClick={logout}
            title="LOGOUT"
            className="w-10 h-10 rounded flex items-center justify-center text-nexus-muted hover:text-nexus-red transition-colors mt-1"
          >
            <LogOut size={16} />
          </button>
        </div>

        {/* Side panel */}
        <AnimatePresence>
          {activePanel && (
            <motion.div
              key={activePanel}
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 300, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 400, damping: 35 }}
              className="bg-nexus-panel border-r border-nexus-border overflow-hidden flex-shrink-0"
            >
              <div className="w-[300px] h-full flex flex-col">
                {PANEL_COMPONENTS[activePanel]}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Map area */}
        <div className="flex-1 relative flex flex-col overflow-hidden">
          <NexusMap />

          {/* Bottom overlay: radar + stats */}
          <div className="absolute bottom-4 right-4 flex flex-col items-end gap-2 pointer-events-none z-10">
            {/* Stats mini cards */}
            <div className="flex gap-2">
              <MiniStat label="SCANS" value={stats?.total_scans ?? 0} />
              <MiniStat label="ANOMALIES" value={stats?.total_anomalies ?? 0} alert={stats?.critical_anomalies > 0} />
            </div>

            {/* Radar */}
            <div className="nexus-panel p-3 nexus-border-glow pointer-events-auto">
              <div className="font-mono text-[9px] text-nexus-muted mb-1 text-center">RADAR</div>
              <RadarWidget anomalyCount={stats?.total_anomalies ?? 0} />
            </div>
          </div>

          {/* Coordinate display */}
          <CoordDisplay />

          {/* Terminal */}
          <Terminal />
        </div>
      </div>
    </div>
  )
}

function MiniStat({ label, value, alert = false }: { label: string; value: number; alert?: boolean }) {
  return (
    <div className="nexus-panel px-3 py-2 text-center min-w-[60px]">
      <div className={`font-mono text-base font-bold ${alert ? 'text-nexus-red text-glow-red' : 'text-nexus-cyan text-glow-cyan'}`}>
        {value}
      </div>
      <div className="font-mono text-[9px] text-nexus-muted uppercase">{label}</div>
    </div>
  )
}

function CoordDisplay() {
  const { mapCenter, mapZoom } = useAppStore()
  return (
    <div className="absolute bottom-4 left-4 nexus-panel px-3 py-2 pointer-events-none z-10">
      <div className="font-mono text-[10px] text-nexus-cyan/70 space-y-0.5">
        <div>LAT: {mapCenter[1].toFixed(4)}°</div>
        <div>LON: {mapCenter[0].toFixed(4)}°</div>
        <div>ZOOM: {mapZoom.toFixed(1)}</div>
      </div>
    </div>
  )
}
