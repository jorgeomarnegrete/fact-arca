from sqlalchemy.orm import Session
from app import models, schemas

def get_punto_venta(db: Session, punto_venta_id: int):
    return db.query(models.PuntoVenta).filter(models.PuntoVenta.id == punto_venta_id).first()

def get_puntos_venta(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.PuntoVenta).offset(skip).limit(limit).all()

def create_punto_venta(db: Session, punto_venta: schemas.PuntoVentaCreate):
    # Nota: aquí no estamos manejando la subida de archivos CRT/KEY aún.
    # Se asume que las rutas se pasarán o se actualizarán luego.
    # Por ahora guardamos rutas dummy o vacías si no vienen en el schema (que no vienen).
    db_punto_venta = models.PuntoVenta(
        numero=punto_venta.numero,
        nombre=punto_venta.nombre,
        cuit=punto_venta.cuit,
        es_produccion=punto_venta.es_produccion,
        certificado_path="", # TODO: Implementar subida de archivos
        key_path=""         # TODO: Implementar subida de archivos
    )
    db.add(db_punto_venta)
    db.commit()
    db.refresh(db_punto_venta)
    return db_punto_venta

def delete_punto_venta(db: Session, punto_venta_id: int):
    db_punto_venta = db.query(models.PuntoVenta).filter(models.PuntoVenta.id == punto_venta_id).first()
    if db_punto_venta:
        db.delete(db_punto_venta)
        db.commit()
        return True
    return False
