import os
from pyafipws.wsaa import WSAA
from pyafipws.wsfev1 import WSFEv1
from datetime import datetime

class AfipService:
    def __init__(self, cuit: str, certificado: str, clave_privada: str, produccion: bool = False):
        self.cuit = cuit
        self.certificado = certificado
        self.clave_privada = clave_privada
        self.produccion = produccion
        
        # URL de WSDLs
        self.wsdl_wsaa = "https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl" if produccion else "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl"
        self.wsdl_wsfe = "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL" if produccion else "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
        
        self.wsaa = WSAA()
        self.wsfe = WSFEv1()

    def authenticate(self):
        """Autentica con AFIP y obtiene el Ticket de Acceso (TA)"""
        # Configurar WSAA
        # Nota: En un entorno real, manejar la caché del TA para no pedirlo en cada request (dura 12hs)
        tra = self.wsaa.CreateTRA("wsfe", ttl=43200)
        cms = self.wsaa.SignTRA(tra, self.certificado, self.clave_privada)
        self.wsaa.Conectar(cache=None, wsdl=self.wsdl_wsaa) # cache=None para evitar problemas de permisos en directorios por defecto
        self.wsaa.LoginCMS(cms)
        
        # Configurar WSFE con el token obtenido
        self.wsfe.SetTicketAcceso(self.wsaa.Expiracion, self.wsaa.Token, self.wsaa.Sign)
        self.wsfe.Cuit = self.cuit
        self.wsfe.Conectar(cache=None, wsdl=self.wsdl_wsfe)
        
        return True

    def get_last_invoice_number(self, punto_venta: int, tipo_comprobante: int):
        """Obtiene el último número de comprobante autorizado"""
        # cbte_tipo: 1=Factura A, 6=Factura B, 11=Factura C
        return self.wsfe.CompUltimoAutorizado(tipo_comprobante, punto_venta)

    def create_invoice(self, punto_venta, tipo_comprobante, numero, fecha, total, dni_cuit, tipo_doc, lineas_items):
        """
        Envía una factura a AFIP para obtener CAE.
        lineas_items: lista de dicts con detalle (opcional para facturas, pero útil para validar totales)
        """
        concepto = 1 # 1: Productos, 2: Servicios, 3: Productos y Servicios
        
        # Validar fecha
        fecha_cbte = fecha.strftime("%Y%m%d")

        # Configurar cabecera
        self.wsfe.CrearFactura(
            concepto=concepto,
            tipo_doc=tipo_doc,
            nro_doc=dni_cuit,
            tipo_cbte=tipo_comprobante,
            punto_vta=punto_venta,
            cbt_desde=numero,
            cbt_hasta=numero,
            imp_total=total,
            imp_tot_conc=0, # Importe neto no gravado
            imp_neto=total / 1.21, # Simplificación: asumimos todo al 21% por ahora (ajustar lógica luego)
            imp_iva=total - (total / 1.21),
            imp_trib=0,
            imp_op_ex=0,
            fecha_cbte=fecha_cbte,
            fecha_venc_pago=None
        )
        
        # Agregar alícuotas de IVA (Simplificado al 21%)
        self.wsfe.AgregarIva(id_iva=5, base_imp=total / 1.21, importe=total - (total / 1.21)) # 5 = 21%

        # Solicitar CAE
        self.wsfe.CAESolicitar()
        
        if self.wsfe.Resultado == "A":
            return {
                "cae": self.wsfe.CAE,
                "vencimiento": self.wsfe.Vencimiento,
                "resultado": "Aprobado"
            }
        else:
            return {
                "resultado": "Rechazado",
                "errores": self.wsfe.Excepcion,
                "observaciones": self.wsfe.Obs
            }
