#!/usr/bin/env bash
# NEXUS ATLAS — Full installation script
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}"
echo "  ███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗"
echo "  ████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝"
echo "  ██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗"
echo "  ██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║"
echo "  ██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║"
echo "  ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝"
echo "                    A T L A S                  "
echo -e "${NC}"
echo "  Geospatial Intelligence Platform"
echo "  Installing..."
echo ""

# Check prerequisites
command -v python3 &>/dev/null || { echo "Python 3 required"; exit 1; }
command -v node &>/dev/null || { echo "Node.js required"; exit 1; }
command -v docker &>/dev/null || { echo "Docker required"; exit 1; }

# Setup .env
if [ ! -f .env ]; then
  cp .env.example .env
  echo -e "${YELLOW}⚠  .env created — edit it with your tokens before starting${NC}"
fi

if [ ! -f frontend/.env ]; then
  cp frontend/.env.example frontend/.env
fi

# Backend deps
echo -e "${GREEN}[1/4] Installing backend dependencies...${NC}"
cd backend
python3 -m pip install --upgrade pip -q
pip install -r requirements.txt -q
cd ..

# Frontend deps
echo -e "${GREEN}[2/4] Installing frontend dependencies...${NC}"
cd frontend
npm install --silent
cd ..

# Create dirs
echo -e "${GREEN}[3/4] Creating data directories...${NC}"
mkdir -p scans reports logs ai_models/weights

# GEE auth hint
echo -e "${GREEN}[4/4] Setup complete!${NC}"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "  NEXT STEPS:"
echo "  1. Edit .env with your credentials"
echo "  2. Authenticate GEE: earthengine authenticate"
echo "  3. Start with Docker: docker-compose up"
echo "  4. Or local dev:"
echo "     make dev-backend   (terminal 1)"
echo "     make dev-frontend  (terminal 2)"
echo ""
echo "  Access: http://localhost:3000"
echo "  API Docs: http://localhost:8000/docs"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
