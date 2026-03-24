# Document Converter

A web application for converting documents between different formats with a React frontend and FastAPI backend.

## Supported Conversions

| From | To | Engine |
|------|-----|--------|
| PDF | Word (.docx) | Auto, marker-pdf, pdf2docx, or doctr OCR |
| Word | PDF | LibreOffice |
| Word | Excel (.xlsx) | python-docx + openpyxl |
| Excel | Word (.docx) | openpyxl + python-docx |

## Prerequisites

### Required

| Dependency | Version | Installation |
|------------|---------|--------------|
| **Python** | 3.11 - 3.13 | https://www.python.org/downloads/ |
| **Node.js** | 18+ | https://nodejs.org/ |
| **uv** | Latest | See below |

**Install uv (Python package manager):**

```bash
# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Optional (for specific features)

| Dependency | Required For | Installation |
|------------|--------------|--------------|
| **LibreOffice** | Word to PDF conversion | https://www.libreoffice.org/download |
| **Pandoc** | marker-pdf engine | https://pandoc.org/installing.html |
| **Redis** | Async background conversions | https://redis.io/download |

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd converter
```

### 2. Backend Setup

```bash
# Install Python dependencies
uv sync

# Start the backend server (port 8000)
uv run uvicorn app.main:app --reload
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start the frontend dev server (port 5173)
npm run dev
```

### 4. Access the Application

- **Frontend UI**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Environment Variables

Create a `.env` file in the project root (optional):

```bash
# Server
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///./app.db

# Redis (only for async conversions)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## API Endpoints

### Conversion Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/convert/formats` | List supported conversion formats |
| POST | `/convert/sync` | Convert file synchronously (no Redis needed) |
| POST | `/convert/upload` | Upload and convert async (requires Redis) |
| GET | `/convert/status/{task_id}` | Check async conversion status |
| GET | `/convert/download/{task_id}` | Download converted file |

### PDF to Word Engine Selection

The `/convert/sync` endpoint accepts an `engine` parameter for PDF to Word conversion:

| Engine | Description |
|--------|-------------|
| `auto` | Automatically selects based on PDF type (default) |
| `marker` | Professional-grade ML-based conversion (best quality) |
| `pdf2docx` | Fast conversion for text-based PDFs |
| `doctr` | OCR-based conversion for scanned documents |

## Project Structure

```
converter/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI app & endpoints
│       ├── converter_service.py # Core conversion logic
│       ├── converter_tasks.py   # Celery background tasks
│       ├── models.py            # Database models
│       └── settings.py          # Configuration
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Root component
│   │   ├── api/converter.ts     # API client
│   │   └── components/
│   │       └── Converter.tsx    # Main converter UI
│   ├── package.json
│   └── vite.config.ts
├── tests/                       # Python test suite
├── migrations/                  # Alembic database migrations
├── pyproject.toml              # Python dependencies
└── README.md
```

## Development Commands

### Backend

```bash
uv run uvicorn app.main:app --reload  # Dev server with hot reload
uv run pytest                          # Run tests
uv run ruff check .                    # Lint code
uv run ruff format .                   # Format code
```

### Frontend

```bash
cd frontend
npm run dev      # Dev server with hot reload
npm run build    # Production build
npm run lint     # Lint code
```

### Celery Worker (Optional)

```bash
# Only needed for async conversions with Redis
uv run celery -A app.celery_app worker --loglevel=info
```

## Notes

- **First PDF conversion** may be slow as doctr downloads ML models (~200MB)
- **Word to PDF** requires LibreOffice installed and in system PATH
- **Sync endpoint** (`/convert/sync`) works without Redis - recommended for testing
- The SQLite database (`app.db`) is created automatically on first run

## Tech Stack

### Backend
- FastAPI (web framework)
- SQLModel (ORM)
- Celery + Redis (task queue)
- pdf2docx, python-docx, openpyxl (document processing)
- doctr, marker-pdf (ML-based conversion)

### Frontend
- React 18 + TypeScript
- Vite (build tool)
- Axios (HTTP client)
