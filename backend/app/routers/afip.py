import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.crud import puntos_venta as crud_pv
from app.schemas import PuntoVenta, PuntoVentaCreate
from app.services.afip import AfipService
from typing import List

router = APIRouter()

# Determinar un directorio seguro para guardar certificados
# Usamos una ruta relativa a este archivo para que funcione tanto en Docker como local
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "certs")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/puntos-venta/", response_model=PuntoVenta)
def create_punto_venta(
    numero: int = Form(...),
    nombre: str = Form(None),
    cuit: str = Form(...),
    es_produccion: bool = Form(False),
    certificado: UploadFile = File(...),
    clave_privada: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Guardar archivos
    cert_filename = f"{cuit}_{numero}.crt"
    key_filename = f"{cuit}_{numero}.key"
    
    cert_path = os.path.join(UPLOAD_DIR, cert_filename)
    key_path = os.path.join(UPLOAD_DIR, key_filename)
    
    with open(cert_path, "wb") as buffer:
        buffer.write(certificado.file.read())
        
    with open(key_path, "wb") as buffer:
        buffer.write(clave_privada.file.read())
        
    # Crear objeto schema manualmente
    pv_data = PuntoVentaCreate(
        numero=numero,
        nombre=nombre,
        cuit=cuit,
        es_produccion=es_produccion
    )
    
    # Crear en DB
    db_pv = crud_pv.create_punto_venta(db, pv_data)
    
    # Actualizar rutas en DB (esto requeriría actualizar el modelo/crud para soportar update, 
    # por ahora hacemos un hack o asumimos que el CRUD lo maneja. 
    # En el CRUD anterior puse campos vacíos. Vamos a actualizarlo directamento.)
    db_pv.certificado_path = cert_path
    db_pv.key_path = key_path
    db.commit()
    db.refresh(db_pv)
    
    return db_pv

@router.get("/puntos-venta/", response_model=List[PuntoVenta])
def read_puntos_venta(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_pv.get_puntos_venta(db, skip=skip, limit=limit)

@router.delete("/puntos-venta/{punto_venta_id}")
def delete_punto_venta(punto_venta_id: int, db: Session = Depends(get_db)):
    # Obtener el PV para saber los archivos
    pv = crud_pv.get_punto_venta(db, punto_venta_id)
    if not pv:
        raise HTTPException(status_code=404, detail="Punto de venta no encontrado")
    
    # Borrar archivos si existen
    if pv.certificado_path and os.path.exists(pv.certificado_path):
        try:
            os.remove(pv.certificado_path)
        except OSError:
            pass # Ignorar error si no se puede borrar archivo
            
    if pv.key_path and os.path.exists(pv.key_path):
        try:
            os.remove(pv.key_path)
        except OSError:
            pass

    # Borrar de DB
    success = crud_pv.delete_punto_venta(db, punto_venta_id)
    if not success:
        raise HTTPException(status_code=500, detail="Error al borrar de base de datos")
        
    return {"status": "success", "message": f"Punto de venta {pv.numero} eliminado correctamente"}

# Definir directorio de caché
CACHE_DIR = os.path.join(BASE_DIR, "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

@router.get("/afip/test-connection/{punto_venta_id}")
def test_afip_connection(punto_venta_id: int, db: Session = Depends(get_db)):
    pv = crud_pv.get_punto_venta(db, punto_venta_id)
    if not pv:
        raise HTTPException(status_code=404, detail="Punto de venta no encontrado")
        
    if not os.path.exists(pv.certificado_path) or not os.path.exists(pv.key_path):
        raise HTTPException(status_code=400, detail="Certificados no encontrados en el servidor")

    print(f"DEBUG: PuntoVenta {pv.id} - CUIT: {pv.cuit} - Es Produccion: {pv.es_produccion}")

    try:
        # Debugging: Mostrar configuración actual
        # Si da error de certificado no confiable, verificar que Es Produccion sea False en DB
        # es_produccion = False # pv.es_produccion 
        # print(f"DEBUG: Forzando produccion={es_produccion} para test-connection")

        afip = AfipService(
            cuit=pv.cuit,
            certificado=pv.certificado_path,
            clave_privada=pv.key_path,
            produccion=pv.es_produccion,
            cache_dir=CACHE_DIR
        )
        
        if afip.authenticate():
            # Prueba adicional: obtener último comprobante
            ultimo_cbte = afip.get_last_invoice_number(pv.numero, 11) # 11 = Factura C por defecto para test
            return {
                "status": "success",
                "message": "Conexión con AFIP exitosa",
                "token_expiration": afip.wsaa.Expiracion,
                "ultimo_comprobante_c": ultimo_cbte
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
