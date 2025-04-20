
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
import asyncpg
import boto3
import os
import uuid

# Конфигурация
app = FastAPI()
#app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://note.kfh.ru.net", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://notes_user:notes_password@localhost:5432/notes_db")
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET = "notes-bucket"

# Модели
class Note(BaseModel):
    id: Optional[str] = None
    title: str
    content: str
    group_id: Optional[str] = None
    owner_id: str
    files: List[str] = []

class User(BaseModel):
    username: str
    email: Optional[EmailStr] = None

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    email: Optional[EmailStr] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

class Token(BaseModel):
    access_token: str
    token_type: str

# Инициализация
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY
)

# База данных
async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(255),
            hashed_password VARCHAR(100) NOT NULL
        );
        CREATE TABLE IF NOT EXISTS notes (
            id VARCHAR(36) PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            content TEXT,
            group_id VARCHAR(36),
            owner_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS groups (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL
        );
        CREATE TABLE IF NOT EXISTS group_members (
            group_id VARCHAR(36) REFERENCES groups(id),
            user_id INTEGER REFERENCES users(id),
            PRIMARY KEY (group_id, user_id)
        );
    """)
    await conn.close()

# Аутентификация
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user(username: str):
    conn = await asyncpg.connect(DATABASE_URL)
    user = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
    await conn.close()
    return user

async def authenticate_user(username: str, password: str):
    user = await get_user(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await get_user(username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Маршруты
@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/")
async def root():
    return {"message": "Welcome to Notes App API. Use /docs for API documentation."}

@app.post("/register", response_model=User)
async def register(user: UserCreate):
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        existing_user = await conn.fetchrow("SELECT * FROM users WHERE username = $1", user.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        hashed_password = get_password_hash(user.password)
        await conn.execute(
            "INSERT INTO users (username, email, hashed_password) VALUES ($1, $2, $3)",
            user.username, user.email, hashed_password
        )
    finally:
        await conn.close()
    return {"username": user.username, "email": user.email}

@app.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user)
):
    if not verify_password(password_data.old_password, current_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    hashed_new_password = get_password_hash(password_data.new_password)
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute(
            "UPDATE users SET hashed_password = $1 WHERE id = $2",
            hashed_new_password, current_user["id"]
        )
    finally:
        await conn.close()
    return {"message": "Password changed successfully"}

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/notes/", response_model=Note)
async def create_note(note: Note, file: UploadFile = File(None), current_user: dict = Depends(get_current_user)):
    note_id = str(uuid.uuid4())
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(
        "INSERT INTO notes (id, title, content, group_id, owner_id) VALUES ($1, $2, $3, $4, $5)",
        note_id, note.title, note.content, note.group_id, current_user["id"]
    )
    files = []
    if file:
        file_key = f"notes/{note_id}/{file.filename}"
        s3_client.upload_fileobj(file.file, S3_BUCKET, file_key)
        files.append(file_key)
    await conn.close()
    return {**note.dict(), "id": note_id, "owner_id": str(current_user["id"]), "files": files}

@app.get("/notes/", response_model=List[Note])
async def get_notes(current_user: dict = Depends(get_current_user)):
    conn = await asyncpg.connect(DATABASE_URL)
    notes = await conn.fetch("""
        SELECT n.* FROM notes n
        LEFT JOIN group_members gm ON n.group_id = gm.group_id
        WHERE n.owner_id = $1 OR gm.user_id = $1
    """, current_user["id"])
    await conn.close()
    return [dict(note) for note in notes]

@app.put("/notes/{note_id}", response_model=Note)
async def update_note(note_id: str, note: Note, file: UploadFile = File(None), current_user: dict = Depends(get_current_user)):
    conn = await asyncpg.connect(DATABASE_URL)
    existing_note = await conn.fetchrow("SELECT * FROM notes WHERE id = $1", note_id)
    if not existing_note:
        raise HTTPException(status_code=404, detail="Note not found")
    if existing_note["owner_id"] != current_user["id"] and existing_note["group_id"]:
        is_member = await conn.fetchrow(
            "SELECT * FROM group_members WHERE group_id = $1 AND user_id = $2",
            existing_note["group_id"], current_user["id"]
        )
        if not is_member:
            raise HTTPException(status_code=403, detail="Not authorized")
    await conn.execute(
        "UPDATE notes SET title = $1, content = $2 WHERE id = $3",
        note.title, note.content, note_id
    )
    files = note.files
    if file:
        file_key = f"notes/{note_id}/{file.filename}"
        s3_client.upload_fileobj(file.file, S3_BUCKET, file_key)
        files.append(file_key)
    await conn.close()
    return {**note.dict(), "id": note_id, "owner_id": str(current_user["id"])}

@app.delete("/notes/{note_id}")
async def delete_note(note_id: str, current_user: dict = Depends(get_current_user)):
    conn = await asyncpg.connect(DATABASE_URL)
    note = await conn.fetchrow("SELECT * FROM notes WHERE id = $1", note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note["owner_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    await conn.execute("DELETE FROM notes WHERE id = $1", note_id)
    await conn.close()
    return {"message": "Note deleted"}
