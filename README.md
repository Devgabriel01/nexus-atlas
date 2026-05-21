# NEXUS ATLAS
### Advanced Geospatial Intelligence Platform

```
  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗
  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝
  ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗
  ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║
  ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║
  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
                      A T L A S
```

> Multi-spectral satellite analysis · AI anomaly detection · Temporal change tracking

---

## Overview

NEXUS ATLAS is a full-stack geospatial intelligence platform that combines:

- **Satellite imagery** from Google Earth Engine (Sentinel-2, Landsat)
- **AI detection** via YOLOv8 object recognition
- **Temporal analysis** — before/after change detection using OpenCV
- **NDVI computation** for vegetation and environmental monitoring
- **Cyberpunk dashboard** built with React, Mapbox GL and Framer Motion
- **Automated reports** exported as PDF and JSON

---

## Architecture

```
nexus-atlas/
├── backend/          FastAPI · SQLAlchemy · PostGIS · JWT
├── frontend/         React · TypeScript · Vite · Tailwind · Mapbox
├── ai_models/        YOLOv8 · Segment Anything · GeospatialAnalyzer
├── geospatial/       Earth Engine · NDVI · Temporal · Heatmap
├── database/         PostgreSQL init · Alembic migrations
├── scripts/          install.sh · setup_db.py
├── tests/            pytest (backend) · Vitest (frontend)
└── docker-compose.yml
```

---

## Quick Start (Docker)

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your Mapbox token and GEE credentials

# 2. Start everything
docker-compose up --build

# 3. Access
#   Frontend:   http://localhost:3000
#   API Docs:   http://localhost:8000/docs
#   Default user: admin@nexus.local / nexus2024
```

---

## Local Development

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 16 with PostGIS extension
- Docker (optional)

### Backend

```bash
cd backend
pip install -r requirements.txt

# Configure database
cp ../.env.example ../.env
# Edit .env

# Initialize DB + seed data
python ../scripts/setup_db.py

# Run
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
cp .env.example .env
# Add your Mapbox public token to VITE_MAPBOX_TOKEN

npm install
npm run dev
# → http://localhost:5173
```

---

## Google Earth Engine Setup

**Option 1 — Personal auth (development)**
```bash
pip install earthengine-api
earthengine authenticate
# Set GEE_PROJECT in .env
```

**Option 2 — Service Account (production)**
1. Create a GEE service account in Google Cloud Console
2. Download the JSON key
3. Set in `.env`:
```env
GEE_SERVICE_ACCOUNT=your-sa@project.iam.gserviceaccount.com
GEE_KEY_FILE=./gee_credentials.json
GEE_PROJECT=your-project-id
```

> Without GEE credentials, the system runs in **mock mode** — all API features still work, scans return empty image results.

---

## Mapbox Setup

1. Create a free account at [mapbox.com](https://mapbox.com)
2. Copy your **public token**
3. Set `VITE_MAPBOX_TOKEN=pk.xxx` in `frontend/.env`

> Without a Mapbox token, the map renders a decorative offline grid — all other features remain functional.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create operator account |
| POST | `/auth/login` | Authenticate, get JWT |
| POST | `/scan/` | Launch new geospatial scan |
| GET | `/scan/` | List all scans |
| GET | `/scan/{id}/status` | Poll scan progress |
| GET | `/anomalies/` | List detected anomalies |
| POST | `/reports/` | Generate intelligence report |
| GET | `/reports/{id}/download/pdf` | Download PDF report |
| GET | `/exploration/suggested-regions` | AI-curated regions |
| GET | `/exploration/stats` | Dashboard statistics |
| POST | `/analyze/coordinates` | Quick coordinate analysis |
| POST | `/analyze/ndvi` | Compute vegetation index |
| GET | `/history/` | Mission history |

Full interactive docs: `http://localhost:8000/docs`

---

## Features

### Scan Pipeline
1. User draws a bounding box on the 3D map
2. System fetches Sentinel-2 imagery from GEE
3. YOLOv8 detects objects (structures, ships, runways, vehicles)
4. Temporal analysis compares before/after imagery
5. Anomalies are geo-referenced and severity-scored
6. Report generated as PDF + JSON

### AI Modules
- **YOLOv8** — real-time object detection on satellite imagery
- **Segment Anything** — geographic region segmentation
- **OpenCV** — temporal change detection via image differencing
- **NDVI** — vegetation health and deforestation monitoring

### Dashboard
- Cyberpunk/HUD aesthetic with dark glass panels
- Interactive 3D globe (Mapbox)
- Live anomaly markers with severity color coding
- Real-time radar widget
- Console terminal with mission logs
- Side panels: Scan, Anomalies, Explore, Reports, History

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing key |
| `GEE_PROJECT` | Google Earth Engine project ID |
| `GEE_SERVICE_ACCOUNT` | GEE service account email |
| `GEE_KEY_FILE` | Path to GEE credentials JSON |
| `VITE_MAPBOX_TOKEN` | Mapbox public token (frontend) |
| `OPENAI_API_KEY` | Optional — AI report enhancement |
| `RATE_LIMIT_PER_MINUTE` | API rate limit (default: 60) |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python · FastAPI · SQLAlchemy · asyncpg |
| Database | PostgreSQL 16 · PostGIS · Alembic |
| Auth | JWT · bcrypt · python-jose |
| Geospatial | Google Earth Engine · rasterio · geopandas · geemap |
| AI/CV | YOLOv8 · Segment Anything · OpenCV · NumPy |
| Reports | ReportLab (PDF) |
| Frontend | React 18 · TypeScript · Vite · Tailwind CSS |
| Maps | Mapbox GL JS · react-map-gl |
| State | Zustand · React Query |
| Animation | Framer Motion |
| DevOps | Docker · Docker Compose · Make |

---

## License

MIT — Use freely, attribution appreciated.

---

*NEXUS ATLAS — See everything. Miss nothing.*
