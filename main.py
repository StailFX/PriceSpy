# price_spy-main/main.py

import os
from datetime import datetime, timedelta
from typing import Optional, Dict

from fastapi import (
    FastAPI, Depends, HTTPException, status,
    Request, Form
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from databases import Database
from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    Integer, String, select
)
from contextlib import asynccontextmanager

# ----------------------------
# 1. Настройка базы данных
# ----------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")
database = Database(DATABASE_URL)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata = MetaData()

products = Table(
    "products", metadata,
    Column("id",   Integer, primary_key=True),
    Column("name", String(255), nullable=False, unique=True),
    Column("sku",  String(50),  unique=True, nullable=True),
)
users = Table(
    "users", metadata,
    Column("id",              Integer, primary_key=True),
    Column("username",        String(50), unique=True, nullable=False),
    Column("hashed_password", String(128),           nullable=False),
    Column("role",            String(20),            nullable=False),  # 'admin' or 'user'
)
metadata.create_all(engine)

# ----------------------------
# 2. JWT и безопасность
# ----------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
pwd_context    = CryptContext(schemes=["bcrypt"], deprecated="auto")
templates      = Jinja2Templates(directory="templates")

# ----------------------------
# 3. Pydantic-схемы
# ----------------------------
class Token(BaseModel):
    access_token: str
    token_type:   str

class TokenData(BaseModel):
    username: Optional[str] = None
    role:     Optional[str] = None

class User(BaseModel):
    username: str
    role:     str

class UserInDB(User):
    hashed_password: str

class ProductCreate(BaseModel):
    name: str

class Product(ProductCreate):
    id:  int
    sku: Optional[str] = None
    class Config:
        from_attributes = True

# ----------------------------
# 4. Lifespan: подключение к БД и создание дефолтных пользователей
# ----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    # если нет ни одного пользователя – создаём admin/user
    row = await database.fetch_one(select(users).limit(1))
    if not row:
        await database.execute(users.insert().values(
            username="admin",
            hashed_password=pwd_context.hash("admin"),
            role="admin"
        ))
        await database.execute(users.insert().values(
            username="user",
            hashed_password=pwd_context.hash("user"),
            role="user"
        ))
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

# ----------------------------
# 5. Утилиты аутентификации
# ----------------------------
async def get_user(username: str) -> Optional[UserInDB]:
    row = await database.fetch_one(
        select(users).where(users.c.username == username)
    )
    return UserInDB(**row) if row else None

async def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = await get_user(username)
    if not user or not pwd_context.verify(password, user.hashed_password):
        return None
    return user

def create_access_token(data: Dict[str,str], expires_delta: Optional[timedelta]=None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate":"Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role:     str = payload.get("role")
        if username is None or role is None:
            raise exc
    except JWTError:
        raise exc
    user = await get_user(username)
    if not user:
        raise exc
    return User(username=user.username, role=user.role)

async def require_user(user: User = Depends(get_current_user)): return user

async def require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return user

# ----------------------------
# 6. API (JSON) маршруты
# ----------------------------
@app.post("/token", response_model=Token)
async def login_token(form: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form.username, form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate":"Bearer"}
        )
    token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return {"access_token": token, "token_type": "bearer"}

@app.get("/products", response_model=list[Product])
async def api_list_products(u: User = Depends(require_user)):
    rows = await database.fetch_all(select(products))
    return [Product(**r) for r in rows]

@app.post("/products", response_model=Product)
async def api_create_product(
    prod: ProductCreate,
    u: User = Depends(require_user)
):
    # запрещаем дубли по name
    exists = await database.fetch_one(
        select(products).where(products.c.name == prod.name)
    )
    if exists:
        raise HTTPException(status_code=400, detail="Product name already exists")
    new_id = await database.execute(products.insert().values(**prod.model_dump()))
    row    = await database.fetch_one(select(products).where(products.c.id == new_id))
    return Product(**row)

@app.delete("/products/{pid}")
async def api_delete_product(pid: int, u: User = Depends(require_admin)):
    await database.execute(products.delete().where(products.c.id == pid))
    return {"status":"deleted"}

# ----------------------------
# 7. Web (HTML) маршруты
# ----------------------------
@app.get("/", include_in_schema=False)
async def web_root():
    return RedirectResponse("/login", status_code=302)

@app.get("/register", response_class=HTMLResponse)
async def web_register_form(request: Request, error: str = ""):
    return templates.TemplateResponse(
        "register.html", {"request": request, "error": error}
    )

@app.post("/register", response_class=HTMLResponse)
async def web_register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    if await get_user(username):
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Пользователь уже существует"}
        )
    await database.execute(users.insert().values(
        username=username,
        hashed_password=pwd_context.hash(password),
        role="user"
    ))
    return RedirectResponse("/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def web_login_form(request: Request, error: str = ""):
    return templates.TemplateResponse(
        "login.html", {"request": request, "error": error}
    )

@app.post("/login", response_class=HTMLResponse)
async def web_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    user = await authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Неверный логин или пароль"}
        )
    token = create_access_token({"sub": user.username, "role": user.role})
    resp  = RedirectResponse("/dashboard", status_code=302)
    resp.set_cookie("Authorization", f"Bearer {token}", httponly=True)
    return resp

@app.get("/dashboard", response_class=HTMLResponse)
async def web_dashboard(request: Request):
    cookie = request.cookies.get("Authorization", "")
    if not cookie.startswith("Bearer "):
        return RedirectResponse("/login")
    token = cookie.removeprefix("Bearer ").strip()
    try:
        user = await get_current_user(token)
    except HTTPException:
        return RedirectResponse("/login")
    rows = await database.fetch_all(select(products))
    return templates.TemplateResponse(
        "index.html", {"request": request, "products": rows, "user": user}
    )

@app.get("/new", response_class=HTMLResponse)
async def web_new_form(request: Request, error: str = ""):
    cookie = request.cookies.get("Authorization", "")
    if not cookie.startswith("Bearer "):
        return RedirectResponse("/login")
    token = cookie.removeprefix("Bearer ").strip()
    try:
        user = await get_current_user(token)
    except HTTPException:
        return RedirectResponse("/login")
    return templates.TemplateResponse(
        "new_product.html",
        {"request": request, "user": user, "error": error}
    )

@app.post("/new", response_class=HTMLResponse)
async def web_new(request: Request, name: str = Form(...)):
    cookie = request.cookies.get("Authorization", "")
    if not cookie.startswith("Bearer "):
        return RedirectResponse("/login")
    token = cookie.removeprefix("Bearer ").strip()
    try:
        user = await get_current_user(token)
    except HTTPException:
        return RedirectResponse("/login")

    # проверяем уникальность
    exists = await database.fetch_one(
        select(products).where(products.c.name == name)
    )
    if exists:
        return templates.TemplateResponse(
            "new_product.html",
            {
              "request": request,
              "user": user,
              "error": "Товар с таким названием уже существует"
            }
        )

    new_id = await database.execute(products.insert().values(name=name))
    return RedirectResponse(f"/confirm/{new_id}", status_code=303)

@app.get("/confirm/{pid}", response_class=HTMLResponse)
async def web_confirm(request: Request, pid: int):
    cookie = request.cookies.get("Authorization", "")
    if not cookie.startswith("Bearer "):
        return RedirectResponse("/login")
    token = cookie.removeprefix("Bearer ").strip()
    try:
        user = await get_current_user(token)
    except HTTPException:
        return RedirectResponse("/login")

    row = await database.fetch_one(select(products).where(products.c.id == pid))
    if not row:
        raise HTTPException(404, "Товар не найден")

    return templates.TemplateResponse(
        "confirm.html", {"request": request, "product": row, "user": user}
    )


@app.post("/delete/{pid}", response_class=HTMLResponse)
async def web_delete(request: Request, pid: int):
    # 1) Извлекаем и валидируем JWT из cookie
    cookie = request.cookies.get("Authorization", "")
    if not cookie.startswith("Bearer "):
        return RedirectResponse("/login", status_code=302)
    token = cookie.removeprefix("Bearer ").strip()
    try:
        user = await get_current_user(token)
    except HTTPException:
        return RedirectResponse("/login", status_code=302)

    # 2) Если не админ — рендерим дашборд со встроенной ошибкой
    if user.role != "admin":
        rows = await database.fetch_all(select(products))
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "products": rows,
                "user": user,
                "error": "У вас недостаточно прав для удаления товара"
            }
        )

    # 3) Если админ — удаляем и редиректим
    await database.execute(products.delete().where(products.c.id == pid))
    return RedirectResponse("/dashboard", status_code=302)

@app.get("/logout", response_class=RedirectResponse)
async def web_logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("Authorization")
    return resp

# ----------------------------
# 8. Запуск приложения
# ----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
