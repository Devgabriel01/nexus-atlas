import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type MapView = 'satellite' | 'terrain' | 'dark'
export type SidePanel = 'scan' | 'anomalies' | 'reports' | 'explore' | 'history' | null

interface Bounds {
  lat_min: number
  lat_max: number
  lon_min: number
  lon_max: number
}

interface User {
  id: string
  email: string
  username: string
  role: string
}

interface AppState {
  // Auth
  token: string | null
  user: User | null
  setAuth: (token: string, user: User) => void
  logout: () => void

  // Map
  mapView: MapView
  setMapView: (v: MapView) => void
  selectedBounds: Bounds | null
  setSelectedBounds: (b: Bounds | null) => void
  mapCenter: [number, number]
  setMapCenter: (c: [number, number]) => void
  mapZoom: number
  setMapZoom: (z: number) => void

  // UI
  activePanel: SidePanel
  setActivePanel: (p: SidePanel) => void
  terminalOpen: boolean
  setTerminalOpen: (v: boolean) => void
  terminalLogs: string[]
  pushLog: (msg: string) => void
  clearLogs: () => void

  // Active scan
  activeScanId: string | null
  setActiveScanId: (id: string | null) => void
  scanDrawMode: boolean
  setScanDrawMode: (v: boolean) => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      setAuth: (token, user) => {
        localStorage.setItem('nexus_token', token)
        set({ token, user })
      },
      logout: () => {
        localStorage.removeItem('nexus_token')
        set({ token: null, user: null })
      },

      mapView: 'dark',
      setMapView: (v) => set({ mapView: v }),
      selectedBounds: null,
      setSelectedBounds: (b) => set({ selectedBounds: b }),
      mapCenter: [0, 20],
      setMapCenter: (c) => set({ mapCenter: c }),
      mapZoom: 2,
      setMapZoom: (z) => set({ mapZoom: z }),

      activePanel: null,
      setActivePanel: (p) => set({ activePanel: p }),
      terminalOpen: false,
      setTerminalOpen: (v) => set({ terminalOpen: v }),
      terminalLogs: [
        '> NEXUS ATLAS v1.0 initialized',
        '> Geospatial systems online',
        '> AI modules loaded',
        '> Awaiting operator input...',
      ],
      pushLog: (msg) =>
        set((s) => ({
          terminalLogs: [
            ...s.terminalLogs.slice(-99),
            `> [${new Date().toISOString().slice(11, 19)}] ${msg}`,
          ],
        })),
      clearLogs: () => set({ terminalLogs: [] }),

      activeScanId: null,
      setActiveScanId: (id) => set({ activeScanId: id }),
      scanDrawMode: false,
      setScanDrawMode: (v) => set({ scanDrawMode: v }),
    }),
    {
      name: 'nexus-atlas-store',
      partialize: (s) => ({ token: s.token, user: s.user, mapView: s.mapView }),
    }
  )
)
