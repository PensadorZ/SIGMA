"""
sigma/core/config.py

Gestión de configuración y secretos según ADR-010 (12-Factor).
Principio de Inyección Cero: ningún string literal de credencial
vive en el código fuente.

get_required_env() falla rápido si la variable no está definida,
implementando el comportamiento fail-fast exigido por ADR-006
(ContextResolver) para que un sistema mal configurado nunca arranque
silenciosamente con valores incorrectos.
"""

from __future__ import annotations

import os
from typing import Optional


class ContextResolutionError(RuntimeError):
    """
    Se lanza cuando una variable de entorno requerida no está definida.
    Mensaje incluye el nombre de la variable y, si se proporciona,
    las fuentes que se intentaron consultar (ADR-006).
    """


def get_required_env(name: str, default: Optional[str] = None) -> str:
    """
    Obtiene una variable de entorno obligatoria. Si `default` se
    proporciona, se usa como fallback. Si no hay default y la
    variable falta, lanza ContextResolutionError inmediatamente.
    Nunca registra el valor resuelto en logs ni en Langfuse.
    """
    value = os.environ.get(name)
    if value is not None:
        return value
    if default is not None:
        return default
    raise ContextResolutionError(
        f"Variable de entorno requerida '{name}' no está definida. "
        f"Fuentes consultadas: os.environ. "
        f"Define '{name}' en tu archivo .env (ver .env.example) o pásala "
        f"como variable de entorno antes de ejecutar SIGMA."
    )


def get_optional_env(name: str, default: str = "") -> str:
    """
    Obtiene una variable de entorno opcional. Nunca lanza excepción;
    devuelve `default` si la variable no está definida.
    """
    return os.environ.get(name, default)


def get_sigma_variant() -> str:
    """
    Devuelve la variante de costo activa de SIGMA: SIGMA-FE (Full
    Engineer, $0) | SIGMA-LE (Low-Cost) | SIGMA-ME (Medium-Cost) |
    SIGMA-HE (High-Cost). Las variantes son independientes del
    submodo (ver get_sigma_submode).
    """
    variant = get_optional_env("SIGMA_VARIANT", "SIGMA-FE")
    valid_variants = {"SIGMA-FE", "SIGMA-LE", "SIGMA-ME", "SIGMA-HE"}
    if variant not in valid_variants:
        raise ContextResolutionError(
            f"SIGMA_VARIANT='{variant}' no es válido. "
            f"Valores aceptados: {sorted(valid_variants)}."
        )
    return variant


def get_sigma_submode() -> str:
    """
    Devuelve el submodo transversal activo: Dev | Runtime. Aplica a
    cualquier variante de costo (ej. "SIGMA-FE en modo Dev").
    """
    submode = get_optional_env("SIGMA_SUBMODE", "Dev")
    valid_submodes = {"Dev", "Runtime"}
    if submode not in valid_submodes:
        raise ContextResolutionError(
            f"SIGMA_SUBMODE='{submode}' no es válido. "
            f"Valores aceptados: {sorted(valid_submodes)}."
        )
    return submode


def is_dev_mode() -> bool:
    """Atajo usado por los skills para aplicar overrides de modo Dev."""
    return get_sigma_submode() == "Dev"