# Invoice Web App (Approach 1)

Stack: **FastAPI + SQLAlchemy + Jinja2 + WeasyPrint** with **Postgres/MySQL** (or SQLite for dev).

## Quick start (dev)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Choose a DB URL (dev uses SQLite by default; for Postgres/MySQL set env var)
export DATABASE_URL="sqlite+pysqlite:///./dev.db"
# Postgres: export DATABASE_URL="postgresql+psycopg2://user:pass@localhost:5432/invoices"
# MySQL:    export DATABASE_URL="mysql+pymysql://user:pass@localhost:3306/invoices"

uvicorn app:app --reload
```

- Open http://127.0.0.1:8000/  → Web UI
- Open http://127.0.0.1:8000/docs → API Docs
- Generate PDF: open an invoice then click **Download PDF**

### System packages (WeasyPrint)
WeasyPrint requires Cairo, Pango, GDK-PixBuf, and libffi.
On Ubuntu/Debian:
```bash
sudo apt update && sudo apt install -y libcairo2 pango1.0-tools libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev
```

### Notes
- Invoice numbering is sequential and resets per year (configurable).
- The first run seeds your **Company** using data in `settings.py`.
- To run with Docker, see `docker-compose.yml`.
