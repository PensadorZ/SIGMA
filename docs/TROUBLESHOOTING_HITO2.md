# TROUBLESHOOTING_HITO2.md

**SIGMA v1.5+ · Incidentes reales de Hito 2 en adelante**
Autor: Prof. Marx Agustín García Delgado · Versión: 1.0.0

Archivo separado de `TROUBLESHOOTING.md` (Hito 1, cerrado — 65/65 tests,
ya no recibe nuevos incidentes). Numeración propia (`H2-N`) para no
colisionar con la numeración del archivo de Hito 1.

---

## Incidente H2-1 — Gherkin en español requiere `# language: es` explícito

**Fecha:** Julio 2026, sesión de construcción de `0004-statistical-validator`.

**Síntoma esperado si no se corrige:** un `.feature` escrito enteramente
en español (`Característica`, `Escenario`, `Dado`, `Cuando`, `Entonces`)
puede no ser reconocido correctamente por el parser de Gherkin
(`gherkin-official`, usado por `pytest-bdd`) sin la directiva de idioma,
dependiendo de la configuración del entorno.

**Causa:** el estándar Gherkin asume inglés (`Feature`, `Scenario`,
`Given`) salvo que el archivo declare explícitamente otro idioma. Esto
se había asumido tácito en todos los `.feature` de SIGMA — nunca se
verificó si `0000`-`0003`, `0008`, `0011` lo declaran o si simplemente
nunca se topó con el caso donde fallaba.

**Corrección:** toda `.feature` nueva de SIGMA debe iniciar con:

```gherkin
# language: es
```

como primera línea con contenido (después del comentario de encabezado
del archivo). Verificado y aplicado en
`tests/test_statistical_validator.feature` de `0004`.

**Pendiente de auditar:** confirmar si los `.feature` de `0000-0003,
0008, 0011` ya la tienen o si pasaron por pura suerte de configuración
del entorno. No se audita en esta entrada — se registra como deuda de
verificación para no bloquear el cierre de Rollout 1 por algo que ya
funciona en la práctica.

**AUDITORÍA CERRADA (misma sesión):** verificado con
`findstr /S /M /C:"language: es" *.feature` sobre los 6 `.feature` de
Hito 1 (`0000, 0001, 0002, 0003, 0008, 0011`) — **los 6 ya tienen la
directiva**. No fue suerte de configuración: estaba correctamente
declarada desde su creación. Sin cambios de código requeridos. Cierre:
✅ resuelto, sin acción pendiente.

**Relación con ADR-009:** la especificación de los siete artefactos
canónicos debería declarar esto como requisito explícito del artefacto
`tests/*.feature`, no dejarlo como convención implícita. Candidato a
incluirse en la próxima revisión de ADR-009.

---

## Incidente H2-2 — carpeta `0004-statistical-validator` duplicada al descomprimir el zip

**Fecha:** Julio 2026, misma sesión que H2-1.

**Síntoma:** al descomprimir el `.zip` de la suite de `0004` dentro de
`sigma\skills\0004-statistical-validator\`, quedó anidada una copia
extra: `sigma\skills\0004-statistical-validator\0004-statistical-validator\`.
`_loader.py` no encontraba `skill.py` en la ruta esperada por este motivo.

**Causa:** el `.zip` entregado por Claude ya traía
`0004-statistical-validator\` como carpeta raíz interna. Al
descomprimirlo dentro de una carpeta que ya se llamaba igual, el
nivel se duplicó. Error de empaquetado de Claude, no de Marx.

**Corrección aplicada:**
```bat
robocopy "0004-statistical-validator" "." /E /MOVE
rmdir 0004-statistical-validator
```

**Lección para futuras entregas de archivos vía Claude:** cuando se
entregue un `.zip` cuyo contenido ya sea una carpeta con el mismo
nombre que el destino, indicar explícitamente si debe descomprimirse
"aquí mismo" o "un nivel arriba" — no asumir que es obvio.

**Estado:** ✅ resuelto, verificado con `dir /S /B` mostrando una sola
ruta sin repetición.
