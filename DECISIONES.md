# Decisiones de diseño — Cripta, segunda parte

Este archivo reúne las decisiones de diseño de la segunda parte (Principio VIII de la constitución). Cada
decisión de estructura de datos indica el problema, las alternativas consideradas, la decisión, su
complejidad, la evidencia empírica (mediciones propias de `--bench`) y los límites conocidos, con enlaces a
la spec y al plan de donde proviene, e indica si la decisión final coincide con la del `plan.md` original.

**El «antes»**: las decisiones de la primera entrega están en
[docs/Documento_Decisiones.pdf](docs/Documento_Decisiones.pdf). Cuando una decisión de la segunda parte
cambia una de la primera (Principio III), se muestra el antes y el después: el antes se cita como
«Documento de Decisiones de la primera entrega, §x» y el después se escribe aquí.

Cada integrante escribe su sección.

---

## Integrante 1 — 001 terreno y cazador (§5.1, §5.2, §5.6)

Spec: [specs/001-terreno-cazador/spec.md](specs/001-terreno-cazador/spec.md) ·
Plan: [specs/001-terreno-cazador/plan.md](specs/001-terreno-cazador/plan.md) ·
Investigación: [specs/001-terreno-cazador/research.md](specs/001-terreno-cazador/research.md)

### §5.1 La ruta más barata del cazador

(se completa en T046 con las mediciones de --bench)

### §5.2 Rutas que dejan de ser válidas

(se completa en T046 con las mediciones de --bench)

### §5.6 Revisión de decisiones de la primera parte

(se completa en T046 con las mediciones de --bench)

### Diferencia conocida entre la verificación y el motor de P1

- **Qué pasa**: la verificación de resolubilidad (003 FR-304) sigue al pie de la letra §3.5 y P1 §2.12:
  la cripta es resoluble si el jugador puede obtener `llave_salida` y llegar a `sala_salida` a través de
  una puerta que requiere `llave_salida`. El motor de la primera parte es más permisivo:
  `Mazmorra.abrir_puerta` activa `salida_abierta` al abrir **cualquier** puerta que pida `llave_salida`,
  aunque esa puerta no dé a `sala_salida`, y después basta con entrar a `sala_salida` por cualquier camino.
- **Decisión**: el motor no se cambia, porque ningún FR lo pide (Principio III: el código de la primera
  entrega que funciona queda cerrado a modificación).
- **Por qué es aceptable**: en esta regla, la diferencia va hacia el lado seguro. Si la verificación dice
  «resoluble», en el motor también se gana: abrir la puerta que requiere `llave_salida` y da a
  `sala_salida` activa `salida_abierta`. Lo contrario sí puede pasar: una cripta que solo se gana abriendo
  otra puerta con `llave_salida` es no resoluble para la verificación, y en ese caso la partida igual se
  puede jugar con `--forzar`.
- **Acuerdo**: con el integrante 2 (dueño de la 003), el 13 de noviembre.

---

## Integrante 2 — 002 y 003

(pendiente)

---

## Integrante 3 — 004

(pendiente)
