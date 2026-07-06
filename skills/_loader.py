# =============================================================================
# skills/_loader.py — Cargador dinámico de skills
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1 / Eco MultiAgentes 4 Skills 2
# Autor: Prof. Marx Agustín García Delgado
# =============================================================================
# Resuelve el problema de que las carpetas de skill tienen guion y prefijo
# numérico (ej. '0008-sentiment-analyzer'), lo cual NO es un identificador
# Python válido y por lo tanto no se puede importar con la sintaxis normal
# de paquetes: `from skills.0008-sentiment-analyzer.skill import run` es
# un SyntaxError, no un ImportError — no hay forma de arreglarlo con imports
# relativos ni con __init__.py.
#
# La solución es cargar cada skill.py directamente por RUTA DE ARCHIVO con
# importlib.util, sin pasar por el sistema de paquetes con puntos. Esto es
# exactamente la técnica ya usada y verificada en Eco MultiAgentes 3 Skills 1
# para 0000-system-health-check, generalizada aquí para los 6 skills del
# Hito 1.
#
# Uso:
#   from skills._loader import load_skill
#   mod_0008 = load_skill("0008-sentiment-analyzer")
#   resultado = mod_0008.run(state)
# =============================================================================

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

# Carpeta skills/ — raíz desde la que se resuelven todas las rutas de skill.
_SKILLS_ROOT = Path(__file__).parent

# Caché de módulos ya cargados — evita releer y reejecutar skill.py
# en cada invocación dentro del mismo proceso.
_loaded_skills: dict[str, ModuleType] = {}


class SkillNotFoundError(Exception):
    """
    Se lanza cuando no existe skills/{skill_dir}/skill.py en la ruta
    esperada. Distinta de ModuleNotFoundError para no confundirse con
    fallos de import de dependencias dentro del propio skill.
    """
    pass


def _safe_module_name(skill_dir: str) -> str:
    """
    Convierte '0008-sentiment-analyzer' en un nombre de módulo válido
    para registrar en sys.modules: 'sigma_skill_0008_sentiment_analyzer'.
    Esto es solo para caché interna de Python — nunca se usa para
    importar con sintaxis de puntos, así que no está sujeto a las
    restricciones de identificador que motivan este cargador.
    """
    return "sigma_skill_" + skill_dir.replace("-", "_")


def load_skill(skill_dir: str, *, force_reload: bool = False) -> ModuleType:
    """
    Carga skills/{skill_dir}/skill.py como módulo Python y lo devuelve.

    Args:
        skill_dir:     nombre exacto de la carpeta, ej. '0008-sentiment-analyzer'.
        force_reload:  si True, ignora la caché y vuelve a ejecutar skill.py.
                        Útil en tests que necesitan un módulo "limpio" entre
                        escenarios, aunque normalmente monkeypatch es suficiente.

    Returns:
        El módulo cargado, con acceso normal a sus atributos:
        mod.run(state), mod.ModelNotFoundError, etc.

    Raises:
        SkillNotFoundError: si skills/{skill_dir}/skill.py no existe.
    """
    module_name = _safe_module_name(skill_dir)

    if not force_reload and module_name in _loaded_skills:
        return _loaded_skills[module_name]

    skill_path = _SKILLS_ROOT / skill_dir / "skill.py"
    if not skill_path.exists():
        raise SkillNotFoundError(
            f"No se encontró '{skill_path}'. "
            f"Verifica que la carpeta '{skill_dir}' exista dentro de skills/ "
            f"y que contenga un archivo skill.py."
        )

    spec = importlib.util.spec_from_file_location(module_name, skill_path)
    if spec is None or spec.loader is None:
        raise SkillNotFoundError(
            f"No se pudo construir el spec de import para '{skill_path}'."
        )

    module = importlib.util.module_from_spec(spec)

    # Registrar en sys.modules ANTES de ejecutar el módulo. Esto es
    # necesario si skill.py llegara a hacer imports relativos a sí mismo
    # (no es el caso actual, pero es la práctica correcta y evita bugs
    # sutiles si algún skill futuro los necesita).
    sys.modules[module_name] = module

    spec.loader.exec_module(module)

    _loaded_skills[module_name] = module
    return module


def clear_cache() -> None:
    """
    Limpia la caché de módulos cargados. Se usa entre ejecuciones de
    tests cuando force_reload no es suficiente (ej. si el módulo dejó
    estado global mutado que un test posterior no debe heredar).
    """
    for module_name in list(_loaded_skills.keys()):
        _loaded_skills.pop(module_name, None)
        sys.modules.pop(module_name, None)
