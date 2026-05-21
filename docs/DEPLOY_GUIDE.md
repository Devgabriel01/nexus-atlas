# NEXUS ATLAS — Deploy Guide

Tudo do projeto local está **pronto para subir em produção**. Esta página lista o comando exato para cada provedor — você só precisa autenticar uma vez no CLI e rodar.

## 📦 O que está pronto

- ✅ Backend Docker prod (multi-stage, gunicorn + uvicorn workers)
- ✅ Frontend Docker prod (nginx static)
- ✅ Configs para Fly.io, Railway, Render, AWS, Kubernetes
- ✅ CI/CD GitHub Actions
- ✅ Repositório git iniciado (108 arquivos no commit inicial)

---

## 🚀 Caminho 1 — GitHub + Render (mais fácil, totalmente grátis)

### 1. Cria o repositório GitHub

```powershell
gh auth login       # abre browser, sign in com sua conta GitHub
gh repo create nexus-atlas --private --source=. --remote=origin --push
```

### 2. Deploy no Render (clica-e-deploya)

1. Acessa https://dashboard.render.com/select-repo?type=blueprint
2. Conecta o repositório `nexus-atlas`
3. Render detecta automaticamente o `render.yaml` na raiz e provisiona:
   - **PostgreSQL** com PostGIS (tier grátis 90 dias)
   - **Backend** (Docker, healthcheck em `/health`)
   - **Frontend** (static site com SPA routes)
4. Adiciona os 2 secrets no Render Dashboard:
   - `GROQ_API_KEY` = sua chave Groq
   - `VITE_MAPBOX_TOKEN` = sua chave Mapbox

**Resultado:** stack em `https://nexus-atlas-frontend.onrender.com` + `https://nexus-atlas-backend.onrender.com`

**Custo:** $0/mês nos primeiros 90 dias, depois ~$7/mês (web service starter).

---

## 🚀 Caminho 2 — Fly.io (mais rápido pra CLI puro)

```powershell
# 1. Autentica
flyctl auth signup    # ou: flyctl auth login

# 2. Subir backend
flyctl launch --copy-config --name nexus-atlas --region gru
# (responde 'no' pro Postgres se for usar SQLite, 'yes' pra criar PG cluster)

# 3. Setar secrets
flyctl secrets set `
  GROQ_API_KEY=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 `
  GEE_PROJECT=project-67cfbe40-3c3a-43bd-98e `
  SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))")

# 4. Deploy
flyctl deploy

# 5. (opcional) Frontend separado
cd frontend
flyctl launch --copy-config --name nexus-atlas-web
```

**URL:** `https://nexus-atlas.fly.dev`
**Custo:** ~$0–5/mês (free tier inclui 3 VMs shared-cpu-1x 256MB, db grátis até 1GB)

---

## 🚀 Caminho 3 — Railway (interface)

```powershell
# CLI já instalado neste projeto
railway login         # abre browser
railway init          # cria projeto novo
railway add postgres  # adiciona Postgres
railway up            # builda + deploya backend
railway domain        # gera URL pública
```

Setar variáveis pelo painel Railway:
- `GROQ_API_KEY`, `GEE_PROJECT`, `SECRET_KEY`, `DATABASE_URL` (auto-injetada se usar Postgres add-on)

**Custo:** $5/mês inclui 500h CPU + db.

---

## 🚀 Caminho 4 — AWS (produção séria)

Pré-requisitos:
- Conta AWS com credenciais (`~/.aws/credentials`)
- Terraform 1.5+ instalado
- Bucket S3 para state (qualquer nome único)

```powershell
cd deploy/terraform/aws

# 1. Init backend
terraform init -backend-config="bucket=meu-tf-state-12345" `
               -backend-config="region=sa-east-1"

# 2. Apply (provisiona TUDO)
terraform apply `
  -var="groq_api_key=gsk_..." `
  -var="gee_project=project-67cfbe40-..." `
  -var="image_backend=ghcr.io/devgabriel01/nexus-atlas/backend:latest" `
  -auto-approve

# Saída: ALB DNS + CloudFront URL + DB endpoint
```

**O que provisiona:**
- VPC + subnets (2 AZs) + NAT Gateway
- RDS PostgreSQL 16 + PostGIS (db.t4g.small, 50 GB gp3, encrypted, backups 14 dias)
- ECS Fargate cluster (2 tasks, 1 vCPU, 2 GB RAM cada)
- ALB com health checks em `/health`
- S3 + CloudFront para o frontend
- Secrets Manager para todas as chaves
- CloudWatch Logs (30 dias retention)
- IAM roles least-privilege

**Custo estimado:** ~$80/mês

---

## 🚀 Caminho 5 — Kubernetes (qualquer provider)

```powershell
helm install nexus `
  ./deploy/helm/nexus-atlas `
  --namespace nexus `
  --create-namespace `
  --set image.backend.repository=ghcr.io/devgabriel01/nexus-atlas/backend `
  --set image.backend.tag=latest `
  --set secrets.existingSecret=nexus-atlas-secrets

# Cria o secret antes:
kubectl create secret generic nexus-atlas-secrets `
  --namespace nexus `
  --from-literal=SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(48))") `
  --from-literal=GROQ_API_KEY=gsk_... `
  --from-literal=GEE_PROJECT=project-... `
  --from-literal=DATABASE_URL=postgresql://...
```

Helm chart inclui: HPA (auto-scaling 2-10 pods), Ingress com cert-manager (Let's Encrypt), PostgreSQL+PostGIS sub-chart.

---

## 🤖 CI/CD automático (após push pro GitHub)

`.github/workflows/ci.yml` roda automaticamente:
1. Lint (ruff) backend
2. Pytest com PostgreSQL+PostGIS de teste
3. Typecheck + build frontend
4. **Apenas no `main`:** build & push imagens Docker pro GitHub Container Registry

`.github/workflows/deploy.yml` (manual ou push):
- Deploy automático pra Fly.io
- Trigger Render deploy (via API key)
- Push pra Railway

**Secrets necessárias no GitHub:**
| Secret | Where |
|--------|-------|
| `FLY_API_TOKEN` | https://fly.io/user/personal_access_tokens |
| `RENDER_API_KEY` | https://dashboard.render.com/account/api-keys |
| `RAILWAY_TOKEN` | https://railway.app/account/tokens |
| `VITE_MAPBOX_TOKEN` | seu token pk.eyJ... |

---

## 🎯 Recomendação rápida

| Cenário | Use |
|---------|-----|
| MVP / Demo | **Render** (1 clique, free 90 dias) |
| Lançar SaaS rápido | **Fly.io** (gru region — São Paulo) |
| Empresa / compliance | **AWS via Terraform** |
| Time grande / k8s já existente | **Helm chart** |

---

## ✅ Pré-flight checklist antes de qualquer deploy

- [ ] `git add -A && git commit -m "..." && git push origin main`
- [ ] Variáveis críticas geradas:
  - [ ] `SECRET_KEY` (64 chars aleatórias)
  - [ ] `GROQ_API_KEY` (obtido de console.groq.com)
  - [ ] `GEE_PROJECT` (do Google Cloud)
- [ ] Mapbox token no `VITE_MAPBOX_TOKEN`
- [ ] `requirements.txt` do backend (não o `-dev`) inclui todas as deps de produção
- [ ] DB de produção é PostgreSQL+PostGIS (não SQLite)
- [ ] CORS_ORIGINS aponta pro domínio final do frontend
- [ ] Healthcheck `/health` responde 200

Todos os ajustes acima já estão refletidos nos arquivos `docker/Dockerfile.*.prod` e nos templates Helm/Terraform — você só precisa preencher as secrets.
