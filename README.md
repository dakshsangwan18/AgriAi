# AgriAI

AI-powered agriculture platform for Indian farmers — crop advisory, weather intelligence, market price predictions, and yield forecasting.

**Features:** AI crop advisor · weather dashboard · price predictions · yield forecasting · price alerts · AI chatbot

## How It Works

1. **Data Collection** — Real market prices from [Data.gov.in](https://data.gov.in), weather from [OpenWeatherMap](https://openweathermap.org), with synthetic fallback
2. **ML Models** — Linear regression for price prediction, Random Forest for yield estimation
3. **Decision Engine** — Rule-based expert system analyzes price trends, weather impact, and market volatility to recommend SELL / WAIT / HOLD
4. **AI Insights** — Gemini generates farmer-friendly explanations in Hinglish; Groq/Llama 3 powers the chatbot
5. **Scheduled Monitoring** — Daily crop analysis at 6 AM, price data collection at 6 PM, hourly alert checks

## Quick Start (Docker)

```bash
cp .env.example .env          # fill in your API keys
docker compose up -d
```

Backend at `http://localhost:8000`, frontend at `http://localhost`.
API docs at `http://localhost:8000/docs`.

## Local Development

**Backend** (Python 3.11+, PostgreSQL 15+)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
cp .env.example .env        # fill in your keys
alembic upgrade head
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`, docs at `http://localhost:8000/docs`.

**Frontend** (Node.js 20+)

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

## Configuration

Copy the `.env.example` file relevant to your setup:

| File | Purpose |
|---|---|
| `.env.example` | Docker Compose variables |
| `backend/.env.example` | Backend app settings (all 33 variables documented) |
| `frontend/.env.example` | Frontend build-time variables |

Generate a secure `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## Testing

```bash
cd backend && pytest
cd frontend && npm test
```

### Create Superuser

```bash
cd backend
SUPERUSER_EMAIL=admin@example.com SUPERUSER_PASSWORD=strong-password \
  python scripts/create_superuser.py
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Production Deployment

```bash
docker compose -f docker-compose.prod.yml up -d
```

Or with TLS termination:
```bash
docker compose -f docker-compose.prod.yml -f docker-compose.proxy.yml up -d
```

Key production settings: `ENVIRONMENT=production`, strong `SECRET_KEY`, `CORS_ORIGINS` allowlist, `COOKIE_SECURE=true`, `FORWARDED_ALLOW_IPS` set to proxy IPs.

### Scripts

| Script | Purpose |
|---|---|
| `scripts/run-migrations.sh` | Apply database migrations |
| `scripts/backup-db.sh` | Backup PostgreSQL |
| `scripts/restore-db.sh <file>` | Restore from backup |

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, PostgreSQL, SQLAlchemy, Redis |
| Frontend | React 19, TypeScript, Vite, TailwindCSS |
| AI | Google Gemini (advisor), Groq/Llama 3 (chatbot) |
| Data | OpenWeatherMap, Data.gov.in |
| Infra | Docker Compose, Nginx, Sentry |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # REST API routes (auth)
│   │   ├── core/                # config, security, cache, middleware
│   │   ├── models/              # SQLAlchemy models
│   │   ├── routers/             # API routers (agent, prices, weather, etc.)
│   │   ├── schemas/             # Pydantic schemas
│   │   └── services/            # Business logic (AI agent, decision engine, ML)
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # pytest test suite
│   └── scripts/                 # Superuser bootstrap
├── frontend/
│   ├── src/
│   │   ├── components/          # UI components (AgentDashboard, ChatBot, etc.)
│   │   ├── pages/               # Route pages (Landing, Login, Settings, etc.)
│   │   ├── services/            # API client + typed endpoints
│   │   ├── config/              # Constants + API base URL
│   │   └── hooks/               # Custom React hooks
│   ├── nginx.conf.template      # Frontend nginx (Render deployment)
│   └── start.sh                 # Runtime nginx config generator
├── nginx/nginx.conf             # Reverse proxy with TLS + CSP
├── scripts/                     # backup, restore, migrations
└── docker-compose*.yml          # Dev / prod / proxy compose files
```

## License

MIT
