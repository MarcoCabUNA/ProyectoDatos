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

**Problema.** Cada cazador debe dar un paso por una ruta de costo mínimo hacia el jugador si ese
costo no pasa su `rango` (FR-106 a FR-111), con decenas de cazadores a la vez y sin que la decisión
cueste según el tamaño de la cripta (NFR-101, NFR-102). Detalle en [research.md](specs/001-terreno-cazador/research.md) R1 a R3.

**Antes (primera entrega).** No había búsqueda de rutas: los errantes y los rastreadores deciden mirando
solo sus g ≤ 4 vecinas (Documento de Decisiones de la primera entrega, §4.7), y moverse costaba siempre
100 (`Motor.COSTO_MOVER`; `turno_enemigo` programaba 100). El único recorrido de grafo era el BFS de la
precarga (§4.2), que cuenta salas y no costos.

**Después.**

- **Costo por salida** (FR-101 a FR-105): `SalidaViva.costo`, igual en los dos sentidos al cargar el
  esqueleto (`_igualar_costos`, junto a `_igualar_caras` y sin modificarlo). El jugador y los enemigos
  pagan el costo de la salida que cruzan; esperar y atacar siguen costando 100.
- **Cola de prioridad** (R1): montículo binario mínimo propio (`Estructuras/MonticuloMinimo.py`) con
  entradas repetidas y borrado perezoso. Alternativas: recorrer un array (O(S²)), generalizar
  `ColaEventos` (tocaría código de la primera entrega), índice de posiciones, cubetas por distancia.
- **Una búsqueda compartida desde el jugador** (R2): como el costo es el mismo en los dos sentidos,
  dist(cazador, jugador) = dist(jugador, cazador), y una sola búsqueda sirve a todos los cazadores. Es
  reanudable: cada cazador la extiende solo hasta resolver su sala o pasar su `rango`.
- **Corte en el `rango` y desempate** (R3): toda vecina que cumple costo + dist = d ya está resuelta, así
  que el paso se elige mirando solo las salidas del cazador (FR-111). Los arrays se reservan una vez y una
  búsqueda nueva solo cambia la generación: empezar cuesta O(1).

**Complejidad.** Una búsqueda: O((S_r + E_r) log E_r), con S_r y E_r las salas y salidas a costo ≤ r del
jugador. Cada decisión que reutiliza la búsqueda: O(g). Memoria: O(S) una sola vez, más la frontera.

**Evidencia.**

| Medición | Resultado |
|---|---|
| Montículo frente a array (esquina a esquina) | 100 salas: 0,48 frente a 0,62 ms; 1 024 salas: 4,2 frente a 31,6 ms (7,5 veces) |
| 1 / 10 / 30 / 100 cazadores, 20 ciclos | una búsqueda por cazador: 32 / 268 / 611 / 1 617 ms; compartida: 32 / 63 / 67 / 64 ms (hasta 25 veces menos) |
| `rango` 200, 100 → 1 024 → 10 000 salas | 19,6 → 32,9 → 35,9 µs por decisión: 1,68 y 1,09 veces, **SC-105 se cumple** |
| `rango` 5 000, las mismas cuadrículas | 0,23 → 3,2 → 19,8 ms: crece con la región dentro del `rango`, como se esperaba |
| Ciclo de eventos, 1 024 salas, 30 cazadores | peor ciclo de 7,9 ms (jugador quieto) y 5,4 ms (jugador moviéndose): **NFR-101 y SC-104 se cumplen** |

En todas las mediciones con cazadores, cada decisión se compara con `paso_desde_cero`, y son iguales
(escenario H3-8).

**Límites.** Con un solo cazador, la búsqueda compartida no ahorra nada (empata). Con `rango` grande en
una cripta grande, la búsqueda recorre casi toda la cripta (19,8 ms con 10 000 salas y `rango` 5 000).
Con 100 cazadores el peor ciclo llega a 18,0 ms: cumple, pero con poco margen.

**¿Coincide con el plan?** Sí. Lo que cambió fue la medición de R3: con el jugador siempre en el centro
de cada cuadrícula, la de 10 000 salas dio 2,78 veces. Se debía a que los costos alrededor del centro
eran distintos (12 salas resueltas en lugar de 4), no a la búsqueda. Ahora se promedian 400 posiciones
del jugador. El array de R1 no se mide con 10 000 salas (O(S²)).

Mediciones: `python -m Service.ServicioBench` (`Logic/BenchRutas.py`), tabla completa en [bench-2026-11-13.txt](specs/001-terreno-cazador/bench-2026-11-13.txt). Máquina: AMD Ryzen 5 3600X, 32 GB, Windows 11 Pro, Python 3.12.10. Semilla `SEMILLA = 2026`: los conteos son reproducibles; los tiempos son medianas y dependen de la máquina.

### §5.2 Rutas que dejan de ser válidas

**Problema.** La búsqueda guardada deja de valer cuando cambia algo de lo que depende: la sala del
jugador o el estado de una puerta (FR-112, FR-120). Además, un pergamino puede devolver puertas y salas a
un estado anterior sin avisar. La decisión debe ser siempre la de un cálculo desde cero (FR-114). Detalle
en [research.md](specs/001-terreno-cazador/research.md) R4.

**Antes (primera entrega).** No había nada guardado que se pudiera invalidar. El historial de retroceso
registra una función inversa por cambio, agrupadas por intervalo (Documento de Decisiones de la primera
entrega, §4.6).

**Después.**

- Si el jugador cambió de sala, la siguiente consulta empieza una búsqueda nueva (se compara el origen).
- La `Mazmorra` avisa en los dos lugares donde cambia una puerta (`abrir_puerta` y `CierrePuerta.activar`)
  con los destinos de las caras. La búsqueda se descarta solo si alguno ya está resuelto: una salida u → v
  solo se lee al resolver v, así que si ninguno lo está, la salida se leerá después con su estado nuevo.
- Moverse, morir, cambiar de velocidad o cargar el contenido de una sala no invalidan nada.
- Pergamino: cada vez que la búsqueda se crea, se extiende o recibe un aviso, registra en el historial
  una función que la descarta. Deshacer un intervalo en el que no cambió nada de eso la conserva. No se
  copia nada.

**Alternativas.** A, recalcular siempre (k búsquedas por ciclo); B, descartar ante cualquier puerta;
C, el descarte preciso (elegida).

**Complejidad.** Cada aviso cuesta O(1). Cada registro en el historial cuesta O(1) y hay uno como mucho
por creación, extensión o aviso.

**Evidencia.** 30 cazadores en 1 024 salas, 60 ciclos; búsquedas por ciclo y tiempo por ciclo:

| Escenario | A, recalcular siempre | B, cualquier puerta | C, descarte preciso |
|---|---|---|---|
| Puertas estables | 21,8 · 15,8 ms | 0,20 · 0,55 ms | 0,20 · 0,64 ms |
| Una puerta al azar por ciclo | 20,6 · 14,1 ms | 0,98 · 2,23 ms | 0,67 · 1,60 ms |
| Al azar y una de la sala del jugador | 19,4 · 10,9 ms | 1,00 · 1,76 ms | 1,00 · 1,77 ms |

Las tres deciden lo mismo en cada turno. FR-114 tiene además su evidencia en pruebas: 12 partidas
aleatorias (`TestEquivalenciaAleatoria`, con puertas, cierres automáticos, muertes, velocidades y
pergaminos), unas 11 000 decisiones de cazador, todas iguales a `paso_desde_cero`, con la búsqueda
reutilizada en más del 90 % de ellas. Pruebas de mutación: sin los avisos de puerta fallan 6 o 7 de
las 12 partidas. Sin el descarte registrado para el pergamino, el error solo lo detecta la prueba fija
`test_pergamino_despues_de_abrir_una_puerta_sin_moverse`; en las partidas aleatorias lo detecta, a lo
sumo, 1 de 12.

**Límites.** Una puerta que toca la región resuelta (por ejemplo, una de la sala del jugador) descarta la
búsqueda igual que B. Un jugador que cambia de sala en cada decisión obliga a una búsqueda nueva por
decisión, pero sigue siendo una sola para todos los cazadores.

**¿Coincide con el plan?** Sí. La medición separa las puertas inestables en dos escenarios, porque con
una puerta junto al jugador en cada ciclo B y C empatan.

Mediciones: `python -m Service.ServicioBench` (`Logic/BenchRutas.py`), tabla completa en [bench-2026-11-13.txt](specs/001-terreno-cazador/bench-2026-11-13.txt). Máquina: AMD Ryzen 5 3600X, 32 GB, Windows 11 Pro, Python 3.12.10. Semilla `SEMILLA = 2026`: los conteos son reproducibles; los tiempos son medianas y dependen de la máquina.

### §5.6 Revisión de decisiones de la primera parte

Las decisiones de la primera entrega que esta feature toca se volvieron a medir con la carga nueva
(Principio VIII; [research.md](specs/001-terreno-cazador/research.md) R6).

**Movimiento y turnos enemigos (cambia).**

- *Antes*: moverse costaba 100 fijo (`Motor.COSTO_MOVER`) y `turno_enemigo` programaba siempre la
  siguiente acción a 100 (P1 §2.3).
- *Después*: el jugador paga `salida.costo`, y `turno_enemigo` programa con el costo que devuelve
  `decidir_paso()` (el de la salida cruzada), o 100 si espera o ataca (FR-102 a FR-104). El errante sortea
  entre las salidas con su costo y hace la misma llamada a `randint` que antes (Principio IV). El
  rastreador paga la salida abierta más barata hacia la sala que elige.

**Agenda de eventos (no cambia).**

- *Antes* (Documento de Decisiones de la primera entrega, §4.1): montículo binario frente a array
  ordenado. Con 10 000 eventos, programar y sacar sumaban 6,36 µs frente a 781,92 µs (unas 120 veces
  menos), y el ciclo con 500 enemigos tenía su peor caso en 16,92 ms.
- *Después*: con tiempos de costos entre 1 y 300 y velocidades distintas, con 10 000 eventos el
  montículo programa en 0,81 µs y saca en 5,4 µs, y el array tarda 1 241 µs en programar: unas 200 veces
  menos. Los dos límites conocidos del montículo con invalidación perezosa, con 10 000 eventos:
  - *Mismo tiempo*: el montículo no cambia (0,69 µs para programar y 5,5 µs para sacar). El array
    empeora, a 1 821 µs por evento programado.
  - *Cancelaciones*: con el 50 % cancelado, sacar cuesta 10,2 µs por evento válido. Con el 90 %, cuesta
    60,6 µs y descarta 917 entradas por cada 100 válidas. En el juego no hay tantas cancelaciones juntas:
    salen de muertes, antídotos y cambios de velocidad.
- Con 30 cazadores en 1 024 salas, el peor ciclo es de 7,9 ms.

**Historial de retroceso (no cambia).**

- *Antes* (§4.6): una función inversa por cambio, unos 12 registros por intervalo en partidas reales.
- *Después*: la búsqueda del cazador registra su descarte. Con 30 cazadores agrega 0,02 registros por
  intervalo con el jugador quieto y 1,60 con el jugador moviéndose (sobre 249 y 106 de la partida
  sintética: menos del 1,5 %).

**¿Coincide con el plan?** Sí: el plan esperaba que el montículo siguiera siendo adecuado y que el
historial no cambiara.

**Pendiente.** En esta máquina, la fila de la primera entrega con 500 enemigos (`medir_ciclo`, sin
cazadores) dio un peor ciclo de 21,2 ms y 29,5 ms en dos corridas del 13 de noviembre: «NO cumple». No
es una medición de esta feature (no hay cazadores ni costos), y el Documento de la primera entrega ya
dice que el peor ciclo varía entre corridas. Queda para revisarla con el equipo.

Mediciones: `python -m Service.ServicioBench` (`Logic/BenchRutas.py`), tabla completa en [bench-2026-11-13.txt](specs/001-terreno-cazador/bench-2026-11-13.txt). Máquina: AMD Ryzen 5 3600X, 32 GB, Windows 11 Pro, Python 3.12.10. Semilla `SEMILLA = 2026`: los conteos son reproducibles; los tiempos son medianas y dependen de la máquina.

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
