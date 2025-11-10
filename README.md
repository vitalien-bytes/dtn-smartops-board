# DTN SmartOps Board (FastAPI)
Interface légère type "tableau d'activité" (CRUD).
- Auth simple (ADMIN_USER / ADMIN_PASS)
- PostgreSQL via `DATABASE_URL`
- Déploiement Render : `render.yaml`

## Local
python -m venv .venv && . .venv/Scripts/activate  # sous Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
set DATABASE_URL=postgresql://user:pass@host:5432/dbname
set ADMIN_USER=admin
set ADMIN_PASS=DTN-2025-secure-base
uvicorn main:app --reload
