import subprocess
import sys
import os

def generate_csr(cuit, common_name="facturador_testing"):
    key_filename = f"PRIVATE_KEY_{cuit}.key"
    csr_filename = f"PEDIDO_{cuit}.csr"
    
    print(f"Generando claves para CUIT {cuit}...")

    # 1. Generar Clave Privada (Private Key)
    # openssl genrsa -out PRIVATE_KEY_{cuit}.key 2048
    try:
        subprocess.run(
            ["openssl", "genrsa", "-out", key_filename, "2048"],
            check=True
        )
        print(f"[OK] Clave Privada generada: {key_filename}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Falló la generación de clave privada: {e}")
        return

    # 2. Generar CSR (Pedido de Firma de Certificado)
    # openssl req -new -key PRIVATE_KEY_{cuit}.key -out PEDIDO_{cuit}.csr -subj "/C=AR/O={cuit}/CN={common_name}/serialNumber=CUIT {cuit}"
    subject = f"/C=AR/O={cuit}/CN={common_name}/serialNumber=CUIT {cuit}"
    try:
        subprocess.run(
            ["openssl", "req", "-new", "-key", key_filename, "-out", csr_filename, "-subj", subject],
            check=True
        )
        print(f"[OK] CSR generado: {csr_filename}")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Falló la generación del CSR: {e}")
        return
    
    print("\n--- PASOS SIGUIENTES ---")
    print(1, "Ingresa a https://wsass-homo.afip.gob.ar/wsass/main")
    print(2, "Logueate con tu CUIT y Clave Fiscal (La misma de producción sirve para entrar)")
    print(3, "Ve a 'Crear Certificado de Servicio' (o similar)")
    print(4, f"Sube el archivo {csr_filename}")
    print(5, "Descarga el certificado .crt resultante")
    print(6, "Usa ese .crt y el archivo .key generado aquí para configurar el sistema en Modo TESTING")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python generate_csr.py <CUIT>")
        print("Ejemplo: python generate_csr.py 20142944295")
    else:
        generate_csr(sys.argv[1])
