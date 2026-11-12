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
- [ ] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [ ] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Constitución v1.2.0

- [x] IX: no se nombran estructuras de datos, clases ni módulos; los requisitos usan FR-1xx / NFR-1xx.
- [ ] X: los 7 casos del Apéndice B «Terreno y cazador» aparecen como escenarios (H1-4, H1-5, H2-1 a H2-4, H3-1) con tabla de trazabilidad.
- [x] IV: el uso del azar por el cazador queda definido en FR-115 y confirmado en «Clarificaciones».
- [ ] V: FR-118 exige las mismas reglas en los modos sin vista.

## Notes

- Las únicas menciones técnicas son las banderas de línea de comandos (`--replay`, `--bench`, etc.) y las fórmulas de tiempo del enunciado. Son parte del contrato observable del juego, no detalles de implementación.
- Sin marcadores [NEEDS CLARIFICATION]. Las decisiones no explícitas en el enunciado quedaron confirmadas en «Clarificaciones» (sesión 2026-11-09).
- La columna «Prueba» de la tabla de trazabilidad se completa con los nombres de las pruebas al implementarlas (tarea T047 de `tasks.md`).
- Revisión cruzada (integrante 3, 2026-11-12): se desmarcaron las casillas que todavía no están cubiertas. Se vuelven a marcar cuando:
  - «All acceptance scenarios are defined» y «X»: cada escenario (H1-9 a H1-11, H2-10 a H2-19, H3-7, H3-8) tiene su prueba corriendo sin `skip` y la tabla del Apéndice B nombra sus pruebas (T047). Hoy siguen con `skip` H2-9, H2-17 a H2-19 (T002, T052, T053), H3-7 (spec 003) y H3-8 (fase 7), y las pruebas de interfaz de H4 (T041).
  - «V»: hay pruebas de FR-118 en `--replay`, `--replay … --hasta`, `--verificar` y `--bench` (T048, specs 003 y 004).
  - «Feature meets measurable outcomes»: `--bench` respalda SC-104 y SC-105 (T042 a T045).
