# NEXUS ATLAS — System Architecture

## Data Flow

```
User (Browser)
     │
     ▼
React Frontend (Vite/Mapbox)
     │  REST + JWT
     ▼
FastAPI Backend
     ├── Auth Router      → JWT tokens
     ├── Scan Router      → Creates scan, triggers background job
     ├── Anomaly Router   → Query detected anomalies
     ├── Report Router    → Generate + download reports
     ├── Explore Router   → Suggested regions, heatmap, stats
     └── Analyze Router   → NDVI, coordinate analysis
          │
          ├── ScanService (Background Task)
          │     ├── EarthEngineClient  → Sentinel-2 download
          │     ├── SatelliteDetector  → YOLOv8 object detection
          │     └── TemporalAnalyzer   → OpenCV change detection
          │
          └── ReportService (Background Task)
                ├── Anomaly aggregation
                ├── Threat assessment
                ├── JSON export
                └── PDF export (ReportLab)
     │
     ▼
PostgreSQL + PostGIS
     ├── users
     ├── scans
     ├── anomalies
     ├── reports
     └── regions
```

## Scan Pipeline (Detail)

```
POST /scan/
  │
  ├─ Create Scan record (status=PENDING)
  ├─ Return 202 Accepted
  └─ Background Task:
       │
       ├─ [1] EarthEngineClient.download_region()
       │    └── Sentinel-2 SR → GeoTIFF
       │
       ├─ [2] SatelliteDetector.detect()
       │    └── YOLOv8 inference → object list
       │
       ├─ [3] TemporalAnalyzer.analyze()
       │    └── GEE temporal pair → OpenCV diff → contours
       │
       ├─ [4] Persist Anomaly records
       │
       └─ [5] Update Scan (status=COMPLETED, anomaly_count)
```

## Frontend Component Tree

```
App
└── Dashboard
     ├── StatusBar          (top HUD bar)
     ├── LeftNav            (icon sidebar)
     ├── SidePanel (animated)
     │    ├── ScanPanel
     │    ├── AnomaliesPanel
     │    ├── ExplorePanel
     │    ├── ReportsPanel
     │    └── HistoryPanel
     ├── NexusMap           (Mapbox Globe)
     │    ├── Selection box layer
     │    ├── Draw mode layer
     │    └── Anomaly markers
     ├── RadarWidget        (bottom-right)
     ├── CoordDisplay       (bottom-left)
     └── Terminal           (slide-up console)
```

## Security Model

- All API routes (except `/auth/*` and `/health`) require Bearer JWT
- Tokens expire after 24h (configurable)
- Rate limiting: 60 req/min per IP (in-memory, swap Redis for prod)
- CORS restricted to frontend origin
- Passwords hashed with bcrypt
- Input validation via Pydantic v2

## Deployment Notes

- PostgreSQL requires PostGIS extension (`CREATE EXTENSION postgis;`)
- GEE authentication must be completed before scan jobs run
- YOLOv8 model auto-downloads on first use (`~6MB` for nano)
- SAM model requires manual download (`sam_vit_b.pth`, ~375MB)
- Frontend build inlines Mapbox token — use a restricted public token
