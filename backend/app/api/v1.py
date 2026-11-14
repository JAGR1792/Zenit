"""Router v1 de la API de Zenit (Simulador narrativo de misiones espaciales)."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException
from app.repositories.data import obtener_mision
from app.schemas.mission import (
    CrearMisionRequest,
    DecisionRequest,
    DecisionResponse,
    EstadoMision,
    EventoMision,
    InformeFinal,
    ResolverEventoRequest,
)
from app.services.mission_service import (
    crear_nueva_mision,
    listar_eventos_activos,
    obtener_catalogo_completo,
    obtener_informe_mision,
    procesar_avance_etapa,
    procesar_decision_mision,
    resolver_evento_mision,
)

router = APIRouter(prefix="/api/v1", tags=["missions"])


@router.get("/catalog")
def get_catalog() -> dict[str, Any]:
    """Devuelve el catálogo completo de componentes con ficha técnica, destinos y tripulación."""
    return obtener_catalogo_completo()


@router.post("/missions", response_model=EstadoMision, status_code=201)
def create_mission(req: CrearMisionRequest) -> EstadoMision:
    """Crea una nueva misión espacial y devuelve su estado inicial."""
    return crear_nueva_mision(req)


@router.get("/missions/{mission_id}", response_model=EstadoMision)
def get_mission(mission_id: str) -> EstadoMision:
    """Obtiene el estado completo de la misión."""
    estado = obtener_mision(mission_id)
    if not estado:
        raise HTTPException(
            status_code=404, detail=f"Misión '{mission_id}' no encontrada."
        )
    return estado


@router.post("/missions/{mission_id}/decisions", response_model=DecisionResponse)
def post_decision(mission_id: str, req: DecisionRequest) -> DecisionResponse:
    """Valida y ejecuta una decisión devolviendo la tabla de variables afectadas."""
    resp = procesar_decision_mision(mission_id, req)
    if not resp:
        raise HTTPException(
            status_code=404, detail=f"Misión '{mission_id}' no encontrada."
        )
    return resp


@router.post("/missions/{mission_id}/advance", response_model=DecisionResponse)
def advance_mission_stage(mission_id: str) -> DecisionResponse:
    """Avanza a la siguiente etapa de la misión verificando restricciones críticas y operativas."""
    resp = procesar_avance_etapa(mission_id)
    if not resp:
        raise HTTPException(
            status_code=404, detail=f"Misión '{mission_id}' no encontrada."
        )
    return resp


@router.get("/missions/{mission_id}/events", response_model=list[EventoMision])
def get_mission_events(mission_id: str) -> list[EventoMision]:
    """Lista los eventos activos en el estado actual de la misión."""
    eventos = listar_eventos_activos(mission_id)
    if eventos is None:
        raise HTTPException(
            status_code=404, detail=f"Misión '{mission_id}' no encontrada."
        )
    return eventos


@router.post(
    "/missions/{mission_id}/events/{event_id}/resolve", response_model=DecisionResponse
)
def resolve_mission_event(
    mission_id: str,
    event_id: str,
    req: ResolverEventoRequest,
) -> DecisionResponse:
    """Resuelve o consulta a Tierra sobre un evento activo."""
    resp = resolver_evento_mision(mission_id, event_id, req.option_id)
    if not resp:
        raise HTTPException(
            status_code=404, detail=f"Misión '{mission_id}' no encontrada."
        )
    return resp


@router.get("/missions/{mission_id}/report", response_model=InformeFinal)
def get_mission_report(mission_id: str) -> InformeFinal:
    """Calcula y devuelve el informe final multidimensional con la escena del jefe."""
    informe = obtener_informe_mision(mission_id)
    if not informe:
        raise HTTPException(
            status_code=404, detail=f"Misión '{mission_id}' no encontrada."
        )
    return informe
