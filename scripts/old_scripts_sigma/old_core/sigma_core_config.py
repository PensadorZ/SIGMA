"""
sigma/core/config.py

Gestión de configuración y secretos según ADR-010 (Directiva de
Remediación de Secretos, 12-Factor). Principio de Inyección Cero:
ningún string literal de credencial vive en el código fuente.

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
    Obtiene una variable de entorno obligatoria.

    Si `default` se proporciona, se usa como fallback cuando la
    variable no está definida (comportamiento equivalente a
    ${VAR:-default} de ADR-006). Si no hay default y la variable
    falta, lanza ContextResolutionError inmediatamente.

    Nunca registra el valor resuelto en logs ni en Langfuse, solo
    el nombre de la variable (ADR-006: "El ContextResolver registra
    el nombre del placeholder y la fuente de resolución, nunca el
    valor resuelto").
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
    Devuelve la variante activa de SIGMA: Full | Lite | Dev | Runtime.

    El nombre técnico canónico es "Full" (no "ZERO"). "SIGMA ZERO" es
    el nombre comercial de la variante Full, usado solo en documentación
    orientada al usuario, nunca en código ni en comparaciones de variable.
    """
    variant = get_optional_env("SIGMA_VARIANT", "Dev")
    valid_variants = {"Full", "Lite", "Dev", "Runtime"}
    if variant not in valid_variants:
        raise ContextResolutionError(
            f"SIGMA_VARIANT='{variant}' no es válido. "
            f"Valores aceptados: {sorted(valid_variants)}. "
            f"Nota: el nombre técnico de la variante gratuita es 'Full', "
            f"no 'ZERO'. 'SIGMA ZERO' es solo el nombre comercial."
        )
    return variant


def is_dev_mode() -> bool:
    """Atajo usado por los skills para aplicar overrides de modo Dev (ADR-002)."""
    return get_sigma_variant() == "Dev"
