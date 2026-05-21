# NEXUS ATLAS — Roadmap completo entregue

## ✅ 1. WebSocket real-time scan progress

**Status:** funcional, testado

- `backend/app/services/event_bus.py` — pub/sub async em memória
- `backend/app/routers/ws.py` — endpoint `/ws/scans/{scan_id}?token=<JWT>`
- `scan_service.py` agora emite eventos em cada estágio: `started → fetch → ai_detect → temporal → sar → complete`
- Frontend pode consumir via `new WebSocket('ws://.../ws/scans/<id>?token=<jwt>')`

**Para produção (multi-node):** trocar `EventBus` por Redis pub/sub (mesma interface).

## ✅ 2. YOLO satellite-trained

**Status:** scaffolding completo + integração via HuggingFace

- `ai_models/satellite_detector.py` — detector que prefere `weights/yolov8-satellite.pt`, com fallback gracioso para HF/COCO
- `ai_models/train_satellite_yolo.py` — pipeline de treino para RarePlanes, xView, DOTA
- Augmentations específicas pra imagem aérea (rotação 180°, flip vertical, mosaico)

**Como obter o modelo:**

```bash
# Opção A: treinar (precisa GPU, ~$5 em Colab Pro+ ou RunPod)
python ai_models/train_satellite_yolo.py --dataset rareplanes --epochs 100

# Opção B: baixar pré-treinado da comunidade
export SATELLITE_YOLO_HF_REPO=keremberke/yolov8n-satellite-image
# detector vai puxar automático no próximo restart

# Opção C: dropa um .pt já existente
cp seu_modelo.pt ai_models/weights/yolov8-satellite.pt
```

## ✅ 3. Sentinel-1 SAR

**Status:** funcional, baixa GeoTIFF real, detecta mudanças

- `geospatial/sar.py` — `SARAnalyzer` com:
  - `detect_changes()` — log-ratio VV-pol entre 2 janelas temporais → anomalias
  - `flood_extent()` — área inundada via threshold dB
- Novo `ScanType.SAR` e `ScanType.FULL_SAR`
- Pipeline integra SAR opcionalmente quando `scan_type` contém "sar"
- **Bloqueado no plano FREE** — só PRO/ENTERPRISE liberam SAR

**Cobertura testada:** Sentinel-1 GRD IW (banda C, ~10m, VV+VH polarizações), penetra nuvens.

## ✅ 4. Multi-tenancy + Billing

**Status:** completo end-to-end

### Modelos
- `models/organization.py`: `Organization`, `UsageRecord`, `PlanTier` (FREE/PRO/ENTERPRISE)
- `User.organization_id` FK adicionado
- Cotas:

  | Plan | Scans/mo | AI/mo | SAR | Preço |
  |------|----------|-------|-----|-------|
  | FREE | 25 | 100 | ❌ | $0 |
  | PRO  | 500 | 5.000 | ✅ | $49 |
  | ENTERPRISE | ∞ | ∞ | ✅ | $499 |

### Endpoints
- `POST /orgs/` — criar organização
- `GET /orgs/me` — ver plano + uso atual
- `GET /orgs/plans` — listar planos
- `POST /billing/checkout` — gerar Stripe Checkout (mock se sem chave)
- `GET /billing/usage` — counters do mês corrente
- `POST /billing/webhook` — recebe eventos Stripe (assinatura verificada)

### Enforcement
- `enforce_quota(org, kind)` automático em `POST /scan/`
- Resposta 402 com `{error, used, limit, upgrade_url}` quando cota estoura
- `record_usage()` salva cada chamada para auditoria + billing

### Para ativar Stripe real
```env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```
E configure `price_pro_monthly` / `price_enterprise_monthly` no Stripe Dashboard.

## ✅ 5. Deploy: AWS, GCP, Railway, Render, Fly.io

**Status:** todos configs prontos

| Provider | Arquivo | Como deployar |
|----------|---------|---------------|
| **Fly.io** | `fly.toml` | `fly launch && fly secrets set ... && fly deploy` |
| **Railway** | `railway.json` | Conecta repo no painel; deploy automático |
| **Render** | `render.yaml` | Blueprint deploy direto do painel |
| **AWS ECS** | `deploy/terraform/aws/main.tf` | `terraform init && terraform apply` |
| **Kubernetes** | `deploy/helm/nexus-atlas/` | `helm install nexus deploy/helm/nexus-atlas` |
| **CI/CD** | `.github/workflows/{ci,deploy}.yml` | Push → testa → build Docker → deploy |

### Docker prod
- `docker/Dockerfile.backend.prod` — multi-stage, gunicorn+uvicorn workers, GDAL/OpenCV runtime libs, healthcheck
- `docker/Dockerfile.frontend.prod` — Vite build → nginx static, cache headers, gzip, security headers

### Quick start AWS (~$80/mês)
```bash
cd deploy/terraform/aws
terraform init -backend-config="bucket=meu-state-bucket"
terraform apply -var="groq_api_key=gsk_..." \
                -var="image_backend=ghcr.io/seu/nexus-atlas/backend:latest"
```

Provisiona: VPC + RDS PostgreSQL+PostGIS + ECS Fargate + ALB + S3+CloudFront pro frontend + Secrets Manager + IAM.

### Quick start Railway (~$5/mês)
```bash
railway link
railway up
railway variables set GROQ_API_KEY=gsk_... GEE_PROJECT=... SECRET_KEY=...
```

### Quick start Fly.io grátis
```bash
fly launch --copy-config
fly secrets set GROQ_API_KEY=gsk_...
fly deploy
```

## 📊 Resumo de arquivos criados nesta sessão

- **Backend (Python):** 35+ módulos, 6 routers, services, models, middleware
- **Frontend (React/TS):** dashboard cyberpunk completo
- **Geospatial:** earth_engine.py + sar.py + temporal.py + ndvi.py
- **AI:** detector.py + satellite_detector.py + train_satellite_yolo.py
- **DevOps:** 5 deploy targets, 2 Dockerfiles prod, Helm chart, Terraform AWS
- **CI/CD:** GitHub Actions com test → build → push → deploy multi-target

**Total: ~78 arquivos de configuração/código de infra entregues prontos pra rodar.**
