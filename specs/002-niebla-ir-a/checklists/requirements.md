# Specification Quality Checklist: Niebla de guerra y mapa conocido (parte del integrante 2)

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-11-12
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

## Notes

- Sesión de clarificación 2026-11-12: se resolvieron los tres marcadores (FR-204 → la sala de origen de una
  salida sin vuelta sigue desconocida y la puerta solo se observa desde la sala de la que sale; FR-212 →
  puertas «sin observar»; FR-215 → la antorcha solo tiene efecto al entrar) y se confirmó FR-220 (ver el mapa
  es una consulta). Quedan registrados en la sección «Clarificaciones» de la spec.
- SC-206 se mide en la misma cripta sintética que la feature 001 (NFR-101 y SC-104: 1 000 salas en cuadrícula
  con 30 cazadores activos), con la antorcha encendida.
- Sesión de clarificación 2026-11-13 (revisión cruzada del integrante 1 y acuerdos con el integrante 3): nuevo
  FR-225 (lo que el mapa conocido ofrece a «ir a», escenario H2-5); FR-205 y FR-219 usan el costo igualado de
  001 FR-101 (escenario H5-6); FR-217 tiene una excepción explícita para el reporte de resolubilidad de 003
  FR-313 (escenario H5-7); NFR-203 limita las inversas al pergamino y FR-223 aclara que la línea de tiempo
  reconstruye el mapa conocido hacia adelante. SC-202 excluye el reporte de resolubilidad. Ningún requisito
  existente cambió de número y no se tocó la tabla del Apéndice B.
- Segunda tanda de la revisión cruzada del integrante 1 (puntos MEDIA y BAJA, 2026-11-13): el estado recordado
  de las puertas es por cara y una salida cuenta como recordada abierta solo si se recuerda abierta la cara de
  la sala de la que sale (Convenciones, FR-207, FR-208, FR-225, entidad; escenario H2-6); escenarios nuevos
  H1-7 (cazador, FR-218) y H3-8 (antorcha que se apaga en el mismo instante, 001 FR-108); nuevo SC-207;
  SC-202 reescrito para comprobarse en cada acción; SC-206 usa la cripta de 001; «(decisión del grupo)»
  marcado donde corresponde; «Fuente» y «Fuera de alcance» completados. En la tabla del Apéndice B solo
  cambió la etiqueta repetida «2» por «2a» y «2b». Ningún requisito ni escenario existente cambió de número.
- Segunda revisión del integrante 1 (2026-11-13): en Convenciones («Puerta») y en la aclaración de la
  sesión 2026-11-13 sobre las caras, las caras también pueden diferir si las dos declaran llave (la misma o
  distintas) con distinto estado, porque la primera parte no iguala dos caras que declaran llave (alineado
  con 003 FR-302); FR-225 reacomodado sin cambiar el texto; la tabla de escenarios adicionales usa la
  columna «Adicional» con filas A1 a A43 en el mismo orden (incluidas las del integrante 3, solo cambió la
  etiqueta); el caso borde del reporte con `--forzar` cita «003 H4-4». Ningún requisito ni escenario cambió
  de número y no se tocó el contenido de FR-250 a FR-299 ni de las historias 6 y 7.
- Los 25 requisitos FR-201 a FR-225 tienen al menos un escenario; no hay identificadores FR-0xx.
- La sección «ir a» (FR-250 a FR-299) la escribió el integrante 3 en su propio commit.
- La spec no nombra estructuras de datos, clases, módulos ni algoritmos (Principio IX). Lista para
  `/speckit-plan`.
