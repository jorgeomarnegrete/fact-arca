from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class PuntoVenta(Base):
    __tablename__ = "puntos_venta"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(Integer, unique=True, nullable=False)  # Número de punto de venta AFIP
    nombre = Column(String, nullable=True) # Nombre descriptivo
    cuit = Column(String, nullable=False) # CUIT del emisor
    certificado_path = Column(String, nullable=False) # Ruta al archivo .crt
    key_path = Column(String, nullable=False) # Ruta al archivo .key
    es_produccion = Column(Boolean, default=False) # True para producción, False para testing

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    tipo_documento = Column(Integer, default=80) # 80 = CUIT, 96 = DNI, 99 = Consumidor Final
    numero_documento = Column(String, unique=True, index=True, nullable=False)
    direccion = Column(String, nullable=True)
    email = Column(String, nullable=True)
    condicion_iva = Column(String, nullable=True) # Responsable Inscripto, Monotributo, etc.

    comprobantes = relationship("Comprobante", back_populates="cliente")

class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True)
    descripcion = Column(String, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    alicuota_iva = Column(Float, default=21.0) # 21.0, 10.5, 0.0, etc.

class Comprobante(Base):
    __tablename__ = "comprobantes"

    id = Column(Integer, primary_key=True, index=True)
    fecha_emision = Column(DateTime, default=datetime.utcnow)
    tipo_comprobante = Column(Integer, nullable=False) # 1 = Factura A, 6 = Factura B, 11 = Factura C
    punto_venta_id = Column(Integer, ForeignKey("puntos_venta.id"))
    numero = Column(Integer, nullable=False) # Número de comprobante asignado por AFIP
    cliente_id = Column(Integer, ForeignKey("clientes.id"))
    
    total_neto = Column(Float, default=0.0)
    total_iva = Column(Float, default=0.0)
    total_comprobante = Column(Float, default=0.0)
    
    cae = Column(String, nullable=True) # Código de Autorización Electrónico
    vto_cae = Column(Date, nullable=True) # Vencimiento del CAE
    resultado_afip = Column(String, nullable=True) # Aprobado, Rechazado
    observaciones_afip = Column(String, nullable=True)

    punto_venta = relationship("PuntoVenta")
    cliente = relationship("Cliente", back_populates="comprobantes")
    items = relationship("ComprobanteDetalle", back_populates="comprobante")

class ComprobanteDetalle(Base):
    __tablename__ = "comprobante_detalles"

    id = Column(Integer, primary_key=True, index=True)
    comprobante_id = Column(Integer, ForeignKey("comprobantes.id"))
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=True)
    descripcion = Column(String, nullable=False) # Se guarda para histórico
    cantidad = Column(Float, default=1.0)
    precio_unitario = Column(Float, nullable=False)
    alicuota_iva = Column(Float, default=21.0)
    subtotal = Column(Float, nullable=False)

    comprobante = relationship("Comprobante", back_populates="items")
    producto = relationship("Producto")
