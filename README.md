# AgriAI

AI-powered agriculture platform for Indian farmers — crop advisory, weather intelligence, market price predictions, and yield forecasting.

## Quick Start (Docker)

```bash
cp .env.example .env          # fill in your API keys
docker compose up -d
```

Backend at `http://localhost:8000`, frontend at `http://localhost`.

## Local Development

**Backend** (Python 3.11+, PostgreSQL 15+)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in your keys
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend** (Node.js 20+)

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

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

## License

MIT
