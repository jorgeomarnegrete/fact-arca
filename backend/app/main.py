import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import afip, invoices

app = FastAPI()

# Configurar CORS para permitir peticiones desde el frontend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(afip.router, prefix="/api", tags=["afip"])
app.include_router(invoices.router, prefix="/api", tags=["facturas"])

@app.get("/")
def read_root():
    return {"message": "API Facturador ARCA funcionando"}
