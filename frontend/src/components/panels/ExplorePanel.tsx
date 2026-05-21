import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { explorationApi } from '../../utils/api'
import { useAppStore } from '../../store/useAppStore'
import { Globe, Zap } from 'lucide-react'

const CATEGORY_COLOR: Record<string, string> = {
  forest: 'text-nexus-green',
  arctic: 'text-blue-300',
  desert: 'text-yellow-400',
  ocean: 'text-nexus-cyan',
  urban: 'text-nexus-purple',
}

const WATCH_COLOR: Record<string, string> = {
  high: 'text-nexus-orange',
  medium: 'text-yellow-400',
  normal: 'text-nexus-green',
}

export default function ExplorePanel() {
  const { setSelectedBounds, setMapCenter, setMapZoom } = useAppStore()

  const { data: regions = [] } = useQuery({
    queryKey: ['suggested-regions'],
    queryFn: () => explorationApi.getSuggestedRegions().then((r) => r.data),
  })

  const handleRegion = (region: any) => {
    const bounds = region.bounds
    setSelectedBounds(bounds)
    setMapCenter([
      (bounds.lon_min + bounds.lon_max) / 2,
      (bounds.lat_min + bounds.lat_max) / 2,
    ])
    setMapZoom(6)
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-nexus-border">
        <Globe size={14} className="text-nexus-cyan" />
        <span className="font-mono text-xs text-nexus-cyan tracking-widest uppercase">Explore Regions</span>
      </div>

      <div className="px-4 py-2 border-b border-nexus-border">
        <div className="font-mono text-[10px] text-nexus-muted">
          ◆ AI-CURATED REGIONS OF INTEREST
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-1 p-2">
        {regions.map((region: any, i: number) => (
          <motion.div
            key={region.id}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            onClick={() => handleRegion(region)}
            className="nexus-panel p-3 cursor-pointer hover:nexus-border-glow transition-all"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="font-mono text-[10px] text-nexus-text font-medium truncate">
                  {region.name}
                </div>
                {region.description && (
                  <div className="font-mono text-[9px] text-nexus-muted mt-0.5 line-clamp-1">
                    {region.description}
                  </div>
                )}
                <div className="flex items-center gap-2 mt-1">
                  <span className={`font-mono text-[9px] uppercase ${CATEGORY_COLOR[region.category] || 'text-nexus-text'}`}>
                    {region.category}
                  </span>
                  <span className={`font-mono text-[9px] uppercase ${WATCH_COLOR[region.watch_level] || 'text-nexus-text'}`}>
                    ◆ {region.watch_level}
                  </span>
                </div>
              </div>
              <Zap size={12} className="text-nexus-cyan/50 flex-shrink-0 mt-0.5" />
            </div>
          </motion.div>
        ))}

        {regions.length === 0 && (
          <div className="flex items-center justify-center h-32">
            <span className="font-mono text-xs text-nexus-muted">NO REGIONS LOADED</span>
          </div>
        )}
      </div>
    </div>
  )
}
