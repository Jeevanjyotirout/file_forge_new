# FileForge 🔧

> A production-ready, full-stack file conversion and processing service.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Browser                                                      │
│  React + TailwindCSS (Vite build, served by Nginx)           │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP :80
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  Nginx  (reverse proxy)                                       │
│  /api/* → backend:8000   /  → frontend:80                    │
└──────────┬────────────────────────┬────────────────────────┘
           │                        │
           ▼                        ▼
┌──────────────────┐    ┌───────────────────────────┐
│  FastAPI Backend │    │  React Frontend (Nginx)   │
│  port 8000       │    │  port 80                  │
│  SQLite DB       │    └───────────────────────────┘
│  Celery dispatch │
└────────┬─────────┘
         │  Redis broker
         ▼
┌──────────────────┐    ┌───────────────────────────┐
│  Celery Worker   │    │  Redis 7                  │
│  File processing │◄───│  broker + result backend  │
└──────────────────┘    └───────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Shared Storage Volume          │
│  /app/storage/uploads/          │
│  /app/storage/outputs/          │
│  /app/storage/temp/             │
└─────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Docker ≥ 24
- Docker Compose ≥ 2.24

### Run in one command

```bash
docker-compose up --build
```

Then open **http://localhost** in your browser.

---

## Supported Operations

| Operation      | Description               |
|----------------|---------------------------|
| `copy`         | Copy file as-is           |
| `compress-img` | Compress image (JPEG/PNG) |
| `img-to-pdf`   | Convert image to PDF      |
| `pdf-to-txt`   | Extract text from PDF     |
| `zip`          | Zip a file                |

---

## API Reference

| Method | Endpoint                         | Description                    |
|--------|----------------------------------|--------------------------------|
| POST   | `/api/files/upload`              | Upload file + start job        |
| GET    | `/api/files/`                    | List all records               |
| GET    | `/api/files/{id}`                | Get a single record            |
| GET    | `/api/files/{id}/download`       | Download processed output      |
| DELETE | `/api/files/{id}`                | Delete record + files          |
| GET    | `/api/files/meta/operations`     | List supported operations      |
| GET    | `/api/jobs/by-record/{id}`       | Poll job status by record ID   |
| GET    | `/api/jobs/{job_id}`             | Poll by Celery task ID         |
| GET    | `/api/health`                    | Health check (Redis + uptime)  |
| GET    | `/api/health/ping`               | Simple ping                    |
| GET    | `/api/docs`                      | Swagger UI                     |

---

## Workflow

```
User uploads file
      │
      ▼
POST /api/files/upload
  → File saved to /storage/uploads/
  → FileRecord created in SQLite (status=pending)
  → Celery task dispatched
      │
      ▼
Celery Worker picks up task
  → status=processing
  → File converted/processed
  → Output saved to /storage/outputs/
  → status=done
      │
      ▼
Frontend polls GET /api/jobs/by-record/{id}
  → When status=done, shows Download button
      │
      ▼
GET /api/files/{id}/download
  → FileResponse streams output file
```

---

## Services & Ports

| Service  | Port  | Notes                                    |
|----------|-------|------------------------------------------|
| Nginx    | 80    | Entry point – reverse proxy              |
| Backend  | 8000  | FastAPI (internal only)                  |
| Frontend | 80    | React SPA (internal only)                |
| Redis    | 6379  | Internal only                            |
| Flower   | 5555  | Celery monitor (enable with `--profile monitoring`) |

---

## Environment Variables

See `.env.example` for all variables. Copy and edit:

```bash
cp .env.example .env
```

Key variables:

| Variable          | Default                          | Description              |
|-------------------|----------------------------------|--------------------------|
| `SECRET_KEY`      | `change-me-…`                    | JWT signing key          |
| `MAX_UPLOAD_MB`   | `500`                            | Max upload size          |
| `FILE_TTL_SECONDS`| `3600`                           | File expiry (1 hour)     |
| `REDIS_URL`       | `redis://redis:6379/0`           | Celery broker            |

---

## Enable Celery Monitoring (Flower)

```bash
docker-compose --profile monitoring up --build
```

Then open **http://localhost:5555** (admin / fileforge)

---

## Project Structure

```
FileForgeNew/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── config.py         # Pydantic settings
│   │   ├── database.py       # SQLAlchemy setup
│   │   ├── celery_app.py     # Celery factory
│   │   ├── models/
│   │   │   └── file_record.py
│   │   ├── routers/
│   │   │   ├── files.py      # Upload/download routes
│   │   │   ├── jobs.py       # Job polling routes
│   │   │   └── health.py     # Health check
│   │   ├── services/
│   │   │   ├── converter.py  # File conversion logic
│   │   │   └── storage.py    # Disk I/O helpers
│   │   └── tasks/
│   │       └── process_file.py  # Celery tasks
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── index.css
│   │   ├── components/
│   │   │   ├── DropZone.jsx
│   │   │   ├── ProgressBar.jsx
│   │   │   └── StatusBadge.jsx
│   │   ├── pages/
│   │   │   ├── HomePage.jsx
│   │   │   └── FilesPage.jsx
│   │   ├── hooks/
│   │   │   └── useFileUpload.js
│   │   └── services/
│   │       └── api.js
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── nginx-spa.conf
│   └── Dockerfile
├── worker/
│   └── Dockerfile
├── nginx/
│   ├── nginx.conf
│   └── Dockerfile
├── storage/
│   ├── uploads/
│   ├── outputs/
│   └── temp/
├── docker-compose.yml
├── .env
└── .env.example
```

---

## Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Start Redis locally or update REDIS_URL
uvicorn app.main:app --reload --port 8000
```

### Worker

```bash
cd backend
celery -A app.celery_app worker --loglevel=info --concurrency=2
```

### Frontend

```bash
cd frontend
npm install
# Edit vite.config.js proxy to point to http://localhost:8000
npm run dev
```

---

## Production Checklist

- [ ] Set a strong `SECRET_KEY` in `.env`
- [ ] Set explicit `ALLOWED_ORIGINS` (no wildcards)
- [ ] Change `FLOWER_PASSWORD`
- [ ] Add HTTPS (Nginx + Let's Encrypt / Cloudflare)
- [ ] Set `APP_ENV=production` and `DEBUG=0`
- [ ] Mount storage volume on persistent disk
- [ ] Set up log rotation
