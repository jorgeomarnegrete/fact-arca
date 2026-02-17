from sqlalchemy.orm import Session
from app.models import Comprobante, ComprobanteDetalle, PuntoVenta, Cliente
from app.schemas import ComprobanteCreate
from app.services.afip import AfipService
from datetime import datetime
import os

class InvoiceService:
    def __init__(self, db: Session):
        self.db = db

    def create_invoice(self, data: ComprobanteCreate):
        # 1. Validar Punto de Venta y Configuración AFIP
        pv = self.db.query(PuntoVenta).filter(PuntoVenta.id == data.punto_venta_id).first()
        if not pv:
            raise ValueError("Punto de venta no encontrado")
        
        if not os.path.exists(pv.certificado_path) or not os.path.exists(pv.key_path):
            raise ValueError("Certificados de AFIP no configurados para este punto de venta")

        # 2. Inicializar Servicio AFIP
        afip = AfipService(
            cuit=pv.cuit,
            certificado=pv.certificado_path,
            clave_privada=pv.key_path,
            produccion=pv.es_produccion
        )

        try:
            # 3. Autenticación AFIP
            if not afip.authenticate():
                raise ValueError("Error de autenticación con AFIP")

            # 4. Obtener último número de comprobante
            ultimo_cbte = afip.get_last_invoice_number(pv.numero, data.tipo_comprobante)
            nuevo_numero = int(ultimo_cbte) + 1

            # 5. Obtener datos del cliente
            cliente = self.db.query(Cliente).filter(Cliente.id == data.cliente_id).first()
            if not cliente:
                 raise ValueError("Cliente no encontrado")

            # 6. Enviar a AFIP
            # TODO: Mapear tipo_doc de cliente a código AFIP (80=CUIT, 96=DNI, etc.)
            tipo_doc_afip = cliente.tipo_documento 
            
            afip_result = afip.create_invoice(
                punto_venta=pv.numero,
                tipo_comprobante=data.tipo_comprobante,
                numero=nuevo_numero,
                fecha=datetime.now(),
                total=data.total_comprobante,
                dni_cuit=int(cliente.numero_documento),
                tipo_doc=tipo_doc_afip,
                lineas_items=None # Por ahora no enviamos detalle de ítems a AFIP (no obligatorio en facturas A/B standard)
            )

            # 7. Guardar en Base de Datos
            nuevo_comprobante = Comprobante(
                fecha_emision=datetime.now(),
                tipo_comprobante=data.tipo_comprobante,
                punto_venta_id=pv.id,
                numero=nuevo_numero,
                cliente_id=cliente.id,
                total_neto=data.total_neto,
                total_iva=data.total_iva,
                total_comprobante=data.total_comprobante,
                cae=afip_result.get("cae"),
                vto_cae=datetime.strptime(afip_result.get("vencimiento"), "%Y%m%d").date() if afip_result.get("vencimiento") else None,
                resultado_afip=afip_result.get("resultado"),
                observaciones_afip=afip_result.get("observaciones")
            )
            
            self.db.add(nuevo_comprobante)
            self.db.commit()
            self.db.refresh(nuevo_comprobante)

            # 8. Guardar Detalles
            for item in data.items:
                detalle = ComprobanteDetalle(
                    comprobante_id=nuevo_comprobante.id,
                    producto_id=item.producto_id,
                    descripcion=item.descripcion,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario,
                    alicuota_iva=item.alicuota_iva,
                    subtotal=item.subtotal
                )
                self.db.add(detalle)
            
            self.db.commit()
            
            return nuevo_comprobante

        except Exception as e:
            # Log error y re-lanzar o guardar comprobante fallido
            print(f"Error generando factura: {e}")
            raise e
