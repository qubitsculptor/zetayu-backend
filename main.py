from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi import FastAPI, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import List
from datetime import datetime
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi.responses import FileResponse
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

# Serve the frontend static HTML
base_dir = Path(__file__).parent.parent
# app.mount("/", StaticFiles(directory=str(base_dir / "frontend"), html=True), name="static")
app.mount("/static", StaticFiles(directory=str(base_dir / "frontend"), html=False), name="static")

# Route to serve the HTML index at root
@app.get("/", response_class=FileResponse)
async def serve_index():
    return FileResponse(str(base_dir / "frontend" / "index.html"))

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace * with your frontend domain
    allow_methods=["*"],
    allow_headers=["*"],
)

class Contact(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    email: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sandeepkumar:neuradeep_tech@localhost:5432/neuradeep_tech")
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# Contact form endpoint
@app.post("/contact")
async def contact(
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
    session: Session = Depends(get_session),
):
    contact = Contact(name=name, email=email, message=message)
    session.add(contact)
    session.commit()
    session.refresh(contact)
    return {"status": "success", "id": contact.id}

@app.get("/contacts", response_model=List[Contact])
async def read_contacts(session: Session = Depends(get_session)):
    results = session.exec(select(Contact))
    return results.all()