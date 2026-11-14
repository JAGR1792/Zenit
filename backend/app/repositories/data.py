"""Repositorio de persistencia del estado de misión (SQLite + caché en memoria para serverless)."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from app.schemas.mission import EstadoMision

_MEM_STORE: dict[str, str] = {}


def _obtener_ruta_db() -> str:
    """Determina una ruta escribible para SQLite (compatible con desarrollo local y Vercel /tmp)."""
    if os.environ.get("VERCEL"):
        return "/tmp/zenit_missions.db"
    ruta_local = Path(__file__).resolve().parents[2] / "space_mission.db"
    return str(ruta_local)


def init_db() -> None:
    """Inicializa la tabla de misiones en SQLite si el sistema de archivos lo permite."""
    try:
        with sqlite3.connect(_obtener_ruta_db()) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS missions (
                    id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.commit()
    except sqlite3.Error:
        # En entornos efímeros restringidos se mantiene el respaldo en _MEM_STORE
        pass


def guardar_mision(estado: EstadoMision) -> EstadoMision:
    """Persiste el estado completo de la misión en JSON."""
    raw = estado.model_dump_json()
    _MEM_STORE[estado.id] = raw
    try:
        with sqlite3.connect(_obtener_ruta_db()) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO missions (id, payload_json) VALUES (?, ?)",
                (estado.id, raw),
            )
            conn.commit()
    except sqlite3.Error:
        pass
    return estado


def obtener_mision(mission_id: str) -> EstadoMision | None:
    """Recupera el estado de una misión por su identificador."""
    if mission_id in _MEM_STORE:
        return EstadoMision.model_validate_json(_MEM_STORE[mission_id])
    try:
        with sqlite3.connect(_obtener_ruta_db()) as conn:
            row = conn.execute(
                "SELECT payload_json FROM missions WHERE id = ?",
                (mission_id,),
            ).fetchone()
            if row:
                _MEM_STORE[mission_id] = row[0]
                return EstadoMision.model_validate_json(row[0])
    except sqlite3.Error:
        pass
    return None
