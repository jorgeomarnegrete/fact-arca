from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import ComprobanteCreate, Comprobante
from app.services.invoice_generator import InvoiceService

router = APIRouter()

@router.post("/facturas/", response_model=Comprobante)
def create_invoice(invoice_data: ComprobanteCreate, db: Session = Depends(get_db)):
    service = InvoiceService(db)
    try:
        return service.create_invoice(invoice_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error interno al generar factura: " + str(e))
