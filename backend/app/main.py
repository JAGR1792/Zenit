"""FastAPI application entrypoint para Zenit (Simulador narrativo de misiones espaciales)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import router as v1_router
from app.repositories.data import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Inicializa la base de datos SQLite al arrancar el servicio."""
    init_db()
    yield


app = FastAPI(
    title="Zenit API — Simulador Narrativo de Misiones Espaciales",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router)


@app.get("/")
def root() -> dict[str, str]:
    """Endpoint raíz de verificación del servicio."""
    return {"message": "Zenit API operativa", "docs": "/docs"}


@app.get("/health")
def health() -> dict[str, str]:
    """Healthcheck para orquestadores y despliegue."""
    return {"status": "ok"}
