from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models import get_db, Service

router = APIRouter()


@router.get("/services")
def list_services(
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(100, ge=1, le=1000),
):
    services = db.query(Service).limit(limit).all()
    return [
        {"id": str(s.id), "nome": s.nome, "orgao": s.orgao, "chunks": len(s.chunks)}
        for s in services
    ]



@router.get("/services/{service_id}")
def get_service(service_id: str, db: Annotated[Session, Depends(get_db)]):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    return {
        "id": str(service.id),
        "nome": service.nome,
        "orgao": service.orgao,
        "markdown_content": service.markdown_content,
        "chunks": [
            {"id": str(c.id), "index": c.chunk_index, "content": c.content}
            for c in sorted(service.chunks, key=lambda c: c.chunk_index)
        ],
    }