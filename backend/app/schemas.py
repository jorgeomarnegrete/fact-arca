from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

# Schemas para Punto de Venta
class PuntoVentaBase(BaseModel):
    numero: int
    nombre: Optional[str] = None
    cuit: str
    es_produccion: bool = False

class PuntoVentaCreate(PuntoVentaBase):
    pass

class PuntoVenta(PuntoVentaBase):
    id: int
    class Config:
        orm_mode = True

# Schemas para Cliente
class ClienteBase(BaseModel):
    nombre: str
    tipo_documento: int
    numero_documento: str
    direccion: Optional[str] = None
    email: Optional[str] = None
    condicion_iva: Optional[str] = None
    condicion_iva: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class Cliente(ClienteBase):
    id: int
    class Config:
        orm_mode = True

# Schemas para Producto
class ProductoBase(BaseModel):
    codigo: Optional[str] = None
    descripcion: str
    precio_unitario: float
    alicuota_iva: float = 21.0

class ProductoCreate(ProductoBase):
    pass

class Producto(ProductoBase):
    id: int
    class Config:
        orm_mode = True

# Schemas para Factura (Comprobante)
class ComprobanteDetalleBase(BaseModel):
    producto_id: Optional[int] = None
    descripcion: str
    cantidad: float
    precio_unitario: float
    alicuota_iva: float = 21.0
    subtotal: float

class ClienteDetalleCreate(BaseModel):
    nombre: str
    numero_documento: str
    tipo_documento: Optional[int] = 80
    direccion: Optional[str] = None
    condicion_iva: Optional[str] = None
    email: Optional[str] = None

class ComprobanteCreate(BaseModel):
    cliente_id: Optional[int] = None
    cliente_detalle: Optional[ClienteDetalleCreate] = None
    punto_venta_id: int
    tipo_comprobante: int # 1=A, 6=B, 11=C
    items: List[ComprobanteDetalleBase]
    total_neto: float
    total_iva: float
    total_comprobante: float

class Comprobante(ComprobanteCreate):
    id: int
    numero: int
    fecha_emision: datetime
    cae: Optional[str] = None
    vto_cae: Optional[date] = None
    resultado_afip: Optional[str] = None
    observaciones_afip: Optional[str] = None
    
    class Config:
        orm_mode = True
