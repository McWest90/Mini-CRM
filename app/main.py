from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import operators, sources, leads, contacts
from app.database import engine, Base

# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Test",
    description="!",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(operators.router)
app.include_router(sources.router)
app.include_router(leads.router)
app.include_router(contacts.router)


@app.get("/")
def read_root():
    return {
        "message": "Lead Distribution Service",
        "docs": "/docs",
        "endpoints": {
            "operators": "/operators",
            "sources": "/sources",
            "contacts": "/contacts",
            "leads": "/leads"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}