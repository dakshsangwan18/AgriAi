# AgriAI Platform

AgriAI is a smart agriculture platform designed to help Indian farmers make better decisions using AI-powered insights, weather data, and market price predictions.

The platform combines real-time data with machine learning models to support crop planning, pricing decisions, and yield forecasting.

# Features

AI Crop Advisor
Provides intelligent sell or hold recommendations based on market trends and forecasts.

Weather Dashboard
Displays real-time weather data with insights tailored for farming decisions.

Market Price Predictions
Shows 7-day price forecasts for major crops using historical and live data.

Yield Forecasting
Estimates expected harvest output based on soil, weather, and crop data.

Smart Alerts
Notifies users when market prices reach predefined targets.

AI Chatbot
Allows farmers to ask agriculture-related questions at any time.

# Tech Stack

Backend
FastAPI, PostgreSQL, SQLAlchemy, Pydantic

Frontend
React, TypeScript, Vite, TailwindCSS

AI Services
Google Gemini, Groq

External APIs
OpenWeatherMap, Data.gov.in

# Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   └── services/
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   └── pages/
│   └── Dockerfile
├── docker-compose.yml
└── docker-compose.prod.yml
```

# Requirements

For local development without Docker:

* Python 3.11 or higher
* Node.js 20 or higher
* PostgreSQL 15 or higher

# Local Development Setup

# Backend

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

The backend server will run at [http://localhost:8000](http://localhost:8000)

# Frontend

```
cd frontend
npm install
npm run dev
```

The frontend application will run at [http://localhost:5173](http://localhost:5173)

# Docker Setup

Docker is the recommended way to run the full stack.

# Development

```
docker-compose up -d
```

# Production

```
docker-compose -f docker-compose.prod.yml up -d
```

The production setup disables hot reload and is intended to be used behind a reverse proxy with HTTPS enabled.
TLS termination is not bundled in the compose file. Use your cloud load balancer or a dedicated reverse proxy.

Optional: Nginx reverse proxy in Docker (HTTP/TLS termination)

```
docker-compose -f docker-compose.prod.yml -f docker-compose.proxy.yml up -d
```

If you enable the proxy profile, place certs in `nginx/ssl/` and update [nginx/nginx.conf](nginx/nginx.conf) with your TLS settings.
Default paths:
- `nginx/ssl/fullchain.pem`
- `nginx/ssl/privkey.pem`

# Configuration

Create a `.env` file inside the backend directory.

```
DATABASE_URL=postgresql://user:password@localhost:5432/agri_ai
SECRET_KEY=replace-with-a-secure-secret

GEMINI_API_KEY=your-key
GROQ_API_KEY=your-key

OPENWEATHER_API_KEY=your-key

GOOGLE_CLIENT_ID=your-id
GOOGLE_CLIENT_SECRET=your-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/auth/google/callback
FRONTEND_URL=http://localhost:5173
```

Do not commit the `.env` file to version control.
Use a `.env.example` file for reference instead.

To generate a secure secret key:

```
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

# Security Hardening Notes

Secrets and rotation:
- Never commit real secrets. If any secret was exposed, rotate it immediately.
- Keys to rotate if exposed: `DATABASE_URL`, `SECRET_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENWEATHER_API_KEY`, `DATA_GOV_IN_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `SENDGRID_API_KEY`, `TWILIO_AUTH_TOKEN`.
- Use [backend/.env.example](backend/.env.example) as the only committed reference.

Environment separation:
- Set `ENVIRONMENT` to `development`, `staging`, or `production`.
- For production, define `CORS_ORIGINS` as a comma-separated allowlist (e.g., `https://app.example.com,https://admin.example.com`).
- Set `FRONTEND_URL` for OAuth redirects.

RBAC and admin access:
- Admin and agent operational endpoints require a superuser account.
- Create a superuser via [backend/scripts/create_superuser.py](backend/scripts/create_superuser.py):

```
SUPERUSER_EMAIL=admin@example.com SUPERUSER_PASSWORD=strong-password \
	python backend/scripts/create_superuser.py
```

Logging and artifacts:
- Runtime logs are written under `backend/logs/` and are gitignored.
- Do not store secrets in logs or build artifacts.

Operational security:
- Set `FORWARDED_ALLOW_IPS` to your reverse proxy IPs/CIDR to prevent spoofed client IPs.
- Anonymous client error logging is disabled in production unless `ALLOW_ANON_ERRORS=true`.

Content Security Policy (CSP):
- CSP is enforced at the reverse proxy/frontend layer with strict defaults.
- Inline JSON-LD scripts in [frontend/index.html](frontend/index.html) are allowed via SHA-256 hashes.
- The inline style block in [frontend/src/pages/LandingPage.tsx](frontend/src/pages/LandingPage.tsx) is allowed via a SHA-256 hash.
- If you modify those inline blocks, update the CSP hashes in [nginx/nginx.conf](nginx/nginx.conf) and [frontend/start.sh](frontend/start.sh).
- Inline style attributes are allowed via `style-src-attr 'unsafe-inline'` because the UI uses inline styles.

# Database Notes

When using Docker, PostgreSQL is managed automatically by Docker Compose.

For local development without Docker, ensure PostgreSQL is running and accessible using the credentials provided in the environment variables.

# Running Tests

Backend tests:

```
cd backend
pytest
```

Frontend tests:

```
cd frontend
npm test
```

# Deployment Notes

* Use the production Docker Compose file
* Set environment variables securely on the server
* Run the application behind Nginx or a cloud load balancer
* Ensure HTTPS is enabled
* Use strong secrets and production API keys

# License

MIT License