import os
import secrets
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from database import SessionLocal, engine
from models import Base, Board, Column, Card

# --- Configuration ---
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "DTN-2025-secure-base")
BOARD_TITLE = os.getenv("BOARD_TITLE", "DTN SmartOps")

SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(16))

# --- Création de l'application ---
app = FastAPI(title="DTN SmartOps Board")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Initialisation de la base ---
Base.metadata.create_all(bind=engine)

# --- Dépendance DB ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Routes principales ---
@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "title": BOARD_TITLE})


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USER and password == ADMIN_PASS:
        request.session["user"] = username
        return RedirectResponse(url="/board", status_code=303)
    raise HTTPException(status_code=401, detail="Identifiants invalides")


@app.get("/board", response_class=HTMLResponse)
def board_page(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/", status_code=303)

    columns = db.scalars(select(Column).order_by(Column.id)).all()
    return templates.TemplateResponse(
        "board.html",
        {"request": request, "title": BOARD_TITLE, "columns": columns, "user": user},
    )


@app.post("/add_card")
def add_card(column_id: int = Form(...), title: str = Form(...), db: Session = Depends(get_db)):
    card = Card(title=title, column_id=column_id)
    db.add(card)
    db.commit()
    return RedirectResponse(url="/board", status_code=303)


@app.post("/move_card")
def move_card(card_id: int = Form(...), new_column_id: int = Form(...), db: Session = Depends(get_db)):
    card = db.get(Card, card_id)
    if card:
        card.column_id = new_column_id
        db.commit()
    return RedirectResponse(url="/board", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


# --- Lancer le serveur localement ou sur Render ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
