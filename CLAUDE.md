# converter

Document conversion web application with React frontend and FastAPI backend.

## Project Overview

- **Ecosystem**: Python (Backend) + TypeScript/React (Frontend)
- **Purpose**: Document conversion web application
- **Supported Conversions**:
  - PDF → Word (.docx)
  - Word → PDF (requires LibreOffice)
  - Word → Excel (.xlsx)
  - Excel → Word (.docx)

## Tech Stack

### Backend
- **Web Framework**: FastAPI
- **ORM**: SQLModel
- **Validation**: Pydantic
- **Task Queue**: Celery + Redis
- **Code Quality**: Ruff
- **Document Processing**: pdf2docx, python-docx, openpyxl
- **Package Manager**: uv

### Frontend
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **HTTP Client**: Axios
- **Styling**: CSS

## Project Structure

```
converter/
├── pyproject.toml              # Python project config & dependencies
├── uv.lock                     # uv lockfile (pinned dependencies)
├── alembic.ini                 # Database migration config
├── app.db                      # SQLite database (dev, gitignored)
├── CLAUDE.md                   # AI assistant context (this file)
├── README.md                   # Project documentation
├── .env.example                # Environment variables template
├── .gitignore
│
├── backend/                    # Backend source code (Python/FastAPI)
│   └── app/
│       ├── __init__.py
│       ├── main.py             # FastAPI app & all endpoints
│       ├── settings.py         # App configuration (pydantic-settings)
│       ├── database.py         # Database connection & session
│       ├── models.py           # SQLModel database models
│       ├── crud.py             # CRUD operations for models
│       │
│       ├── celery_app.py       # Celery configuration
│       ├── celery_schemas.py   # Pydantic schemas for task endpoints
│       ├── tasks.py            # General background tasks
│       │
│       ├── converter_schemas.py  # Pydantic schemas for conversion API
│       ├── converter_service.py  # Core conversion logic
│       └── converter_tasks.py    # Celery tasks for conversions
│
├── frontend/                   # Frontend source code (React/TypeScript)
│   ├── package.json            # Node.js dependencies
│   ├── package-lock.json       # npm lockfile
│   ├── vite.config.ts          # Vite configuration
│   ├── tsconfig.json           # TypeScript config (base)
│   ├── tsconfig.app.json       # TypeScript config (app)
│   ├── tsconfig.node.json      # TypeScript config (node/vite)
│   ├── eslint.config.js        # ESLint configuration
│   ├── index.html              # HTML entry point
│   ├── .gitignore
│   │
│   ├── public/                 # Static assets (served as-is)
│   │   ├── favicon.svg
│   │   └── icons.svg
│   │
│   └── src/
│       ├── main.tsx            # React entry point
│       ├── App.tsx             # Root component
│       ├── App.css             # App styles
│       ├── index.css           # Global styles
│       │
│       ├── api/
│       │   └── converter.ts    # API client for backend
│       │
│       └── components/
│           ├── Converter.tsx   # Main converter UI component
│           └── Converter.css   # Component styles
│
├── tests/                      # Python test suite
│   ├── __init__.py
│   ├── test_main.py            # API endpoint tests
│   └── test_database.py        # Database tests
│
└── migrations/                 # Alembic database migrations
    ├── env.py
    └── script.py.mako
```

## API Endpoints

### Conversion Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/convert/formats` | List supported conversion formats |
| POST | `/convert/upload` | Upload file, start async conversion (requires Redis) |
| POST | `/convert/sync` | Upload file, convert synchronously (no Redis needed) |
| GET | `/convert/status/{task_id}` | Check async conversion progress |
| GET | `/convert/download/{task_id}` | Download converted file |

### Task Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/tasks/submit` | Submit background task |
| GET | `/tasks/{task_id}` | Get task status |
| POST | `/tasks/{task_id}/revoke` | Cancel task |

### Health & User Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/health` | Health check |
| GET/POST/PATCH/DELETE | `/users/*` | User CRUD |
| GET/POST/PATCH/DELETE | `/posts/*` | Post CRUD |

## Development Commands

### Backend
```bash
# Install dependencies
uv sync

# Start dev server (port 8000)
uv run uvicorn app.main:app --reload

# Start Celery worker (optional, for async conversions)
uv run celery -A app.celery_app worker --loglevel=info

# Run tests
uv run pytest

# Lint & format
uv run ruff check .
uv run ruff format .
```

### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start dev server (port 5173)
npm run dev

# Build for production
npm run build
```

## Environment Variables

```bash
# Backend (.env)
DEBUG=true
HOST=0.0.0.0
PORT=8000
DATABASE_URL=sqlite:///./app.db
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## Conversion Flow

### Synchronous (No Redis Required)
```
1. User selects file + conversion type in React UI
2. POST /convert/sync with file
3. Backend converts file immediately
4. Converted file returned as download
```

### Asynchronous (Requires Redis + Celery)
```
1. User uploads file via POST /convert/upload
2. Backend saves file, queues Celery task
3. User polls GET /convert/status/{task_id}
4. On completion, GET /convert/download/{task_id}
```

## Key Dependencies

### Python (Backend)
- `fastapi` - Web framework
- `sqlmodel` - ORM (SQLAlchemy + Pydantic)
- `celery[redis]` - Task queue
- `pdf2docx` - PDF to Word conversion
- `python-docx` - Word document manipulation
- `openpyxl` - Excel file handling
- `aiofiles` - Async file operations
- `python-multipart` - File upload handling

### Node.js (Frontend)
- `react` - UI framework
- `axios` - HTTP client
- `vite` - Build tool
- `typescript` - Type safety

## Notes

- **Word → PDF**: Requires LibreOffice installed on the system
- **Sync endpoint** (`/convert/sync`): Use for testing without Redis
- **Async endpoint** (`/convert/upload`): Use in production with Redis + Celery

## Maintenance

Update this file when:
- Adding/removing dependencies
- Changing project structure
- Adding new API endpoints
- Modifying build/dev workflows
