
import os
from datetime import date
from typing import Optional
from fastapi import FastAPI, Request, Depends, Form, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Date
from sqlalchemy.orm import sessionmaker, declarative_base, Session as OrmSession

DB_URL = os.getenv("DATABASE_URL") or os.getenv("DATABASE_URI")
if not DB_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "DTN-2025-secure-base")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-please-very-secret")

app = FastAPI(title="DTN SmartOps")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, same_site="lax")

engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Activite(Base):
    __tablename__ = "activites"
    id = Column(Integer, primary_key=True, index=True)
    client = Column(String(255), nullable=False)
    type_intervention = Column(String(255), nullable=False)
    technicien = Column(String(255), nullable=True)
    statut = Column(String(50), nullable=False, default="À faire")
    note = Column(String(1000), nullable=True)
    date_prevue = Column(Date, nullable=True)
    commentaire = Column(String(1000), nullable=True)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def require_auth(request: Request):
    return bool(request.session.get("user"))

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["user"] = username
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Identifiants incorrects."})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: OrmSession = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    rows = db.query(Activite).order_by(Activite.id.desc()).all()
    return templates.TemplateResponse("index.html", {"request": request, "rows": rows})

@app.post("/add")
def add_item(
    request: Request,
    client: str = Form(...),
    type_intervention: str = Form(...),
    technicien: Optional[str] = Form(None),
    statut: str = Form("À faire"),
    note: Optional[str] = Form(None),
    date_prevue: Optional[str] = Form(None),
    commentaire: Optional[str] = Form(None),
    db: OrmSession = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    d = None
    if date_prevue:
        try:
            y, m, d2 = [int(x) for x in date_prevue.split("-")]
            d = date(y, m, d2)
        except Exception:
            d = None
    item = Activite(
        client=client.strip(),
        type_intervention=type_intervention.strip(),
        technicien=(technicien or "").strip(),
        statut=statut.strip(),
        note=(note or "").strip(),
        date_prevue=d,
        commentaire=(commentaire or "").strip(),
    )
    db.add(item)
    db.commit()
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

@app.post("/edit/{item_id}")
def edit_item(
    item_id: int,
    request: Request,
    client: str = Form(...),
    type_intervention: str = Form(...),
    technicien: Optional[str] = Form(None),
    statut: str = Form("À faire"),
    note: Optional[str] = Form(None),
    date_prevue: Optional[str] = Form(None),
    commentaire: Optional[str] = Form(None),
    db: OrmSession = Depends(get_db),
):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    item = db.get(Activite, item_id)
    if not item:
        raise HTTPException(404, "Non trouvé")
    item.client = client.strip()
    item.type_intervention = type_intervention.strip()
    item.technicien = (technicien or "").strip()
    item.statut = statut.strip()
    item.note = (note or "").strip()
    if date_prevue:
        try:
            y, m, d2 = [int(x) for x in date_prevue.split("-")]
            item.date_prevue = date(y, m, d2)
        except Exception:
            item.date_prevue = None
    else:
        item.date_prevue = None
    item.commentaire = (commentaire or "").strip()
    db.commit()
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)

@app.post("/delete/{item_id}")
def delete_item(item_id: int, request: Request, db: OrmSession = Depends(get_db)):
    if not require_auth(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    item = db.get(Activite, item_id)
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse("/", status_code=status.HTTP_302_FOUND)
