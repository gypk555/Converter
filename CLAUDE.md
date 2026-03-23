# converter

This file provides context about the project for AI assistants.

## Project Overview

- **Ecosystem**: Python

## Tech Stack

- Web Framework: fastapi
- ORM: sqlmodel
- Validation: pydantic
- Task Queue: celery
- Code Quality: ruff

## Project Structure

```
converter/
├── pyproject.toml   # Project config
├── src/
│   └── app/         # Application code
├── tests/           # Test suite
├── migrations/      # Database migrations
```

## Common Commands

- `uv sync` - Install dependencies
- `uv run uvicorn app.main:app --reload` - Start dev server
- `uv run pytest` - Run tests
- `uv run ruff check .` - Run linter
- `uv run ruff format .` - Format code

## Maintenance

Keep CLAUDE.md updated when:

- Adding/removing dependencies
- Changing project structure
- Adding new features or services
- Modifying build/dev workflows

AI assistants should suggest updates to this file when they notice relevant changes.
