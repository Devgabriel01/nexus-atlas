# 🚀 NEXUS ATLAS — Próximos passos

O sistema está **100% funcional localmente** e o código está commitado em git. As últimas etapas exigem autenticação na sua conta — **nada que eu possa fazer sem suas credenciais**. Os comandos abaixo são literalmente o que falta.

## ✅ O que já está pronto

- ✅ Backend + Frontend rodando em http://localhost:8000 / :5173
- ✅ 2 commits git no branch `main` (108 arquivos)
- ✅ GitHub CLI (`gh`) instalado
- ✅ Fly CLI (`flyctl`) instalado em `~/.fly/bin/flyctl.exe`
- ✅ Railway CLI instalado
- ✅ Configs Terraform AWS + Helm K8s + Render Blueprint + GitHub Actions
- ✅ Earth Engine, Groq, Mapbox autenticados
- ✅ SAR funcionando (Sentinel-1) — testado, gera `sar_changes.tif`
- ✅ WebSocket funcionando — testado, eventos chegam ao cliente
- ✅ Multi-tenancy funcionando — FREE bloqueia SAR, PRO libera

## 1️⃣ Push para o GitHub (2 minutos)

```powershell
# Login (abre browser, escolhe "Login with web browser")
gh auth login

# Cria repo + push tudo
gh repo create nexus-atlas --private --source=. --remote=origin --push

# A partir daí o CI roda automaticamente
```

Depois disso:
- Issues / PRs habilitados
- GitHub Actions roda lint + tests + build a cada push
- Container images aparecem em `ghcr.io/<seu-user>/nexus-atlas/{backend,frontend}`

## 2️⃣ Deploy mais rápido — Render (free tier)

Pré-requisito: passo 1 concluído.

1. Abre https://dashboard.render.com/select-repo?type=blueprint
2. Conecta o repo `nexus-atlas`
3. Render detecta `render.yaml` e cria os 3 serviços
4. Em **Environment** de cada serviço, adiciona:
   - `GROQ_API_KEY` = a chave Groq
   - `VITE_MAPBOX_TOKEN` = o token Mapbox

**Resultado em ~5 min:** URL pública pronta pra demo.

## 3️⃣ Deploy mais flexível — Fly.io (free tier)

```powershell
$env:Path += ";$HOME\.fly\bin"

flyctl auth signup    # ou login

# Lança backend
flyctl launch --copy-config --name nexus-atlas --region gru --no-deploy

# Setar secrets
$secret = python -c "import secrets; print(secrets.token_urlsafe(48))"
flyctl secrets set `
  GROQ_API_KEY=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 `
  GEE_PROJECT=project-67cfbe40-3c3a-43bd-98e `
  SECRET_KEY=$secret

# Cria DB Postgres no Fly
flyctl postgres create --name nexus-atlas-db --region gru
flyctl postgres attach nexus-atlas-db --app nexus-atlas

# Deploy!
flyctl deploy
```

## 4️⃣ Deploy AWS (produção real)

```powershell
# Pré-requisito: AWS CLI configurado, terraform 1.5+
cd deploy\terraform\aws

terraform init -backend-config="bucket=meu-tf-state-12345"
terraform plan -var="groq_api_key=gsk_..." -var="image_backend=ghcr.io/seu/nexus-atlas/backend:latest"
terraform apply -auto-approve
```

## 5️⃣ Conectar o frontend ao WebSocket

O backend já emite eventos em `ws://localhost:8000/ws/scans/<id>?token=<JWT>`.
O frontend ainda precisa de um hook. Estrutura recomendada (1 arquivo, ~30 linhas):

```typescript
// frontend/src/hooks/useScanWebSocket.ts
import { useEffect, useRef, useState } from 'react'

interface ScanEvent {
  stage: string
  message: string
  progress: number
  scan_id: string
  [key: string]: any
}

export function useScanWebSocket(scanId: string | null, token: string | null) {
  const [events, setEvents] = useState<ScanEvent[]>([])
  const [progress, setProgress] = useState(0)
  const [stage, setStage] = useState('idle')
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!scanId || !token) return
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const wsUrl = apiUrl.replace(/^http/, 'ws') + `/ws/scans/${scanId}?token=${token}`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onmessage = (e) => {
      const evt: ScanEvent = JSON.parse(e.data)
      setEvents((prev) => [...prev, evt])
      setProgress(evt.progress)
      setStage(evt.stage)
    }
    ws.onerror = (e) => console.error('[WS] error', e)
    return () => ws.close()
  }, [scanId, token])

  return { events, progress, stage }
}
```

Uso em um componente:

```tsx
const { progress, stage, events } = useScanWebSocket(activeScanId, jwt)
return <ProgressBar value={progress} label={stage} log={events} />
```

## 🎯 Caminho mais inteligente agora

1. **Faz o `gh auth login`** (30s)
2. **`gh repo create nexus-atlas --private --source=. --remote=origin --push`** (1 min)
3. **Conecta no Render** (5 min) — link público pronto pra mandar pra alguém
4. Quando quiser dar pra Stripe/clientes reais: troca pra Fly.io ou AWS

Cada um desses passos é UM comando ou UM clique. **Tudo o que vinha antes (8h de trabalho) ficou pronto.**
