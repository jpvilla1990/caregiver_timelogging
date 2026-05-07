# Caregiver Time Logging

A web application for caregivers to log their working hours and sync them automatically to Google Sheets. Built with FastAPI and vanilla HTML/CSS/JS.

## Features

- Google OAuth login (restricted to whitelisted emails)
- Log date, hours worked, and a daily comment
- Duplicate date prevention
- Automatic sync to Google Sheets via service account
- Last 20 entries displayed on the frontend

## Architecture

```
Caregiver logs in with Gmail (Google OAuth)
    → Backend verifies identity
    → Backend writes to Google Sheets via service account
    → Caregiver never needs direct access to the Sheet
```

Two separate authentication mechanisms:
- **Google OAuth** — caregiver identity (who is logging in)
- **Service account** — Google Sheets access (invisible to the user)

## Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML / CSS / JS (vanilla)
- **Auth**: Google OAuth2
- **Storage**: Google Sheets (via service account)

---

## Setup

### 1. Google Cloud — OAuth credentials

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (e.g. `caregiver-app`)
3. APIs & Services → Enable APIs:
   - Google Sheets API
4. APIs & Services → Credentials → Create OAuth 2.0 Client ID
   - Application type: **Web application**
   - Authorized redirect URIs: `https://your-domain.com/auth/callback`
5. Copy the **Client ID** and **Client Secret**

> **Note:** Keep the OAuth consent screen in **Testing** mode and add the caregiver's Gmail as a test user — this avoids the "unverified app" warning without needing Google verification.

### 2. Google Cloud — Service account

1. IAM & Admin → Service Accounts → Create service account
2. Keys → Add Key → Create new key → **JSON**
3. Download the JSON file — this is your `GOOGLE_SERVICE_ACCOUNT_JSON`
4. Go to your Google Sheet → Share → add the service account email (e.g. `xxx@project.iam.gserviceaccount.com`) with **Editor** access

### 3. Google Sheet

1. Create a new sheet in Google Drive
2. Rename the tab to `records`
3. Add headers in row 1: `Fecha | Horas | Comentario | Registrado`
4. Copy the Sheet ID from the URL: `docs.google.com/spreadsheets/d/SHEET_ID/edit`

---

## Environment variables

| Variable | Description |
|---|---|
| `GOOGLE_CLIENT_ID` | OAuth Client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth Client Secret |
| `GOOGLE_SHEET_ID` | Google Sheet ID |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Full service account JSON (as string) to access spreadsheeet |
| `APP_URL` | Public URL of the app (e.g. `https://caregiver.your-domain.com`) |
| `ALLOWED_EMAILS` | Comma-separated list of authorized Gmail addresses |

---

## Running locally

```bash
# Install dependencies
cd caregiver

# Set environment variables
export GOOGLE_CLIENT_ID=xxx
export GOOGLE_CLIENT_SECRET=xxx
export GOOGLE_SHEET_ID=xxx
export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
export APP_URL=http://localhost:8000
export ALLOWED_EMAILS=caregiver@gmail.com

# Run
uv run uvicorn caregiver.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000)

---

## Docker

```bash
# Build
docker build -t caregiver-app .

# Run
docker run -p 8000:8000 \
  -e GOOGLE_CLIENT_ID=xxx \
  -e GOOGLE_CLIENT_SECRET=xxx \
  -e GOOGLE_SHEET_ID=xxx \
  -e GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}' \
  -e APP_URL=https://your-domain.com \
  -e ALLOWED_EMAILS=caregiver@gmail.com \
  caregiver-app
```

---

## Kubernetes

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: caregiver-secret
  namespace: caregiver
type: Opaque
stringData:
  GOOGLE_CLIENT_ID: "your-client-id"
  GOOGLE_CLIENT_SECRET: "your-client-secret"
  GOOGLE_SHEET_ID: "your-sheet-id"
  GOOGLE_SERVICE_ACCOUNT_JSON: '{"type":"service_account",...}'
  APP_URL: "https://caregiver.your-domain.com"
  ALLOWED_EMAILS: "caregiver@gmail.com"
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: caregiver
  namespace: caregiver
spec:
  replicas: 1
  selector:
    matchLabels:
      app: caregiver
  template:
    metadata:
      labels:
        app: caregiver
    spec:
      containers:
        - name: caregiver
          image: your-registry/caregiver-app:latest
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef:
                name: caregiver-secret
---
apiVersion: v1
kind: Service
metadata:
  name: caregiver-service
  namespace: caregiver
spec:
  selector:
    app: caregiver
  ports:
    - port: 8000
      targetPort: 8000
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: caregiver
  namespace: caregiver
spec:
  parentRefs:
    - name: traefik-gateway
      namespace: traefik
  hostnames:
    - caregiver.your-domain.com
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /
      backendRefs:
        - name: caregiver-service
          port: 8000
```

---

## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/auth/login` | Redirect to Google OAuth consent screen |
| `GET` | `/auth/callback` | OAuth callback, exchanges code for token |
| `GET` | `/auth/userinfo?access_token=` | Returns user info for a given token |
| `POST` | `/api/register` | Create a new entry in Google Sheets |
| `GET` | `/api/registers` | Fetch last 20 entries from Google Sheets |

### POST /api/register

Requires `Authorization: Bearer <token>` header.

```json
{
  "fecha": "2025-05-07",
  "horas": 8,
  "comentario": "Todo bien, tomó la medicación."
}
```

---

## Project structure

```
caregiver/
├── src/
│   └── caregiver/
│       ├── main.py        # FastAPI app, routes, Sheets integration
│       ├── config.py      # Settings via pydantic-settings
│       └── static/
│           └── index.html # Frontend
|   pyproject.toml
Dockerfile
build.sh
README.md
```
