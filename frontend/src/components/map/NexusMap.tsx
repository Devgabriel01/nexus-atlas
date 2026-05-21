import { useRef, useCallback, useState } from 'react'
import Map, { Source, Layer, Marker } from 'react-map-gl'
import type { MapRef, MapLayerMouseEvent } from 'react-map-gl'
import { useAppStore } from '../../store/useAppStore'
import { useQuery } from '@tanstack/react-query'
import { anomalyApi } from '../../utils/api'
import 'mapbox-gl/dist/mapbox-gl.css'

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN || ''

const DARK_STYLE = 'mapbox://styles/mapbox/dark-v11'
const SATELLITE_STYLE = 'mapbox://styles/mapbox/satellite-streets-v12'

export default function NexusMap() {
  const mapRef = useRef<MapRef>(null)
  const {
    mapView, mapCenter, mapZoom, setMapCenter, setMapZoom,
    selectedBounds, setSelectedBounds, scanDrawMode, setScanDrawMode,
    pushLog,
  } = useAppStore()

  const [drawStart, setDrawStart] = useState<[number, number] | null>(null)
  const [drawCurrent, setDrawCurrent] = useState<[number, number] | null>(null)

  const { data: anomalies } = useQuery({
    queryKey: ['anomalies-map'],
    queryFn: () => anomalyApi.list({ limit: 200 }).then((r) => r.data),
    refetchInterval: 30_000,
  })

  const mapStyle = mapView === 'satellite' ? SATELLITE_STYLE : DARK_STYLE

  const handleClick = useCallback(
    (e: MapLayerMouseEvent) => {
      if (!scanDrawMode) return
      const { lng, lat } = e.lngLat

      if (!drawStart) {
        setDrawStart([lng, lat])
        setDrawCurrent([lng, lat])
        pushLog(`Draw start: [${lat.toFixed(4)}, ${lng.toFixed(4)}]`)
      } else {
        const bounds = {
          lat_min: Math.min(drawStart[1], lat),
          lat_max: Math.max(drawStart[1], lat),
          lon_min: Math.min(drawStart[0], lng),
          lon_max: Math.max(drawStart[0], lng),
        }
        setSelectedBounds(bounds)
        setDrawStart(null)
        setDrawCurrent(null)
        setScanDrawMode(false)
        pushLog(`Region selected: [${bounds.lat_min.toFixed(3)}, ${bounds.lon_min.toFixed(3)}] → [${bounds.lat_max.toFixed(3)}, ${bounds.lon_max.toFixed(3)}]`)
      }
    },
    [scanDrawMode, drawStart, pushLog, setSelectedBounds, setScanDrawMode]
  )

  const handleMouseMove = useCallback(
    (e: MapLayerMouseEvent) => {
      if (drawStart) setDrawCurrent([e.lngLat.lng, e.lngLat.lat])
    },
    [drawStart]
  )

  // Build selection box GeoJSON
  const selectionBox = selectedBounds
    ? {
        type: 'Feature' as const,
        geometry: {
          type: 'Polygon' as const,
          coordinates: [[
            [selectedBounds.lon_min, selectedBounds.lat_min],
            [selectedBounds.lon_max, selectedBounds.lat_min],
            [selectedBounds.lon_max, selectedBounds.lat_max],
            [selectedBounds.lon_min, selectedBounds.lat_max],
            [selectedBounds.lon_min, selectedBounds.lat_min],
          ]],
        },
        properties: {},
      }
    : null

  const drawBox =
    drawStart && drawCurrent
      ? {
          type: 'Feature' as const,
          geometry: {
            type: 'Polygon' as const,
            coordinates: [[
              drawStart,
              [drawCurrent[0], drawStart[1]],
              drawCurrent,
              [drawStart[0], drawCurrent[1]],
              drawStart,
            ]],
          },
          properties: {},
        }
      : null

  if (!MAPBOX_TOKEN) {
    return (
      <div className="flex-1 flex items-center justify-center bg-nexus-dark grid-bg relative">
        <div className="text-center">
          <div className="text-nexus-cyan font-mono text-lg mb-2">MAP OFFLINE</div>
          <div className="text-nexus-muted font-mono text-xs">
            Set VITE_MAPBOX_TOKEN in .env to enable interactive map
          </div>
        </div>
        {/* Decorative grid lines */}
        <div className="absolute inset-0 pointer-events-none opacity-20">
          {Array.from({ length: 10 }).map((_, i) => (
            <div
              key={i}
              className="absolute top-0 bottom-0 border-l border-nexus-cyan/10"
              style={{ left: `${i * 10}%` }}
            />
          ))}
          {Array.from({ length: 10 }).map((_, i) => (
            <div
              key={i}
              className="absolute left-0 right-0 border-t border-nexus-cyan/10"
              style={{ top: `${i * 10}%` }}
            />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 relative" style={{ cursor: scanDrawMode ? 'crosshair' : 'default' }}>
      <Map
        ref={mapRef}
        mapboxAccessToken={MAPBOX_TOKEN}
        style={{ width: '100%', height: '100%' }}
        mapStyle={mapStyle}
        initialViewState={{ longitude: mapCenter[0], latitude: mapCenter[1], zoom: mapZoom }}
        onMove={(e) => {
          setMapCenter([e.viewState.longitude, e.viewState.latitude])
          setMapZoom(e.viewState.zoom)
        }}
        onClick={handleClick}
        onMouseMove={handleMouseMove}
        projection={{ name: 'globe' }}
        fog={{}}
      >
        {/* Selection rectangle */}
        {selectionBox && (
          <Source id="selection" type="geojson" data={selectionBox}>
            <Layer
              id="selection-fill"
              type="fill"
              paint={{ 'fill-color': '#00d4ff', 'fill-opacity': 0.1 }}
            />
            <Layer
              id="selection-border"
              type="line"
              paint={{ 'line-color': '#00d4ff', 'line-width': 2, 'line-dasharray': [4, 2] }}
            />
          </Source>
        )}

        {/* Active draw box */}
        {drawBox && (
          <Source id="draw-box" type="geojson" data={drawBox}>
            <Layer
              id="draw-fill"
              type="fill"
              paint={{ 'fill-color': '#00ff88', 'fill-opacity': 0.08 }}
            />
            <Layer
              id="draw-border"
              type="line"
              paint={{ 'line-color': '#00ff88', 'line-width': 1.5, 'line-dasharray': [3, 2] }}
            />
          </Source>
        )}

        {/* Anomaly markers */}
        {anomalies?.map((a: any) => (
          <Marker key={a.id} longitude={a.longitude} latitude={a.latitude} anchor="center">
            <div
              className={`w-3 h-3 rounded-full border-2 cursor-pointer transition-transform hover:scale-150 ${
                a.severity === 'critical' ? 'bg-nexus-red border-nexus-red shadow-nexus-red' :
                a.severity === 'high' ? 'bg-nexus-orange border-nexus-orange' :
                a.severity === 'medium' ? 'bg-yellow-400 border-yellow-400' :
                'bg-nexus-green border-nexus-green'
              }`}
              title={`${a.anomaly_type} — ${a.severity}`}
            />
          </Marker>
        ))}
      </Map>

      {/* Draw mode overlay hint */}
      {scanDrawMode && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 nexus-panel px-4 py-2 nexus-border-glow z-10">
          <span className="font-mono text-xs text-nexus-green animate-pulse">
            ◆ CLICK TO SET POINT 1 — CLICK AGAIN TO COMPLETE REGION
          </span>
        </div>
      )}
    </div>
  )
}
