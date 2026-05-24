"""
Generate the NEXUS ATLAS technical report as a styled PDF.
Run: python scripts/generate_tech_report.py
Output: docs/NEXUS_ATLAS_Relatorio_Tecnico.pdf
"""
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, ListFlowable, ListItem, HRFlowable,
)


# ── Color palette (cyberpunk-inspired) ────────────────────────────────
ACCENT      = colors.HexColor("#22d3ee")   # cyan-400
ACCENT_DARK = colors.HexColor("#0e7490")   # cyan-700
DARK_BG     = colors.HexColor("#0a0e27")
INK         = colors.HexColor("#1f2937")   # near-black for body
MUTED       = colors.HexColor("#6b7280")
SUCCESS     = colors.HexColor("#16a34a")
WARNING     = colors.HexColor("#d97706")
DANGER      = colors.HexColor("#dc2626")


# ── Style sheet ────────────────────────────────────────────────────────
def build_styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle(
        name="CoverTitle", parent=s["Title"],
        fontSize=32, leading=38, textColor=ACCENT_DARK,
        alignment=TA_CENTER, spaceAfter=10,
    ))
    s.add(ParagraphStyle(
        name="CoverSubtitle", parent=s["Normal"],
        fontSize=14, leading=18, textColor=MUTED,
        alignment=TA_CENTER, spaceAfter=24,
    ))
    s.add(ParagraphStyle(
        name="CoverMeta", parent=s["Normal"],
        fontSize=10, leading=14, textColor=MUTED,
        alignment=TA_CENTER,
    ))
    s.add(ParagraphStyle(
        name="H1", parent=s["Heading1"],
        fontSize=20, leading=26, textColor=ACCENT_DARK,
        spaceBefore=18, spaceAfter=10, keepWithNext=True,
    ))
    s.add(ParagraphStyle(
        name="H2", parent=s["Heading2"],
        fontSize=15, leading=20, textColor=INK,
        spaceBefore=14, spaceAfter=6, keepWithNext=True,
    ))
    s.add(ParagraphStyle(
        name="H3", parent=s["Heading3"],
        fontSize=12, leading=16, textColor=ACCENT_DARK,
        spaceBefore=8, spaceAfter=4, keepWithNext=True,
    ))
    s.add(ParagraphStyle(
        name="Body", parent=s["BodyText"],
        fontSize=10, leading=15, textColor=INK,
        alignment=TA_JUSTIFY, spaceAfter=6,
    ))
    s.add(ParagraphStyle(
        name="NexusBullet", parent=s["BodyText"],
        fontSize=10, leading=14, leftIndent=14, bulletIndent=4,
        spaceAfter=3,
    ))
    s.add(ParagraphStyle(
        name="NexusQuote", parent=s["BodyText"],
        fontSize=10, leading=14, leftIndent=20, rightIndent=20,
        textColor=MUTED, italic=True, borderColor=ACCENT,
        borderPadding=8, spaceAfter=8,
    ))
    s.add(ParagraphStyle(
        name="TOCEntry", parent=s["Normal"],
        fontSize=10, leading=18, leftIndent=8,
    ))
    return s


# ── Helpers ────────────────────────────────────────────────────────────
def hr(color=ACCENT, thickness=1):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceBefore=4, spaceAfter=8)


def tag_table(rows, header_fill=ACCENT_DARK, header_color=colors.white):
    """Build a styled table given a list of (key, value) tuples."""
    data = rows
    t = Table(data, colWidths=[5*cm, 11.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_fill),
        ("TEXTCOLOR",  (0, 0), (-1, 0), header_color),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("ALIGN",      (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def info_grid(rows, col_widths=None, body_size=9):
    """Generic grid table."""
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT_DARK),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), body_size),
        ("ALIGN",      (0, 0), (-1, -1), "LEFT"),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("GRID",       (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def add_page_decorations(canvas, doc):
    """Header + footer on every page (except cover)."""
    canvas.saveState()
    page_num = canvas.getPageNumber()
    if page_num > 1:
        # Header line
        canvas.setStrokeColor(ACCENT)
        canvas.setLineWidth(0.6)
        canvas.line(2*cm, A4[1] - 1.5*cm, A4[0] - 2*cm, A4[1] - 1.5*cm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(2*cm, A4[1] - 1.3*cm, "NEXUS ATLAS — Relatório Técnico")
        canvas.drawRightString(A4[0] - 2*cm, A4[1] - 1.3*cm,
                               f"Página {page_num}")
        # Footer
        canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
        canvas.line(2*cm, 1.2*cm, A4[0] - 2*cm, 1.2*cm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(2*cm, 0.8*cm,
                          "github.com/Devgabriel01/nexus-atlas  •  Plataforma de Inteligência Geoespacial")
        canvas.drawRightString(A4[0] - 2*cm, 0.8*cm,
                               datetime.now().strftime("%Y-%m-%d"))
    canvas.restoreState()


# ── Document builder ───────────────────────────────────────────────────
def build_document():
    out_dir = Path(__file__).resolve().parent.parent / "docs"
    out_dir.mkdir(exist_ok=True)
    pdf_path = out_dir / "NEXUS_ATLAS_Relatorio_Tecnico.pdf"

    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="NEXUS ATLAS — Relatório Técnico",
        author="NEXUS Atlas Engineering",
        subject="Geospatial Intelligence Platform — full technology breakdown",
    )

    s = build_styles()
    flow = []

    # ============================================================
    # COVER PAGE
    # ============================================================
    flow.append(Spacer(1, 4*cm))
    flow.append(Paragraph("🛰️ NEXUS ATLAS", s["CoverTitle"]))
    flow.append(Paragraph(
        "Plataforma avançada de inteligência geoespacial<br/>"
        "com IA, satélites e análise tática em tempo real",
        s["CoverSubtitle"]))
    flow.append(Spacer(1, 1*cm))
    flow.append(hr(thickness=1.5))
    flow.append(Spacer(1, 1*cm))

    cover_table = info_grid([
        ["Componente", "Tecnologia / Provedor"],
        ["Backend", "FastAPI + SQLAlchemy 2.0 + asyncpg"],
        ["Frontend", "React 18 + Vite + TypeScript + Tailwind + Framer Motion"],
        ["Banco de dados", "PostgreSQL 16 (Neon serverless)"],
        ["Imagens de satélite", "Google Earth Engine (Sentinel-1 SAR + Sentinel-2)"],
        ["IA (LLM)", "Groq Llama 3.3 70B Versatile"],
        ["Visão computacional", "YOLOv8 (Ultralytics) + OpenCV"],
        ["Mapas", "Mapbox GL JS (3D)"],
        ["Tempo real", "WebSocket (FastAPI + wsproto)"],
        ["Pagamentos", "Stripe Checkout + Webhook"],
        ["Containers", "Docker multi-stage"],
        ["Deploy", "Render + Neon (configurado: Fly, AWS, Helm)"],
        ["CI/CD", "GitHub Actions (CI + multi-target deploy)"],
        ["Repositório", "github.com/Devgabriel01/nexus-atlas"],
    ], col_widths=[5.5*cm, 11*cm], body_size=9)
    flow.append(cover_table)

    flow.append(Spacer(1, 1.5*cm))
    flow.append(Paragraph(
        f"Gerado em {datetime.now().strftime('%d de %B de %Y, %H:%M')}<br/>"
        "Versão 1.0 — 110+ arquivos, ~13.500 linhas de código<br/>"
        "Documento técnico interno",
        s["CoverMeta"]))

    flow.append(PageBreak())

    # ============================================================
    # 1. VISÃO GERAL
    # ============================================================
    flow.append(Paragraph("1. Visão geral do projeto", s["H1"]))
    flow.append(hr())
    flow.append(Paragraph(
        "<b>NEXUS ATLAS</b> é uma plataforma SaaS de inteligência geoespacial que combina "
        "imagens de satélite reais (Sentinel-1 e Sentinel-2), análise por IA (LLM Llama 3.3 "
        "70B + visão computacional YOLOv8), dashboard 3D estilo cyberpunk, multi-tenancy "
        "com billing, e pipeline em tempo real via WebSocket.", s["Body"]))
    flow.append(Paragraph(
        "A arquitetura é inspirada em sistemas militares de OSINT, centros de comando "
        "futuristas e em assistentes virtuais como Jarvis. O objetivo é fornecer "
        "interpretação tática de mudanças geográficas, detecção automática de anomalias "
        "(estruturas, navios, desmatamento) e geração de relatórios em PDF/JSON.", s["Body"]))

    # ============================================================
    # 2. BACKEND
    # ============================================================
    flow.append(Paragraph("2. Backend — FastAPI (Python 3.11)", s["H1"]))
    flow.append(hr())

    flow.append(Paragraph("O que é", s["H3"]))
    flow.append(Paragraph(
        "Framework Python assíncrono moderno baseado em Starlette + Pydantic. "
        "Usado para construir a API REST e endpoints WebSocket.", s["Body"]))

    flow.append(Paragraph("Por que usamos", s["H3"]))
    flow.append(ListFlowable([
        ListItem(Paragraph("Performance comparável a Node.js", s["NexusBullet"])),
        ListItem(Paragraph("Documentação OpenAPI/Swagger automática em /docs", s["NexusBullet"])),
        ListItem(Paragraph("Validação de tipos via Pydantic (zero boilerplate)", s["NexusBullet"])),
        ListItem(Paragraph("Async nativo — essencial pra Earth Engine + Groq + DB simultâneos", s["NexusBullet"])),
    ], bulletType="bullet"))

    flow.append(Paragraph("Onde aparece no projeto", s["H3"]))
    flow.append(Paragraph(
        "<font face='Courier' size='9'>backend/app/main.py</font> → entry point; "
        "<font face='Courier' size='9'>backend/app/routers/</font> → 11 routers (auth, scan, anomalies, "
        "reports, exploration, history, analyze, integrations, ws, organizations, billing); "
        "<font face='Courier' size='9'>backend/app/middleware/rate_limit.py</font> → rate limiting in-memory.",
        s["Body"]))

    flow.append(Paragraph("Como funciona — passo a passo", s["H3"]))
    flow.append(ListFlowable([
        ListItem(Paragraph("Uvicorn (servidor ASGI) recebe requisição HTTP", s["NexusBullet"])),
        ListItem(Paragraph("CORS middleware valida origem", s["NexusBullet"])),
        ListItem(Paragraph("Rate limit middleware checa IP (60 req/min)", s["NexusBullet"])),
        ListItem(Paragraph("Router específico processa a rota", s["NexusBullet"])),
        ListItem(Paragraph("Dependency injection injeta sessão DB e usuário JWT", s["NexusBullet"])),
        ListItem(Paragraph("Pydantic valida payload de entrada", s["NexusBullet"])),
        ListItem(Paragraph("Endpoint executa lógica → serializa resposta via Pydantic", s["NexusBullet"])),
    ], bulletType="1"))

    # ============================================================
    # 3. BANCO DE DADOS
    # ============================================================
    flow.append(Paragraph("3. Banco de dados — SQLAlchemy 2.0 + PostgreSQL (Neon)", s["H1"]))
    flow.append(hr())
    flow.append(Paragraph(
        "<b>SQLAlchemy</b> é o ORM Python mais robusto, com sintaxe async-first na versão 2.0. "
        "<b>Neon</b> é Postgres serverless gerenciado (free tier 0.5 GB com auto-pause).", s["Body"]))
    flow.append(Paragraph("Modelos definidos", s["H3"]))
    flow.append(info_grid([
        ["Modelo", "Função"],
        ["User", "Conta de usuário (email, password hash, role, organization_id)"],
        ["Organization", "Tenant — possui plano, status assinatura, owner"],
        ["UsageRecord", "Cada scan/AI query é logado pra cota e billing"],
        ["Scan", "Sessão de análise (bbox, datas, tipo, status, anomaly_count)"],
        ["Anomaly", "Detecção individual (type, severity, lat/lon, confidence)"],
        ["Report", "Relatório gerado com IA (PDF + JSON exportáveis)"],
        ["Region", "Áreas pré-cadastradas (Amazônia, Ártico, etc.)"],
    ], col_widths=[4*cm, 12.5*cm], body_size=9))
    flow.append(Spacer(1, 6))
    flow.append(Paragraph(
        "<b>Driver:</b> asyncpg — cliente Postgres binário ~3× mais rápido que psycopg2. "
        "O <font face='Courier' size='9'>database.py</font> detecta SQLite vs Postgres e traduz "
        "<font face='Courier' size='9'>sslmode=require</font> → <font face='Courier' size='9'>ssl=True</font> "
        "(parâmetro incompatível com asyncpg).", s["Body"]))

    # ============================================================
    # 4. AUTENTICAÇÃO
    # ============================================================
    flow.append(Paragraph("4. Autenticação — JWT + bcrypt", s["H1"]))
    flow.append(hr())
    flow.append(Paragraph(
        "<b>JWT (JSON Web Token):</b> token assinado que carrega claims do usuário (sub, exp).<br/>"
        "<b>bcrypt:</b> algoritmo de hash resistente a brute-force.<br/>"
        "<b>python-jose:</b> biblioteca de assinatura JWT.<br/>"
        "<b>passlib:</b> wrapper friendly em cima do bcrypt.", s["Body"]))

    flow.append(Paragraph("Fluxo de autenticação", s["H3"]))
    flow.append(ListFlowable([
        ListItem(Paragraph("POST /auth/register com email + senha", s["NexusBullet"])),
        ListItem(Paragraph("Backend hash a senha com bcrypt (cost factor 12)", s["NexusBullet"])),
        ListItem(Paragraph("Salva User no Postgres", s["NexusBullet"])),
        ListItem(Paragraph("POST /auth/login verifica hash, retorna JWT (sub=user_id, exp=24h)", s["NexusBullet"])),
        ListItem(Paragraph("Toda requisição autenticada inclui Authorization: Bearer &lt;jwt&gt;", s["NexusBullet"])),
        ListItem(Paragraph("get_current_user() decodifica, busca usuário no DB, injeta no endpoint", s["NexusBullet"])),
    ], bulletType="1"))

    # ============================================================
    # 5. WEBSOCKET
    # ============================================================
    flow.append(Paragraph("5. WebSocket — pipeline em tempo real", s["H1"]))
    flow.append(hr())
    flow.append(Paragraph(
        "WebSocket é uma comunicação bidirecional persistente sobre TCP. O backend pode "
        "<b>empurrar</b> eventos pro cliente sem ele perguntar. Scans demoram 30-60 segundos "
        "(download de satélite + AI); sem WS, o frontend teria que fazer polling caro.", s["Body"]))

    flow.append(Paragraph("Arquitetura pub/sub", s["H3"]))
    flow.append(Paragraph(
        "<font face='Courier' size='9'>event_bus.py</font> implementa pub/sub em memória usando "
        "<font face='Courier' size='9'>asyncio.Queue</font>. Cada scan tem um tópico "
        "<font face='Courier' size='9'>scan:&lt;id&gt;</font>. Subscribers (WebSocket clients) "
        "recebem eventos via <font face='Courier' size='9'>async for evt in bus.subscribe(topic)</font>.", s["Body"]))

    flow.append(Paragraph("Sequência de eventos durante um scan", s["H3"]))
    flow.append(info_grid([
        ["Stage", "Progress", "Mensagem"],
        ["started", "5%", "Pipeline initialized"],
        ["fetch", "15-35%", "Fetching Sentinel-2 imagery..."],
        ["sar", "45-55%", "Fetching Sentinel-1 SAR data..."],
        ["ai_detect", "60-75%", "Running YOLO + segmentation"],
        ["temporal", "82-92%", "Comparing before/after imagery"],
        ["complete", "100%", "Scan complete — N anomalies found"],
    ], col_widths=[3.5*cm, 2.5*cm, 10.5*cm], body_size=9))

    # ============================================================
    # 6. EARTH ENGINE
    # ============================================================
    flow.append(Paragraph("6. Google Earth Engine — Sentinel-1 + Sentinel-2", s["H1"]))
    flow.append(hr())
    flow.append(Paragraph(
        "Plataforma do Google que dá acesso ao catálogo público de satélites (Sentinel, "
        "Landsat, MODIS) com API Python + servidores de processamento na nuvem.", s["Body"]))

    flow.append(Paragraph("Sentinel-2 — visível + infravermelho", s["H3"]))
    flow.append(ListFlowable([
        ListItem(Paragraph("Backend recebe POST /scan com bbox + datas", s["NexusBullet"])),
        ListItem(Paragraph("Cria geometria ee.Geometry.BBox(lon_min, lat_min, lon_max, lat_max)", s["NexusBullet"])),
        ListItem(Paragraph("Query COPERNICUS/S2_SR_HARMONIZED filtrada por bbox + datas + nuvens <20%", s["NexusBullet"])),
        ListItem(Paragraph("Seleciona bandas RGB (B4, B3, B2), divide por 10000 (reflectância 0-1)", s["NexusBullet"])),
        ListItem(Paragraph("geemap.ee_export_image() baixa GeoTIFF ~1-3 MB", s["NexusBullet"])),
    ], bulletType="1"))

    flow.append(Paragraph("Sentinel-1 SAR — radar penetrante", s["H3"]))
    flow.append(Paragraph(
        "SAR penetra nuvens, fumaça e escuridão — único método pra monitorar a Amazônia ano todo. "
        "O algoritmo de detecção de mudanças:", s["Body"]))
    flow.append(ListFlowable([
        ListItem(Paragraph("Filtra COPERNICUS/S1_GRD em modo IW, polarização VV", s["NexusBullet"])),
        ListItem(Paragraph("Divide intervalo em duas metades (before/after)", s["NexusBullet"])),
        ListItem(Paragraph("Calcula mediana de cada metade", s["NexusBullet"])),
        ListItem(Paragraph("Log-ratio em dB: diff = after - before", s["NexusBullet"])),
        ListItem(Paragraph("Máscara: pixels com |diff| > 3 dB são mudança forte", s["NexusBullet"])),
        ListItem(Paragraph("Sample 50 pontos aleatórios → cada um vira anomalia", s["NexusBullet"])),
        ListItem(Paragraph("Exporta GeoTIFF do mapa de mudanças (sar_changes.tif)", s["NexusBullet"])),
    ], bulletType="1"))

    flow.append(Paragraph(
        "<b>Autenticação:</b> User OAuth via <font face='Courier' size='9'>"
        "ee.Authenticate(auth_mode='localhost')</font>. Token persiste em "
        "<font face='Courier' size='9'>~/.config/earthengine/credentials</font>. "
        "Projeto: <font face='Courier' size='9'>project-67cfbe40-3c3a-43bd-98e</font>.", s["Body"]))

    # ============================================================
    # 7. IA GENERATIVA
    # ============================================================
    flow.append(Paragraph("7. IA Generativa — Groq + Llama 3.3 70B", s["H1"]))
    flow.append(hr())
    flow.append(Paragraph(
        "<b>Groq</b> é uma empresa que criou um chip LPU (Language Processing Unit) que roda "
        "LLMs ~10× mais rápido que GPU. Servem o <b>Llama 3.3 70B Versatile</b> da Meta, "
        "qualidade comparável a GPT-4o-mini, gratuitamente no tier de dev.", s["Body"]))

    flow.append(Paragraph("Vantagens", s["H3"]))
    flow.append(ListFlowable([
        ListItem(Paragraph("Velocidade: ~500 tokens/s vs ~50 da OpenAI", s["NexusBullet"])),
        ListItem(Paragraph("Gratuito: 14.400 tokens/dia, 30 req/min", s["NexusBullet"])),
        ListItem(Paragraph("Sem cartão de crédito necessário", s["NexusBullet"])),
        ListItem(Paragraph("API compatível com OpenAI SDK (drop-in)", s["NexusBullet"])),
    ], bulletType="bullet"))

    flow.append(Paragraph("Pipeline de geração de relatório", s["H3"]))
    flow.append(ListFlowable([
        ListItem(Paragraph(
            "Backend monta prompt estruturado com scan, anomalias detectadas e threat level", s["NexusBullet"])),
        ListItem(Paragraph(
            "AsyncGroq.chat.completions.create() com response_format={'type': 'json_object'}", s["NexusBullet"])),
        ListItem(Paragraph(
            "Groq retorna análise tática em ~1s (JSON: headline + analysis + recommendations)", s["NexusBullet"])),
        ListItem(Paragraph(
            "Backend parseia JSON com fallback regex em caso de output malformado", s["NexusBullet"])),
        ListItem(Paragraph(
            "Salva no Report row e expõe via /reports/{id}/download/json", s["NexusBullet"])),
    ], bulletType="1"))

    # ============================================================
    # 8. VISÃO COMPUTACIONAL
    # ============================================================
    flow.append(Paragraph("8. Visão Computacional — YOLOv8 + OpenCV", s["H1"]))
    flow.append(hr())
    flow.append(Paragraph(
        "<b>YOLOv8 (Ultralytics)</b>: detector de objetos state-of-the-art. "
        "<b>OpenCV</b>: processamento de imagem (change detection, NDVI binarization). "
        "Detecta automaticamente estradas, navios, aeronaves, estruturas nas imagens.", s["Body"]))

    flow.append(Paragraph("Estratégia em 3 camadas (graceful fallback)", s["H3"]))
    flow.append(info_grid([
        ["Prioridade", "Modelo", "Quando"],
        ["1", "yolov8-satellite.pt (treinado em RarePlanes/xView)", "Existe em ai_models/weights/"],
        ["2", "HuggingFace satellite model", "Env SATELLITE_YOLO_HF_REPO setada"],
        ["3", "yolov8n.pt COCO (78 classes)", "Fallback final, accuracy reduzida"],
    ], col_widths=[2*cm, 9*cm, 5.5*cm], body_size=9))

    flow.append(Paragraph("Mapeamento classe → severity", s["H3"]))
    flow.append(info_grid([
        ["Classe detectada", "Severity atribuída"],
        ["large_aircraft, tanker", "critical"],
        ["aircraft, helicopter, structure", "high"],
        ["ship, vessel, warehouse", "medium"],
        ["truck, vehicle, building", "low"],
    ], col_widths=[6*cm, 10.5*cm], body_size=9))

    # ============================================================
    # 9. FRONTEND
    # ============================================================
    flow.append(Paragraph("9. Frontend — React 18 + Vite + TypeScript", s["H1"]))
    flow.append(hr())
    flow.append(Paragraph(
        "<b>React 18</b>: framework UI declarativo. <b>Vite</b>: bundler 100× mais rápido "
        "que Webpack (HMR em ~50 ms). <b>TypeScript</b>: superset tipado de JavaScript que "
        "pega bugs em compile-time. <b>Tailwind</b>: utility-first CSS (dark mode trivial). "
        "<b>Framer Motion</b>: biblioteca de animações declarativas pro HUD estilo Jarvis. "
        "<b>Zustand</b>: store global leve.", s["Body"]))

    # ============================================================
    # 10. MAPAS
    # ============================================================
    flow.append(Paragraph("10. Mapas — Mapbox GL JS", s["H1"]))
    flow.append(hr())
    flow.append(Paragraph(
        "Biblioteca JavaScript de mapas vetoriais com WebGL — renderiza 3D no browser. "
        "Escolhido por: renderização vetorial (suave em qualquer zoom), 3D nativo (tilt, "
        "rotate, pitch), estilo dark customizável, free tier de 50k loads/mês.", s["Body"]))
    flow.append(Paragraph(
        "Token configurado em <font face='Courier' size='9'>frontend/.env</font> via "
        "<font face='Courier' size='9'>VITE_MAPBOX_TOKEN</font>. Estilo "
        "<font face='Courier' size='9'>mapbox://styles/mapbox/dark-v11</font> com pitch 45° "
        "pra perspectiva tática.", s["Body"]))

    # ============================================================
    # 11. MULTI-TENANCY
    # ============================================================
    flow.append(Paragraph("11. Multi-tenancy — Organizations + Plans", s["H1"]))
    flow.append(hr())
    flow.append(Paragraph(
        "Estrutura que permite múltiplos clientes (organizações) coexistirem na mesma "
        "instância com dados isolados e cotas separadas. Essencial pra vender SaaS.", s["Body"]))

    flow.append(Paragraph("Tiers configurados", s["H3"]))
    flow.append(info_grid([
        ["Plano", "Scans/mês", "AI/mês", "SAR", "Preço"],
        ["FREE", "25", "100", "❌", "$0"],
        ["PRO", "500", "5.000", "✅", "$49"],
        ["ENTERPRISE", "1M+", "1M+", "✅", "$499"],
    ], col_widths=[3.5*cm, 3*cm, 3*cm, 2*cm, 5*cm], body_size=9))

    flow.append(Paragraph("Enforcement de cota", s["H3"]))
    flow.append(ListFlowable([
        ListItem(Paragraph("Usuário faz POST /scan", s["NexusBullet"])),
        ListItem(Paragraph("Endpoint carrega org via current_user.organization_id", s["NexusBullet"])),
        ListItem(Paragraph("enforce_quota(db, org, kind='scan') é chamado", s["NexusBullet"])),
        ListItem(Paragraph("Função conta UsageRecord desde início do mês", s["NexusBullet"])),
        ListItem(Paragraph("Se >= limit, raise HTTP 402 Payment Required + upgrade_url", s["NexusBullet"])),
        ListItem(Paragraph("Senão, record_usage cria UsageRecord, scan continua", s["NexusBullet"])),
    ], bulletType="1"))

    # ============================================================
    # 12. STRIPE
    # ============================================================
    flow.append(Paragraph("12. Pagamentos — Stripe", s["H1"]))
    flow.append(hr())
    flow.append(Paragraph(
        "Stripe é a plataforma de pagamentos com Checkout hospedado — não precisa salvar "
        "cartão na sua aplicação (PCI compliance grátis). Funciona em mock mode se "
        "<font face='Courier' size='9'>STRIPE_SECRET_KEY</font> não estiver setado.", s["Body"]))

    flow.append(Paragraph("Fluxo de upgrade", s["H3"]))
    flow.append(ListFlowable([
        ListItem(Paragraph("Usuário clica 'Upgrade to PRO' no dashboard", s["NexusBullet"])),
        ListItem(Paragraph("Frontend chama POST /billing/checkout {target_plan: 'pro'}", s["NexusBullet"])),
        ListItem(Paragraph("Backend cria Stripe Checkout Session, retorna URL", s["NexusBullet"])),
        ListItem(Paragraph("Frontend redireciona usuário pra Stripe", s["NexusBullet"])),
        ListItem(Paragraph("Stripe envia webhook checkout.session.completed para /billing/webhook", s["NexusBullet"])),
        ListItem(Paragraph("Backend valida assinatura HMAC, atualiza org.plan = 'pro'", s["NexusBullet"])),
    ], bulletType="1"))

    # ============================================================
    # 13. DOCKER
    # ============================================================
    flow.append(Paragraph("13. Containerização — Docker", s["H1"]))
    flow.append(hr())
    flow.append(Paragraph(
        "Empacota aplicação + dependências em imagem portátil. Sem 'funciona na minha máquina'.", s["Body"]))

    flow.append(Paragraph("Imagens criadas", s["H3"]))
    flow.append(info_grid([
        ["Arquivo", "Tamanho final", "Usado em"],
        ["Dockerfile.backend.prod", "~2 GB (GDAL + PyTorch + OpenCV)", "AWS, k8s, Fly.io"],
        ["Dockerfile.backend.render", "~400 MB (slim, sem GDAL/torch)", "Render free tier"],
        ["Dockerfile.frontend.prod", "~50 MB (nginx + dist estática)", "Todos os providers"],
    ], col_widths=[6*cm, 6*cm, 4.5*cm], body_size=8.5))

    # ============================================================
    # 14. DEPLOY
    # ============================================================
    flow.append(Paragraph("14. Deploy — Render + Neon", s["H1"]))
    flow.append(hr())
    flow.append(Paragraph(
        "<b>Render</b> é uma PaaS — você dá um repo Git, ela builda e hospeda. Setup mais "
        "rápido (1 clique via Blueprint), detecta <font face='Courier' size='9'>render.yaml</font> "
        "automaticamente, free tier para web service + static site.", s["Body"]))
    flow.append(Paragraph(
        "<b>Neon</b> é Postgres serverless. Render removeu Postgres free em out/2024, então "
        "usamos Neon (free 0.5 GB, sem cartão, auto-pause economiza compute, performance "
        "idêntica a RDS pra cargas pequenas).", s["Body"]))

    flow.append(Paragraph("Outros targets configurados", s["H3"]))
    flow.append(info_grid([
        ["Provedor", "Custo estimado", "Status no projeto"],
        ["Render + Neon", "$0 (free tier)", "Blueprint criado, env vars pendentes"],
        ["Fly.io", "$0-5/mês", "fly.toml pronto, CLI instalado"],
        ["Railway", "$5/mês", "railway.json pronto, CLI instalado"],
        ["AWS (Terraform)", "~$80/mês", "main.tf completo (ECS+RDS+ALB+CF)"],
        ["Kubernetes (Helm)", "Custo do cluster", "Chart com HPA e Ingress pronto"],
    ], col_widths=[4*cm, 4*cm, 8.5*cm], body_size=8.5))

    # ============================================================
    # 15. CI/CD
    # ============================================================
    flow.append(Paragraph("15. CI/CD — GitHub Actions", s["H1"]))
    flow.append(hr())
    flow.append(Paragraph(
        "<b>ci.yml</b>: roda em cada push. Linta Python (ruff), testa import, builda frontend, "
        "e (no main) buildar+push das imagens Docker pro GitHub Container Registry.<br/>"
        "<b>deploy.yml</b>: manual via workflow_dispatch. Deploy pra Fly ou Render via API key.", s["Body"]))

    # ============================================================
    # 16. FLUXO COMPLETO
    # ============================================================
    flow.append(Paragraph("16. Fluxo completo de um scan", s["H1"]))
    flow.append(hr())
    flow.append(Paragraph(
        "Sequência end-to-end desde o clique do usuário até o relatório com IA pronto:", s["Body"]))

    flow_steps = [
        ("1.", "USER", "POST /scan", "{bbox, dates, scan_type:'full_sar'}"),
        ("2.", "BACKEND", "Quota check", "enforce_quota(org, 'sar') + record_usage(...)"),
        ("3.", "BACKEND", "Persist Scan row", "Status: PENDING → background_task agendado"),
        ("4.", "BACKEND", "Return 202", "{scan_id, status: pending}"),
        ("5.", "USER", "WS connect", "ws://api/ws/scans/<id>?token=jwt"),
        ("6.", "WORKER", "Sentinel-2 fetch", "Earth Engine: download GeoTIFF"),
        ("7.", "WORKER", "Sentinel-1 SAR", "Log-ratio change detection"),
        ("8.", "WORKER", "YOLOv8 detect", "Bounding boxes + class + confidence"),
        ("9.", "WORKER", "Temporal CV", "OpenCV before/after change"),
        ("10.", "WORKER", "Persist anomalies", "Postgres: N rows in Anomaly table"),
        ("11.", "WS", "Emit complete", "{stage:'complete', progress:100, anomaly_count}"),
        ("12.", "USER", "POST /reports", "{scan_id}"),
        ("13.", "BACKEND", "Groq Llama 3.3 70B", "Gera headline + analysis + recommendations"),
        ("14.", "BACKEND", "ReportLab → PDF", "Salva em /reports/<report_id>.pdf"),
        ("15.", "USER", "GET /reports/<id>/download/pdf", "FileResponse"),
    ]
    flow_table_data = [["#", "Ator", "Ação", "Detalhe"]] + [list(r) for r in flow_steps]
    flow.append(info_grid(flow_table_data, col_widths=[1*cm, 2.5*cm, 4.5*cm, 8.5*cm], body_size=8.5))

    # ============================================================
    # 17. ESTADO ATUAL
    # ============================================================
    flow.append(Paragraph("17. Estado atual e próximos passos", s["H1"]))
    flow.append(hr())

    flow.append(Paragraph("✅ O que está pronto", s["H2"]))
    flow.append(info_grid([
        ["Componente", "Status", "URL"],
        ["Backend local", "🟢 Online", "http://localhost:8000"],
        ["Frontend local", "🟢 Online", "http://localhost:5173"],
        ["Postgres Neon", "🟢 Populado", "sa-east-1 (neon.tech)"],
        ["GitHub repo", "🟢 7 commits", "github.com/Devgabriel01/nexus-atlas"],
        ["Render Blueprint", "🟡 Criado", "Aguardando env vars"],
        ["Earth Engine", "🟢 Autenticado", "project-67cfbe40-3c3a-43bd-98e"],
        ["Groq AI", "🟢 Active", "Llama 3.3 70B Versatile"],
        ["Mapbox", "🟢 Token válido", "Verificado HTTP 200"],
    ], col_widths=[4.5*cm, 3.5*cm, 8.5*cm], body_size=9))

    flow.append(Paragraph("⏸️ Pendências", s["H2"]))
    flow.append(ListFlowable([
        ListItem(Paragraph("Setar DATABASE_URL, GROQ_API_KEY, GEE_PROJECT no Render backend", s["NexusBullet"])),
        ListItem(Paragraph("Setar VITE_MAPBOX_TOKEN no Render frontend", s["NexusBullet"])),
        ListItem(Paragraph("Resolver billing lock do GitHub (caso queira usar GH Actions)", s["NexusBullet"])),
        ListItem(Paragraph("Opcionalmente, treinar YOLOv8 satellite-aware em RarePlanes", s["NexusBullet"])),
    ], bulletType="bullet"))

    # ============================================================
    # 18. APÊNDICE — TECNOLOGIAS RESUMO
    # ============================================================
    flow.append(PageBreak())
    flow.append(Paragraph("Apêndice A — Resumo de todas as tecnologias usadas", s["H1"]))
    flow.append(hr())

    tech_summary = [
        ["Camada", "Tecnologia", "Função"],
        ["Linguagem (backend)", "Python 3.11", "Linguagem principal"],
        ["Web framework", "FastAPI 0.115", "API REST + WebSocket assíncrona"],
        ["Servidor ASGI", "Uvicorn + Gunicorn", "Produção: 2 workers, healthcheck"],
        ["ORM", "SQLAlchemy 2.0", "Modelagem + queries async"],
        ["Driver PG", "asyncpg 0.29", "Cliente Postgres binário"],
        ["Banco", "PostgreSQL 16 (Neon)", "Storage relacional serverless"],
        ["Banco dev", "SQLite + aiosqlite", "Desenvolvimento local"],
        ["Validação", "Pydantic v2", "Schemas + settings"],
        ["Auth", "python-jose + bcrypt 4", "JWT + hash de senhas"],
        ["WebSocket", "wsproto + websockets", "Real-time pipeline events"],
        ["IA / LLM", "Groq SDK + Llama 3.3 70B", "Interpretação tática"],
        ["Visão computacional", "Ultralytics YOLOv8", "Detecção de objetos"],
        ["Image processing", "OpenCV 4.10", "Change detection"],
        ["Geospatial", "earthengine-api 0.1.408", "Sentinel-1/2, Landsat"],
        ["Geospatial helper", "geemap 0.34", "Export GeoTIFF"],
        ["Numpy", "1.26", "Operações matriciais"],
        ["Shapely", "2.0", "Geometria vetorial"],
        ["Reports", "ReportLab 4.2", "Geração de PDF"],
        ["Pagamentos", "Stripe SDK 10.12", "Checkout + webhooks"],
        ["Linguagem (front)", "TypeScript 5", "Tipagem estática"],
        ["UI framework", "React 18", "Componentes declarativos"],
        ["Bundler", "Vite 5", "Dev server + build"],
        ["CSS", "TailwindCSS 3", "Utility-first"],
        ["Animações", "Framer Motion", "HUD cyberpunk"],
        ["State", "Zustand", "Store global leve"],
        ["Mapas", "Mapbox GL JS", "Mapas 3D vetoriais"],
        ["Container", "Docker multi-stage", "Imagens portáteis"],
        ["Web server", "nginx alpine", "Servir frontend estático"],
        ["Orquestração", "docker-compose", "Dev local com Postgres+PostGIS"],
        ["Cloud (IaC)", "Terraform 1.5+", "Provisioning AWS"],
        ["Cloud (k8s)", "Helm chart", "Kubernetes deployment"],
        ["Versionamento", "Git + GitHub", "Source control"],
        ["CI/CD", "GitHub Actions", "Build + test + deploy"],
        ["Registry", "GHCR", "Container registry"],
        ["CLIs", "gh, flyctl, railway", "Tooling de deploy"],
    ]
    flow.append(info_grid(tech_summary, col_widths=[4.5*cm, 4.5*cm, 7.5*cm], body_size=8))

    # ============================================================
    # APÊNDICE B — ENDPOINTS
    # ============================================================
    flow.append(Paragraph("Apêndice B — Endpoints da API", s["H1"]))
    flow.append(hr())

    endpoints = [
        ["Método", "Rota", "Função"],
        ["POST", "/auth/register", "Cria usuário, retorna JWT"],
        ["POST", "/auth/login", "Login, retorna JWT"],
        ["GET",  "/auth/me", "Dados do usuário atual"],
        ["POST", "/scan/", "Inicia scan (cota aplicada)"],
        ["GET",  "/scan/", "Lista scans do usuário"],
        ["GET",  "/scan/{id}", "Detalhes de um scan"],
        ["GET",  "/scan/{id}/status", "Status + progresso"],
        ["WS",   "/ws/scans/{id}", "Stream tempo real"],
        ["GET",  "/anomalies/", "Lista anomalias"],
        ["POST", "/reports/", "Gera relatório com IA"],
        ["GET",  "/reports/{id}/download/pdf", "Download PDF"],
        ["GET",  "/reports/{id}/download/json", "Download JSON"],
        ["POST", "/analyze/coordinates", "AI readout pra coordenada"],
        ["POST", "/analyze/ai-query", "Query livre Llama 3.3"],
        ["POST", "/analyze/ndvi", "Cálculo de NDVI"],
        ["GET",  "/analyze/ai/status", "Status do Groq"],
        ["POST", "/orgs/", "Cria organização"],
        ["GET",  "/orgs/me", "Org + plano + uso"],
        ["GET",  "/orgs/plans", "Lista FREE/PRO/ENTERPRISE"],
        ["POST", "/billing/checkout", "Stripe Checkout Session"],
        ["GET",  "/billing/usage", "Counters do mês"],
        ["POST", "/billing/webhook", "Stripe events handler"],
        ["GET",  "/integrations/status", "Status das integrações"],
        ["GET",  "/health", "Liveness probe"],
        ["GET",  "/", "Root info"],
    ]
    flow.append(info_grid(endpoints, col_widths=[1.5*cm, 6*cm, 9*cm], body_size=8.5))

    # ============================================================
    # CONTRA-CAPA
    # ============================================================
    flow.append(PageBreak())
    flow.append(Spacer(1, 6*cm))
    flow.append(Paragraph("NEXUS ATLAS", s["CoverTitle"]))
    flow.append(Paragraph("Plataforma de Inteligência Geoespacial", s["CoverSubtitle"]))
    flow.append(Spacer(1, 2*cm))
    flow.append(hr(thickness=0.6))
    flow.append(Spacer(1, 0.5*cm))
    flow.append(Paragraph(
        "Este documento descreve a arquitetura completa, escolhas técnicas e estado atual<br/>"
        "do projeto NEXUS ATLAS — uma plataforma SaaS de análise geoespacial<br/>"
        "construída com Python, FastAPI, React, Earth Engine, YOLOv8 e Llama 3.3.",
        s["CoverMeta"]))
    flow.append(Spacer(1, 1*cm))
    flow.append(Paragraph(
        "github.com/Devgabriel01/nexus-atlas<br/>"
        "Documento técnico v1.0",
        s["CoverMeta"]))

    # ── Build ──────────────────────────────────────────────────────────
    doc.build(flow, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)
    return pdf_path


if __name__ == "__main__":
    path = build_document()
    print(f"[OK] PDF generated: {path}")
    print(f"     Size: {path.stat().st_size / 1024:.1f} KB")
