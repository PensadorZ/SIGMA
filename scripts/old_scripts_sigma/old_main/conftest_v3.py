"""
conftest.py (raíz del proyecto)

Las carpetas de skills usan el formato canónico `0000-nombre-skill`
(ADR-009 v1.4), que no es un identificador Python válido para import
directo (empieza por dígito y contiene guiones). Este conftest registra
cada skill.py bajo un alias de módulo importable usando importlib,
para que los tests puedan hacer:

    from skills_0000_system_health_check.skill import run_system_health_check

sin tener que renombrar las carpetas y romper la convención de
nomenclatura del ecosistema.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).parent
SKILLS_DIR = ROOT / "skills"


def _register_skill_module(skill_dir_name: str, alias: str) -> None:
    """
    Carga skills/<skill_dir_name>/skill.py y lo registra en sys.modules
    bajo <alias> y <alias>.skill, de modo que tanto
    `import skills_0000_system_health_check` como
    `from skills_0000_system_health_check.skill import X` funcionen.
    """
    skill_py = SKILLS_DIR / skill_dir_name / "skill.py"
    if not skill_py.exists():
        return  # el skill aún no tiene implementación; no es un error fatal

    # Módulo "paquete" vacío bajo el alias, para soportar el import con punto.
    if alias not in sys.modules:
        pkg_spec = importlib.util.spec_from_loader(alias, loader=None)
        pkg_module = importlib.util.module_from_spec(pkg_spec)  # type: ignore[arg-type]
        pkg_module.__path__ = [str(SKILLS_DIR / skill_dir_name)]  # type: ignore[attr-defined]
        sys.modules[alias] = pkg_module

    submodule_name = f"{alias}.skill"
    if submodule_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(submodule_name, skill_py)
        module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        sys.modules[submodule_name] = module
        assert spec and spec.loader
        spec.loader.exec_module(module)
        # Crítico: asignar el submódulo como atributo del paquete padre.
        # sys.modules por sí solo no basta para que monkeypatch.setattr
        # resuelva "alias.skill.func" recorriendo getattr() en cadena.
        setattr(sys.modules[alias], "skill", module)


# Añadir la raíz del proyecto al path para que `import sigma` funcione.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Registro de skills con implementación. Se amplía conforme el Roadmap
# Técnico (Fase 2 en adelante) añade más skill.py reales.
_register_skill_module("0000-system-health-check", "skills_0000_system_health_check")
_register_skill_module("0001-data-ingestion", "skills_0001_data_ingestion")
_register_skill_module("0002-data-cleanser", "skills_0002_data_cleanser")
