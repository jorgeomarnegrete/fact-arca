from sqlalchemy.orm import Session
from app import models, schemas
from sqlalchemy import desc

def get_comprobante(db: Session, comprobante_id: int):
    return db.query(models.Comprobante).filter(models.Comprobante.id == comprobante_id).first()

def get_comprobantes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Comprobante).order_by(desc(models.Comprobante.fecha_emision)).offset(skip).limit(limit).all()

def create_comprobante(db: Session, comprobante: schemas.ComprobanteCreate):
    # Nota: La creación real con lógica de negocio está en InvoiceService.
    # Este CRUD es principalmente para lectura o creaciones simples si fuera necesario.
    pass
