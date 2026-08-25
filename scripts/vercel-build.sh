#!/bin/bash
# Vercel build: build the frontend, then stage frontend dist + backend package
# + serverless entrypoint at the deploy root (per the verified mixed pattern).
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

echo "[build] installing frontend deps..."
cd frontend
npm ci --no-audit --no-fund
npm run build
cd ..

echo "[build] staging deploy root..."
rm -rf deploy api && mkdir -p api deploy
# static frontend at outputDirectory (deploy/dist)
cp -r frontend/dist deploy/dist
# backend package + serverless entrypoint at ROOT api/ (Vercel scans root api/)
cp -r backend/remnant api/remnant
find api -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
find api -name '*.pyc' -delete 2>/dev/null || true
cp backend/pyproject.toml api/pyproject.toml
cp frontend/vercel-api/index.py api/index.py
# python deps for the serverless function
cat > api/requirements.txt <<'REQ'
fastapi>=0.115
uvicorn[standard]>=0.30
pydantic>=2.7
REQ

echo "[build] staged:"
ls api api/remnant | head -25