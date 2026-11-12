# Investigación (fase 0): Terreno y cazador

**Feature**: `001-terreno-cazador` · **Spec**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

Este archivo resuelve las decisiones abiertas del plan. Cada una tiene problema, alternativas,
decisión, complejidad, medición prevista y límites conocidos, como pide el Principio VIII.
Las mediciones se completan al implementar. La sección final de `DECISIONES.md` (§5.1, §5.2,
§5.6) se escribe a partir de aquí e indica si la decisión final coincide con esta.

Notación: S = salas de la cripta, E = salidas, S_r y E_r = salas y salidas a costo ≤ r del
jugador, k = cazadores activos, g = grado de una sala (≤ 4).

Vocabulario: una **puerta** está abierta o cerrada; una **sala** de la búsqueda está **resuelta**
cuando su distancia ya es definitiva.

---

## R0. Revisión de las estructuras existentes (Principio II)

| Estructura (P1) | Qué hace hoy | Limitación frente a esta feature | Qué se hace |
|---|---|---|---|
| `Logic/ColaEventos.py` | Montículo binario de `EventoProgramado`, desempate por secuencia. Registra cada `programar` y cada extracción en `HistorialRetroceso`. | Está atado a eventos (`tiempo`, `secuencia`, `cancelar`) y al historial. Una búsqueda de rutas no es estado del juego y haría miles de registros inútiles por decisión. No sirve como cola de la búsqueda sin modificarla. | No se toca. La búsqueda usa un montículo nuevo en `Estructuras` (R1). Se vuelve a medir con la carga nueva (R6). |
| `Logic/Comportamientos.py` | `decidir()` devuelve una **sala destino** o `None`. | El costo del movimiento depende de la **salida**, no del destino. Con dos salidas hacia la misma sala, el destino no basta para saber qué costo pagar (FR-104, FR-119). | Se agrega `decidir_paso()` (destino y costo) en la clase base, con una implementación por defecto que usa `decidir()`. `Errante` la redefine para pagar la salida sorteada. `Cazador` es una clase nueva que se suma a `COMPORTAMIENTOS`. |
| `Logic/Mazmorra.py` | `salidas_abiertas()` devuelve destinos **sin costo**. `SalidaViva` no guarda costo. Las puertas cambian en `abrir_puerta()` y `CierrePuerta.activar()`. | No hay costo por salida ni forma de enterarse de que una puerta cambió (lo necesita la invalidación, R4). Además, el costo puede venir declarado en un solo lado (§4.1), igual que la llave, que ya iguala `_igualar_caras`. | `SalidaViva.costo` y `costo_declarado`, y `_igualar_costos()` junto a `_igualar_caras()` (sin modificarlo). Métodos nuevos que devuelven destino y costo, y un aviso de cambio de puerta en los dos puntos donde cambian. |
| `Logic/motorJuego.py` | `mover_jugador()` usa `COSTO_MOVER` (100). `turno_enemigo()` programa siempre 100. | Contradice FR-102 para el jugador y para los enemigos. | El jugador paga `salida.costo`. `turno_enemigo()` paga el costo que devuelve `decidir_paso()`, o 100 si espera o ataca. `cambiar_velocidad()` ya cumple FR-105 y no se toca. |
| `Logic/HistorialRetroceso.py` | Funciones de reversión por intervalo, 5 intervalos. | Ninguna. La caché de rutas se integra registrando en él (R4). | No se toca. |
| `Estructuras/Cola.py` | FIFO enlazada (BFS de `GestorContenido`). | Un BFS cuenta salas. Con costos no uniformes, contar salas no da la ruta más barata (§5.1, caso 3 del Apéndice B). | No sirve para la búsqueda. |
| `Estructuras/Ordenador.py` | Ordenamiento estable propio. | Ordenar toda la frontera en cada paso cuesta O(n log n) por extracción. | No sirve como cola de prioridad. |
| `Estructuras/ListaDoble.py`, `BufferCircular.py` | Inventario y bitácora. | No ofrecen extracción del mínimo. | No se usan. |
| `Logic/BenchLogica.py` | Agenda de eventos y ciclo < 20 ms con errantes y rastreadores. | No hay cazadores ni costos variables (§5.6). | Su `medir()` agrega las mediciones nuevas. Las funciones existentes no cambian. |

Hallazgo en los datos: las cuatro criptas de `paquete/` no tienen salidas sin vuelta, ni dos
salidas hacia la misma sala, ni el campo `costo`. Las pruebas de FR-101, FR-104 y FR-119 usan
criptas sintéticas.

---

## R1. Cola de prioridad de la búsqueda

**Problema**: la búsqueda de costo mínimo necesita extraer repetidamente la sala de menor
distancia tentativa (§5.1). `heapq` y `bisect` están prohibidos (Principio II).

| Alternativa | Extraer mínimo | Bajar una clave | Total búsqueda | Notas |
|---|---|---|---|---|
| A. Recorrer un array de salas sin resolver | O(S) | O(1) | O(S²) | La más simple. Cuesta según el tamaño de la cripta, no según la región: incumple NFR-102. |
| B. Generalizar `ColaEventos` | O(log n) | no tiene | — | Habría que separarla de los eventos y del historial: se modifica código P1 que funciona (Principio III). |
| **C. Montículo binario mínimo nuevo, con entradas repetidas («borrado perezoso»)** | O(log E) | se inserta otra entrada | O((S_r + E_r) log E_r) | Una entrada (distancia, sala). Si al extraerla la sala ya estaba resuelta, se descarta. No necesita índice de posiciones. |
| D. Montículo con índice de posiciones y `bajar_clave` | O(log S) | O(log S) | O((S_r + E_r) log S_r) | Un poco menos de memoria que C, pero necesita un array posición-por-sala que se mantiene en cada intercambio. Más código para el mismo orden de complejidad con g ≤ 4. |
| E. Cubetas por distancia (Dial) | O(1) amortizado | O(1) | O(E_r + r) | Barata si los costos son pequeños. Con costos de cientos y `rango` grande hay muchas cubetas vacías, y la memoria crece con el `rango`. |

**Decisión**: C, en `Estructuras/MonticuloMinimo.py`, sin dependencias de capas. Las entradas
se comparan por distancia y luego por id de sala, así el orden interno también es determinista.
El desempate de FR-111 no depende de este orden (ver R3).

**Por qué**: es la opción más simple que cumple NFR-102. Con g ≤ 4, E_r ≤ 4·S_r, y la
diferencia de C frente a D es una constante.

**Medición prevista**: búsqueda completa con C frente a A en cuadrículas de 100, 1 000 y
10 000 salas con costos aleatorios por semilla.

**Límites**: con muchas mejoras sucesivas de la misma sala, el montículo guarda entradas
viejas: hasta E_r entradas en lugar de S_r.

---

## R2. Un cálculo por cazador o uno compartido desde el jugador

**Problema**: hay decenas de cazadores y todos persiguen al mismo jugador (§5.1).

**Observación clave**: el costo es el mismo en ambos sentidos (FR-101). Por lo tanto,
dist(v, jugador) = dist(jugador, v), y una sola búsqueda **desde el jugador** da la distancia de
todas las salas al jugador. Además, el desempate de FR-111 pide justamente dist(v, jugador) para
las vecinas v del cazador. Una búsqueda desde el cazador daría dist(cazador, x), que no sirve para
desempatar sin otra búsqueda.

| Alternativa | Trabajo por ciclo con k cazadores | Notas |
|---|---|---|
| A. Una búsqueda por cazador, desde el jugador, que se detiene al resolver la sala del cazador o al pasar su `rango` | k · O((S_r + E_r) log E_r) | Cada cazador repite casi la misma búsqueda. Es la referencia «desde cero» de las pruebas (FR-114). |
| B. Una búsqueda por cazador, desde el cazador | k búsquedas, más otra para desempatar | Descartada: no da dist(v, jugador). |
| **C. Una búsqueda compartida desde el jugador, reanudable** | O((S_R + E_R) log E_R) una vez, con R = el mayor `rango` consultado, más O(g) por decisión | Se guarda el estado de la búsqueda (distancias, salas resueltas y frontera). Cada cazador la **extiende solo lo que necesita**: hasta resolver su sala o hasta que el mínimo de la frontera pase su `rango`. |

**Decisión**: C. Con un solo cazador hace el mismo trabajo que A, y con k cazadores reparte el
trabajo. La alternativa A se mantiene como función «desde cero» para las pruebas y para la
medición.

**Cuándo cambia la respuesta**: A solo podría ganar si el jugador cambiara de sala entre cada
par de decisiones de cazadores. En ese caso C también recalcula, así que empatan, con el costo
extra de guardar el estado. El bench lo mide.

**Medición prevista**: 1, 10, 30 y 100 cazadores, A frente a C, en la misma cripta y con la
misma secuencia de turnos.

---

## R3. Cortar la búsqueda en el `rango` y corrección del desempate

Consulta de un cazador en la sala u con `rango` r, sobre la búsqueda desde el jugador:

1. Si u ya está resuelta, d = dist(u).
2. Si no, se extraen salas mientras la frontera no esté vacía, su mínimo sea ≤ r y u siga sin resolver.
3. Si u no se resolvió, o d > r, no hay ruta dentro del `rango` y el cazador espera (FR-109).
4. Si se resolvió con d ≤ r, el paso es la vecina v de menor id con costo(u, v) + dist(v) = d. costo(u, v) es el de
   la salida abierta más barata entre u y v (FR-119).

**Por qué basta con lo ya calculado**: toda vecina v que cumple costo(u, v) + dist(v) = d tiene
dist(v) = d − costo(u, v) ≤ d − 1 < d, porque todo costo es ≥ 1 (FR-101). Por lo tanto v se resolvió
**antes** que u y su distancia es definitiva. Una vecina que no está resuelta tiene dist(v) ≥ d, así
que costo(u, v) + dist(v) > d y no puede cumplir la igualdad. El desempate se resuelve mirando solo
las g ≤ 4 salidas de u, y el resultado no depende del orden de la búsqueda (§3.2, FR-111).

**Corte en el `rango`**: con r pequeño, la búsqueda solo resuelve salas a distancia ≤ r del jugador.
El trabajo crece con la región dentro del `rango`, no con la cripta (NFR-102).

**Arrays sin reiniciar**: las distancias y las marcas de sala resuelta viven en arrays (`list`
usada como almacenamiento contiguo, Principio II) de tamaño S, que se crean **una sola vez**.
Cada búsqueda nueva incrementa un número de generación, y una casilla solo vale si su marca
coincide con la generación actual. Empezar una búsqueda nueva cuesta O(1), no O(S).

**Salidas sin vuelta**: la búsqueda desde el jugador recorre las salidas **al revés**: para resolver
x mira las salas que tienen una salida abierta hacia x. Esta adyacencia inversa es estática (no
depende de las puertas) y se arma una vez, en O(S + E). Con salidas siempre de ida y vuelta da lo
mismo que recorrerlas al derecho, y si una cripta trae una salida sin vuelta, sigue siendo correcta.

**Medición prevista**: `rango` 200, 600 y 5 000 sobre cuadrículas de 100, 1 000 y 10 000 salas.
Con `rango` fijo, el tiempo debe quedar aproximadamente constante al crecer la cripta (SC-105).

---

## R4. Qué invalida la búsqueda guardada, y reutilizar frente a recalcular

Lo que entra en el cálculo es solo **la sala del jugador**, **la topología con costos** (fija) y
**el estado de las puertas** (FR-112, FR-120). Cada evento del §5.2:

| Evento entre dos turnos | ¿Afecta? | Regla |
|---|---|---|
| El jugador cambia de sala | Sí, cambia el origen | Al consultar se compara el origen guardado con la sala actual del jugador. Si difieren, se empieza una búsqueda nueva. No hace falta aviso. |
| Se abre o se cierra una puerta (llave o cierre automático) entre a y b | Solo si a o b ya están **resueltas** en la búsqueda | Una salida u→v solo se lee al resolver v (R3). Si ningún extremo está resuelto, la salida todavía no se leyó, y cuando se lea se leerá con su estado nuevo. Si alguno está resuelto, se descarta la búsqueda. Por eso el aviso puede llevar solo los destinos de las caras que cambiaron. |
| Un cazador u otro enemigo se mueve | No | El origen es el jugador y los actores no bloquean (FR-120). |
| Muere un actor | No | Ídem. |
| Cambia la velocidad de un actor | No | Solo cambia cuándo actúa (FR-105), no la ruta. |
| Se carga el contenido de una sala | No | FR-112. |
| Pergamino de retroceso | Sí | Ver «Historial». |
| Se carga una partida guardada o un replay | — | El motor nuevo empieza sin búsqueda guardada. |

**Historial (pedido del usuario: «toda caché que sea estado del juego se registra en
HistorialRetroceso»)**: la búsqueda guardada es un dato derivado, no estado del juego. Aun así,
**cada vez que se crea, se extiende o recibe un aviso de puerta**, registra en el historial una
reversión que la **descarta**. Si un pergamino deshace un intervalo en el que la búsqueda o una
puerta cambiaron, la búsqueda queda descartada y la siguiente consulta empieza desde cero. Si en
ese intervalo no cambió ninguna de las dos, la búsqueda sigue siendo válida para el estado
restaurado. Así no se copian estructuras (no se usa `copy`, Principio II) y deshacer sigue
costando O(cambios del intervalo).

**Garantía de FR-114**: con estas reglas, la búsqueda guardada siempre es la que habría producido
una búsqueda desde cero desde el mismo origen con las puertas actuales, extendida hasta el mismo
punto. Por R3, la decisión es idéntica. Las pruebas lo verifican comparando, en cada turno de cada
cazador, contra la alternativa A de R2.

| Alternativa | Trabajo con puertas estables | Con puertas inestables | Complejidad |
|---|---|---|---|
| A. Recalcular siempre | k búsquedas por ciclo | Igual | Mínima |
| B. Descartar ante **cualquier** cambio de puerta | 1 búsqueda por cambio de sala del jugador | 1 por cada cambio de puerta | Baja |
| **C. Descartar solo si la puerta toca una sala resuelta** | Igual que B | Solo los cambios cercanos al jugador descartan | Una comprobación O(1) por aviso |

**Decisión**: C. Una puerta que se cierra lejos de todos los cazadores no descarta nada (§8,
pregunta 2 del enunciado).

**Medición prevista**: A, B y C con puertas estables (sin cambios) y con puertas inestables
(cierres automáticos frecuentes, cerca y lejos del jugador), contando búsquedas reales por ciclo
y tiempo por ciclo (§5.2, §6.3).

**Límites**: un jugador que cambia de sala en cada decisión obliga a una búsqueda nueva por
decisión del jugador. Sigue siendo una sola búsqueda para todos los cazadores.

---

## R5. La misma búsqueda para «ir a» (§5.3)

**Problema**: «ir a» (feature 002, integrantes 2 y 3) calcula la ruta del jugador sobre el
**mapa conocido**, con el mismo desempate. Lo pide el §5.3 del enunciado, no un requisito de la
spec 001.

**Decisión**: la búsqueda y la elección del paso reciben el **grafo como parámetro**. Un grafo
es cualquier objeto que responde:

- `cantidad_salas()`: el tamaño de los arrays;
- `entradas(x)`: pares (origen, costo) de las salidas **utilizables** que llegan a x;
- `salidas(u)`: pares (destino, costo) de las salidas utilizables de u.

Para el cazador, «utilizable» es «abierta ahora» sobre el esqueleto real. Para «ir a», el
integrante 2 da un grafo con las salas exploradas y las puertas como se recuerdan. «Ir a» busca
**desde la sala destino**, y el jugador da un paso con la misma regla de R3. El cazador es el caso
«origen = jugador».

**Por qué no es YAGNI (Principio III)**: el cazador ya necesita separar la búsqueda de la
`Mazmorra` para probarla con grafos pequeños (FR-111, FR-114), así que el parámetro no agrega
código. Lo que se agrega para «ir a» es solo el contrato.

**Alternativa descartada**: dos búsquedas separadas. Duplicaría el código y el desempate, y las
pruebas del Apéndice B solo cubrirían una.

**Límites**: el paso de «ir a» debe tardar menos de 5 ms (§6.1). Su medición es del integrante 3,
sobre el grafo del integrante 2. Ver el [contrato](contracts/busqueda-rutas.md).

---

## R6. Revisión de decisiones de la primera parte (§5.6)

- **Agenda de eventos** (Principio VIII: las mediciones de P1 se repiten con la carga nueva): se
  repite la comparación de `medir_agenda`, montículo frente a array ordenado, con los tiempos que
  generan costos entre 1 y 300 y velocidades distintas (`medir_agenda_con_costos`). También se mide
  el ciclo con 30 cazadores en una cuadrícula de 1 000 salas. Con costos variables, los tiempos de los eventos se dispersan más. Se espera
  que el montículo siga siendo adecuado frente al array ordenado. Si los datos dicen otra cosa,
  se documenta el antes y el después en `DECISIONES.md`.
- **Historial de retroceso**: la búsqueda guardada agrega a lo sumo un registro por cada
  creación, extensión o aviso de puerta. Se mide cuántos registros más hay por intervalo con 30
  cazadores (la medición base es del integrante 3).

---

## R7. Contrato de datos

**Confirmado con el integrante 2 el 11 de noviembre, tal como está.** Ver
[contracts/contrato-datos.md](contracts/contrato-datos.md).

- `SalidaDTO.costo: int | None = None`: el costo **declarado** en ese lado, o `None` (FR-101). Es
  del integrante 2. Con `int = 100`, Lógica no podría distinguir «no declarado» de «declarado 100»,
  y no sabría qué lado manda cuando solo uno lo declara. Lógica iguala los dos lados al cargar el
  esqueleto.
- `FichaEnemigoDTO.rango: int | None = None`: es del integrante 1. Tiene que tener valor por
  defecto en Python porque los campos anteriores (`efectos`, `extras`) ya lo tienen, y porque los
  enemigos que no son cazadores no lo traen. «Sin valor por defecto» de FR-122 significa que
  **a un cazador no se le inventa un `rango`**: si un cazador llega con `None` o con un valor
  inválido, Data lo rechaza. `"rango"` se agrega a `_CAMPOS` para que no se duplique en `extras`.
- La validación de FR-122 (incluidos dos lados con costos distintos) vive en Data (Principio I: Data valida formato). Es código del
  integrante 2 y este plan no la incluye.
- Sin cambios en Lógica para validar: Lógica confía en el DTO.
