import os
from pyafipws.wsaa import WSAA
from pyafipws.wsfev1 import WSFEv1
from datetime import datetime

class AfipService:
    def __init__(self, cuit: str, certificado: str, clave_privada: str, produccion: bool = False, cache_dir: str = None):
        self.cuit = cuit
        self.certificado = certificado
        self.clave_privada = clave_privada
        self.produccion = produccion
        self.cache_dir = cache_dir
        
        # URL de WSDLs
        self.wsdl_wsaa = "https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl" if produccion else "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl"
        self.wsdl_wsfe = "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL" if produccion else "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
        
        self.wsaa = WSAA()
        self.wsfe = WSFEv1()

    def authenticate(self):
        """Autentica con AFIP y obtiene el Ticket de Acceso (TA)"""
        import sys
        import os
        import glob
        import re
        import html

        # Configurar WSAA
        # Nota: En un entorno real, manejar la caché del TA para no pedirlo en cada request (dura 12hs)
        # Usar cache_dir si está definido
        
        # Hack para pyafipws/pysimplesoap que a veces lee sys.argv
        # (Mantener por seguridad si pyafipws lo requiere en este entorno)
        old_argv = sys.argv
        sys.argv = [sys.argv[0]]
        
        try:
            # Primero conectamos para ver si hay un token válido en caché
            # pyafipws espera un directorio en el argumento cache, no el archivo
            self.wsaa.Conectar(cache=self.cache_dir, wsdl=self.wsdl_wsaa) 
        finally:
             sys.argv = old_argv

        # Verificar si expiró o no existe
        # Nota: wsaa.Expirado() puede crashear si no hay token cargado.
        # Verificamos si tenemos token y si no ha expirado.
        # En pyafipws, Expiracion suele ser un atributo de la instancia tras conectar/leer TA.
        expiracion = getattr(self.wsaa, "Expiracion", None)
        token = getattr(self.wsaa, "Token", None)
        sign = getattr(self.wsaa, "Sign", None)
        
        token_valido = False
        if token and sign and expiracion:
            try:
                print(f"DEBUG: Verificando expiracion: {expiracion}")
                # Nota: Expirado espera un string o datetime, pyafipws devuelve string en Expiracion
                if not self.wsaa.Expirado(expiracion):
                    token_valido = True
                    print("DEBUG: Token válido en caché (Cargado por pyafipws)")
            except Exception as e:
                print(f"DEBUG: Error verificando expiración: {e}")
                pass
        
        # Si pyafipws no cargó nada, intentamos buscar TA.xml manualmente
        # (El cache de pyafipws a veces tiene nombres hash para WSDLs, pero el TA debería ser TA.xml si lo forzamos)
        if not token_valido and self.cache_dir:
            ta_file = os.path.join(self.cache_dir, "TA.xml")
            if os.path.exists(ta_file):
                print(f"DEBUG: Intentando leer {ta_file} manualmente...")
                try:
                    with open(ta_file, "r", encoding="utf8") as file:
                        content = file.read()
                        
                    content_unescaped = html.unescape(content)
                    
                    token_match = re.search(r'<token>(.+?)</token>', content_unescaped)
                    sign_match = re.search(r'<sign>(.+?)</sign>', content_unescaped)
                    exp_match = re.search(r'<expirationTime>(.+?)</expirationTime>', content_unescaped)
                    
                    if token_match and sign_match and exp_match:
                        exp_str = exp_match.group(1)
                        if not self.wsaa.Expirado(exp_str):
                            print(f"DEBUG: Token válido encontrado manualmente en {ta_file}")
                            self.wsaa.Token = token_match.group(1)
                            self.wsaa.Sign = sign_match.group(1)
                            self.wsaa.Expiracion = exp_str
                            token_valido = True
                except Exception as ex:
                    print(f"DEBUG: Error leyendo {ta_file}: {ex}")

        if not token_valido:
            print("DEBUG: Generando nuevo token...")
            try:
                # Generar nuevo token
                tra = self.wsaa.CreateTRA("wsfe", ttl=43200)
                cms = self.wsaa.SignTRA(tra, self.certificado, self.clave_privada)
                self.wsaa.LoginCMS(cms)
                print("DEBUG: LoginCMS exitoso")
                
                # Debug logging
                if hasattr(self.wsaa, 'xml_response'):
                    # print(f"DEBUG: XML RESPONSE: {self.wsaa.xml_response}") # Reducir ruido
                    pass
                elif hasattr(self.wsaa.client, 'xml_response') and self.wsaa.client.xml_response:
                    # print(f"DEBUG: XML RESPONSE (client): {self.wsaa.client.xml_response}")
                    pass

                if not getattr(self.wsaa, "Expiracion", None):
                    # Fallback: Parsear XML manualmente si pyafipws falló
                    print("DEBUG: pyafipws no parseó XML, intentando manual...")
                    response_xml = getattr(self.wsaa, 'xml_response', None)
                    if not response_xml and hasattr(self.wsaa.client, 'xml_response'):
                        response_xml = self.wsaa.client.xml_response
                    
                    if response_xml:
                        import re
                        import html
                        
                        if isinstance(response_xml, bytes):
                            response_xml = response_xml.decode('utf8', errors='ignore')
                        
                        # Des-escapar el XML (porque viene dentro de loginCmsReturn)
                        response_xml_unescaped = html.unescape(response_xml)
                            
                        token_match = re.search(r'<token>(.+?)</token>', response_xml_unescaped)
                        sign_match = re.search(r'<sign>(.+?)</sign>', response_xml_unescaped)
                        exp_match = re.search(r'<expirationTime>(.+?)</expirationTime>', response_xml_unescaped)
                        
                        if token_match and sign_match and exp_match:
                             self.wsaa.Token = token_match.group(1)
                             self.wsaa.Sign = sign_match.group(1)
                             self.wsaa.Expiracion = exp_match.group(1)
                             print(f"DEBUG: Parseo manual exitoso. Expiracion: {self.wsaa.Expiracion}")
                             
                             # Guardar MANUALMENTE el TA.xml para que la proxima vez lo encontremos
                             if self.cache_dir:
                                 try:
                                     ta_path = os.path.join(self.cache_dir, "TA.xml")
                                     # Guardamos la versión des-escapada que es la que tiene el XML limpio
                                     # OJO: pyafipws espera cierta estructura, pero si lo leemos nosotros manual, basta con que tenga los tags.
                                     # Tratemos de guardar algo limpio.
                                     with open(ta_path, "w", encoding="utf8") as f:
                                         f.write(response_xml_unescaped)
                                     print(f"DEBUG: TA.xml guardado manualmente en {ta_path}")
                                 except Exception as save_err:
                                     print(f"DEBUG: No se pudo guardar TA.xml: {save_err}")
                                     
                        else:
                             print("DEBUG: No se encontraron tags en XML manual (post-unescape)")

                if not getattr(self.wsaa, "Expiracion", None):
                   raise Exception(f"LoginCMS no devolvió Expiración. Respuesta: {getattr(self.wsaa, 'Excepcion', 'Desconocida')}")

            except Exception as e:
                print(f"DEBUG: Error en LoginCMS: {e}")
                import traceback
                print(f"DEBUG: TRACEBACK:\n{traceback.format_exc()}")
                raise e
        
        # Configurar WSFE con el token obtenido
        print(f"DEBUG: Seteando Ticket. Expiracion: {getattr(self.wsaa, 'Expiracion', 'MISSING')}")
        
        # Reconstruir XML del Ticket de Acceso para SetTicketAcceso (que espera string XML)
        ta_xml = f'<loginTicketResponse version="1.0"><header><expirationTime>{self.wsaa.Expiracion}</expirationTime></header><credentials><token>{self.wsaa.Token}</token><sign>{self.wsaa.Sign}</sign></credentials></loginTicketResponse>'
        
        self.wsfe.SetTicketAcceso(ta_xml)
        
        self.wsfe.Cuit = self.cuit
        self.wsfe.Conectar(cache=self.cache_dir, wsdl=self.wsdl_wsfe)
        
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
