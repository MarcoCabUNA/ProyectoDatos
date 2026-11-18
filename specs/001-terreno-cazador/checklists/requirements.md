# Specification Quality Checklist: Terreno con costo por salida y enemigo cazador

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-11-09
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Constitución v1.2.0

- [x] IX: no se nombran estructuras de datos, clases ni módulos; los requisitos usan FR-1xx / NFR-1xx.
- [x] X: los 7 casos del Apéndice B «Terreno y cazador» aparecen como escenarios (H1-4, H1-5, H2-1 a H2-4, H3-1) con tabla de trazabilidad.
- [x] IV: el uso del azar por el cazador queda definido en FR-115 y confirmado en «Clarificaciones».
- [x] V: FR-118 exige las mismas reglas en los modos sin vista.

## Notes

- Las únicas menciones técnicas son las banderas de línea de comandos (`--replay`, `--bench`, etc.) y las fórmulas de tiempo del enunciado. Son parte del contrato observable del juego, no detalles de implementación.
- Sin marcadores [NEEDS CLARIFICATION]. Las decisiones no explícitas en el enunciado quedaron confirmadas en «Clarificaciones» (sesión 2026-11-09).
- La columna «Prueba» de la tabla de trazabilidad se completa con los nombres de las pruebas al implementarlas (tarea T047 de `tasks.md`).
- Revisión cruzada (integrante 3, 2026-11-12): se desmarcaron las casillas que todavía no están cubiertas. Se vuelven a marcar cuando:
  - «All acceptance scenarios are defined» y «X»: cada escenario (H1-9 a H1-11, H2-10 a H2-19, H3-7, H3-8) tiene su prueba corriendo sin `skip` y la tabla del Apéndice B nombra sus pruebas (T047). Hoy siguen con `skip` H2-9, H2-17 a H2-19 (T002, T052, T053), H3-7 (spec 003) y H3-8 (fase 7), y las pruebas de interfaz de H4 (T041).
  - «V»: hay pruebas de FR-118 en `--replay`, `--replay … --hasta`, `--verificar` y `--bench` (T048, specs 003 y 004).
  - «Feature meets measurable outcomes»: `--bench` respalda SC-104 y SC-105 (T042 a T045).
- Fase 7 (integrante 1, 2026-11-13): se marcó «X»: los 7 casos tienen su prueba sin `skip` y la tabla del Apéndice B nombra cada una (T047). Siguen sin marcar:
  - «All acceptance scenarios are defined»: H3-7 sigue con `skip` hasta que exista `--verificar` (spec 003) y faltan las pruebas de interfaz de H4 (T041, integrante 3). H2-9, H2-17 a H2-19 y H3-8 ya corren sin `skip`.
  - «Feature meets measurable outcomes»: `--bench` ya respalda SC-104 (peor ciclo de 5,4 a 7,9 ms con 30 cazadores en 1 024 salas) y SC-105 (con `rango` 200, 1,68 y 1,09 veces al multiplicar por 10 el tamaño), ver `bench-2026-11-13.txt`. Con el mapa conocido de la 002 conectado, `bench-2026-11-15.txt` da con 30 cazadores un peor ciclo de 5,5 a 17,6 ms en 3 corridas: sigue cumpliendo, con menos margen; falta SC-106, que depende de T041.
  - «V»: FR-118 ya tiene pruebas en `--replay` (T048) y en `--bench` (H3-8); faltan `--replay … --hasta` (spec 004) y `--verificar` (spec 003).
- Cierre (2026-11-17): se marcaron las tres casillas que faltaban.
  - «All acceptance scenarios are defined»: H3-7 corre sin `skip` (`test_h3_7_fr118_fr122_verificar_no_depende_de_costos_ni_cazadores`, con `--verificar` de la 003) y las pruebas de interfaz de H4 están en `tests/test_vista_terreno.py` (T041).
  - «Feature meets measurable outcomes»: SC-104 y SC-105 ya estaban respaldadas por `--bench`; SC-106 queda cubierta por las pruebas `test_h4_1_fr116_sc106_…` y `test_h4_2_fr117_sc106_…` de `tests/test_vista_terreno.py` (T041).
  - «V»: FR-118 tiene pruebas en `--replay` (T048), `--bench` (H3-8), `--replay … --hasta` y `--verificar` (`tests/test_modos_sin_vista_terreno.py`).
  - «IX» sigue marcada: la spec ya no nombra clases ni tipos en FR-122 (corrección D2 del análisis).
