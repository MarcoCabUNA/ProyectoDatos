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
del jugador. El array de R1 no se mide con 10 000 salas (O(S²)). Las dos mediciones de cada cambio de
método, con su causa y su evidencia, están en [research.md](specs/001-terreno-cazador/research.md) R3 y R6.

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
- *Con el mapa conocido de la 002* (15 de noviembre): `observador_puertas` ya no es `self.rutas` sino un
  `RepartidorAvisosPuertas([rutas, mapa])` que el `Motor` asigna (002 FR-207), y `Logic/BenchRutas.py` arma el
  mismo repartidor en las dos mediciones que reemplazan las rutas (`medir_ciclo_cazadores`, `medir_historial`).
  En 3 corridas del `--bench` completo, con 30 cazadores el peor ciclo es de 5,5 a 17,6 ms: **NFR-101 y SC-104 se
  siguen cumpliendo**. Con 100 cazadores y el jugador moviéndose (fuera de NFR-101) dio 19,6 / **20,0** / **22,4** ms.
  Medido aparte, alternando el código de antes del merge (sin mapa) y el de ahora, el peor ciclo es de 7,2 a 9,4 ms
  en los dos y las medianas son iguales: el mapa no encarece el ciclo, y el pico depende de lo que corre antes en
  el mismo proceso, como la fila de 500 enemigos de abajo. Tabla en
  [bench-2026-11-15.txt](specs/001-terreno-cazador/bench-2026-11-15.txt).

**Historial de retroceso (no cambia).**

- *Antes* (§4.6): una función inversa por cambio, unos 12 registros por intervalo en partidas reales.
- *Después*: la búsqueda del cazador registra su descarte. Con 30 cazadores agrega 0,02 registros por
  intervalo con el jugador quieto y 1,60 con el jugador moviéndose (sobre 249 y 106 de la partida
  sintética: menos del 1,5 %).

**¿Coincide con el plan?** Sí: el plan esperaba que el montículo siguiera siendo adecuado y que el
historial no cambiara.

**La fila de la primera entrega con 500 enemigos ya fallaba antes de esta feature.** `medir_ciclo`
con 500 errantes y rastreadores, sin cazadores ni costos. Se midió el 13 de noviembre en esta máquina,
en el último commit anterior a la 001 (`83d15c5`, en un `git worktree` aparte) y en la rama actual:

| Cómo se midió | Antes de la 001 (`83d15c5`) | Rama actual |
|---|---|---|
| Sola, 10 corridas alternadas | peor 11,7 a 16,2 ms; mediana 5,37 a 5,67 ms | peor 12,3 a 17,0 ms; mediana 5,37 a 5,68 ms |
| Dentro de `--bench` completo, 3 corridas | peor 17,4 / **20,7** / 16,5 ms | peor **24,3** / **25,0** / **24,0** ms |
| Con el mismo `BenchDatos` actual antes, 4 corridas | peor 18,7 / **21,3** / 17,3 / 17,1 ms | peor 16,8 / 17,8 / 19,6 / 16,9 ms |

En negrita, las que no cumplen. Los dos árboles procesan los mismos ~521 eventos por ciclo y hacen las
mismas 21 pasadas completas del recolector de basura de Python (generación 2) durante la medición.
Cada pasada recorre unos 103 000 objetos y tarda de 10 a 20 ms. El peor ciclo es un ciclo normal
(5 a 8 ms) más una de esas pasadas: con el recolector desactivado, el peor ciclo baja a 7 a 12 ms en
los dos árboles. Por eso la fila queda en el límite y a veces no cumple, con o sin la 001. Ya fallaba
antes: una de las tres corridas del `--bench` completo en `83d15c5` dio 20,7 ms. El Documento de la
primera entrega ya decía que el peor ciclo varía entre corridas (§4.1, límites: un pico de 119 ms).

En el `--bench` completo, la rama actual da un peor ciclo más alto (24 ms frente a 16 a 21 ms). Esa
diferencia no viene del código de la 001. Con lo mismo corriendo antes en el proceso (el `BenchDatos`
actual), el `Logic` de antes y el de ahora dan lo mismo (tercera fila). La diferencia aparece según lo
que corre antes en el mismo proceso, cuyo código (Servicios y Datos) también cambió desde `83d15c5`; no
se aisló qué parte. Queda para revisarla con el equipo; esta feature no cambia nada por eso.

Mediciones: `python -m Service.ServicioBench` (`Logic/BenchRutas.py`), tabla completa en [bench-2026-11-13.txt](specs/001-terreno-cazador/bench-2026-11-13.txt) y, con el mapa conocido conectado, en [bench-2026-11-15.txt](specs/001-terreno-cazador/bench-2026-11-15.txt). Máquina: AMD Ryzen 5 3600X, 32 GB, Windows 11 Pro, Python 3.12.10. Semilla `SEMILLA = 2026`: los conteos son reproducibles; los tiempos son medianas y dependen de la máquina.

**Contenido de una sala con una caché vieja en disco (cambia, T058, FR-122).**

- *Antes* (P1, `Data/GestorContenido.asegurar_sala`, con lo de T052): la sala se entregaba como cargada si ninguna
  de sus fichas estaba entre los rechazos **en memoria**. Con una caché escrita antes de T055/T057 (un enemigo
  guardado sin su `suelta`, o un objeto con `duracion` 0), la ficha inválida aparecía recién dentro de
  `Mazmorra.cargar_contenido`, cuando `ResolvedorCatalogo.ficha()` la volvía a validar al leerla del disco. La
  sala quedaba a medio cargar: los enemigos anteriores agregados, `contadores_tipo` avanzado (incluido el del
  rechazado) y la sala todavía cargada para Data. Con un `ErrorRed` a mitad, el reintento duplicaba los enemigos
  (en la prueba (c), `e-1` dos veces y los números en 2). Un objeto del suelo inválido ni siquiera se detectaba al
  entrar: el movimiento se hacía y el error salía después, sin atrapar, en `SincronizadorUsos`.
- *Después*: antes de devolver la sala, `asegurar_sala` pide `resolvedor.ficha(tipo, contar_acierto=False)` de
  cada enemigo, cada trampa y cada objeto del suelo. Con `ErrorDatos`, la sala queda rechazada (`_rechazar`) y el
  error sale; con `ErrorRed`, sale sin marcar nada y la sala se vuelve a validar en el próximo intento. Lógica
  recibe la sala solo si todas sus fichas son válidas; `Logic/Mazmorra.py` no cambia.
- *Costo*: O(enemigos + trampas + objetos) consultas a `ficha()` por sala que se entra. Las fichas ya están en
  memoria o en disco (las bajó `resolver_contenido`), así que no hay solicitudes nuevas: en una partida con el API
  falso, sin caché y con caché, las solicitudes (6 y 4) y los pedidos de catálogo (2 y 0) son los mismos antes y
  después, y el replay de ejemplo pide los mismos 2 lotes de contenido. Lo que cambia es el reporte de la caché:
  si una ficha se lee del disco aquí, la lectura de `cargar_contenido` que sigue cuenta como acierto (en la
  partida con caché, 3 aciertos en lugar de 1; los fallos y las lecturas de disco no cambian).
- *Acuerdo*: con el integrante 2, dueño del archivo; el cambio lo hizo el integrante 1. Pruebas en
  `tests/test_cache_vieja.py`.

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

Spec: [specs/002-niebla-ir-a/spec.md](specs/002-niebla-ir-a/spec.md) ·
Plan: [specs/002-niebla-ir-a/plan.md](specs/002-niebla-ir-a/plan.md) ·
Investigación: [specs/002-niebla-ir-a/research.md](specs/002-niebla-ir-a/research.md)

### §5.3 Mapa conocido

La parte de «ir a» de §5.3 (el viaje automático que usa este mapa) la escribe el integrante 3 en su sección. Aquí va
la parte del mapa conocido: los tres estados de cada sala, la memoria de puertas por cara, la antorcha, el pergamino,
el guardado y lo que el mapa le ofrece a «ir a» (FR-201 a FR-225, NFR-201 a NFR-205). Detalle en
[research.md](specs/002-niebla-ir-a/research.md) R0 a R7 y en
[contrato-mapa-conocido.md](specs/002-niebla-ir-a/contracts/contrato-mapa-conocido.md).

**Revisión de las estructuras existentes (R0).** Se usa tal cual `HistorialRetroceso` (registrar O(1), deshacer
O(cambios del intervalo)) para el pergamino. La `Mazmorra` se usa **solo para leer** (nombres, salidas, costo
igualado, emparejamiento de caras con `_salida_inversa`); tiene un solo `observador_puertas`, ocupado por las rutas
del cazador. `GrafoEsqueleto` no sirve para «ir a» (su «utilizable» es «abierta ahora», no «recordada abierta»), pero
se copia su idea de adyacencia inversa armada una vez. `BusquedaCostoMinimo` sirve sin cambios porque recibe el grafo
como parámetro. Ninguna estructura de `Estructuras/` ofrece acceso directo por id, y los ids ya son enteros seguidos,
así que no se usan ni se agrega nada a `Estructuras/`. `PartidaGuardada` y `GuardadoBinario` se extienden (decisión 4).

#### 1. Representación: dos arreglos, por sala y por cara (R1)

**Problema.** Tres estados por sala (desconocida, avistada, explorada; FR-201), el estado recordado de cada puerta
**por cara** (abierta, cerrada o sin observar; FR-207, FR-208, FR-212), separado del esqueleto (FR-218), con
consultas que no dependan del tamaño (NFR-201, SC-203) y sin `dict` ni `set`.

**Alternativas.** `set` o `dict` de exploradas (O(1) promedio, prohibido); una lista de ids explorados recorrida en
cada consulta (O(X)); atributos nuevos en `SalaViva` y `SalidaViva` (O(1), pero mezcla esqueleto y conocimiento y
modifica código P1 del integrante 1); un grafo propio con copia de las salas conocidas (duplica el esqueleto);
`bytearray` (O(1), fuera de los tipos acordados).

**Decisión.** `Logic/MapaConocido.py`, estado de la partida que vive en el motor (`motor.mapa`), con dos `list[int]`:
`estado[sala]` (largo S) y `caras[sala*4 + dirección]` (largo 4·S). Lo que se sabe de una explorada (nombre,
salidas, costo igualado) no se copia: se lee del esqueleto solo si está explorada. «Avistada» se mantiene al
explorar (cada destino desconocido de sus salidas pasa a avistado), sin contadores, porque entre dos pergaminos las
exploradas solo crecen. Ninguna operación baja un estado (FR-203).

**Complejidad.** `estado_sala` y `estado_cara`: O(1). Memoria: 5 casillas por sala, O(S).

**Evidencia** (B1 a B3, 100 / 1 024 / 10 000 salas, un tercio en cada estado):

| Medición | Resultado |
|---|---|
| B1 `estado_sala`, 100 000 consultas | 0,044 / 0,048 / 0,048 µs por consulta: 10 000 contra 100, 1,10 veces; **SC-203 se cumple** |
| B2 `estado_cara`, 100 000 consultas | 0,092 / 0,101 / 0,100 µs por consulta: 1,09 veces; **SC-203 se cumple** |
| B3 listas de ids recorridas (descartada) | 0,87 / 7,6 / 102,7 µs por consulta: 20, 158 y 2 138 veces B1 |

**¿Coincide con el plan?** Sí.

#### 2. Tres puntos de entrada y el repartidor del aviso de puertas (R2)

**Problema.** Explorar al entrar, con y sin antorcha (FR-202, FR-203, FR-210 a FR-216), volver a observar las
puertas de la sala del jugador cuando cambian (FR-207, FR-209), con costo proporcional a lo revelado (NFR-202,
SC-204), dentro del ciclo de 20 ms (NFR-205, SC-206) y sin que la precarga, el esqueleto o el cazador toquen el mapa
(FR-218).

**Alternativas.** Actualizar el mapa en Service después de cada movimiento (las reglas quedarían en Service y la
re-simulación de la 004 tendría que repetirlo); re-observar la sala del jugador al final de cada evento (O(1) por
evento, en todos, y toca el bucle de P1); recalcular «avistadas» recorriendo todo el mapa después de cada entrada
(O(S + X·g)); un segundo observador en la `Mazmorra`; que el mapa reenvíe el aviso a las rutas (cadena).

**Decisión.** Solo tres puntos escriben el mapa: `iniciar` (desde `Motor.iniciar`), `entrar(sala, antorcha)` (desde
`Motor.mover_jugador`, justo después de cambiar la sala; el booleano es `efectos.tiene(jugador, "antorcha")` en ese
instante, así que el mapa no conoce los efectos y H3-8 sale sin código especial) y `puerta_cambio` (el aviso de la
001, que re-observa todas las puertas de la sala del jugador, porque el aviso no identifica una puerta sin vuelta).
Más `restaurar` al cargar. Todo pasa por `_poner_estado` y `_poner_cara`. Para que el aviso llegue a las rutas del
cazador y al mapa sin modificar la `Mazmorra`, el motor asigna `RepartidorAvisosPuertas([rutas, mapa])` como
`observador_puertas` (hallazgo H-1; las líneas de `Logic/motorJuego.py` las escribió el integrante 2 y las revisó el
integrante 1). El cambio a `Logic/motorJuego.py` quedó en el commit `ed0da17` (revisado y aprobado por el integrante 1
el 15/11).

**Complejidad.** `iniciar` y `entrar` sin antorcha: O(g). Con antorcha: O(1 + Σ g de las vecinas que pasan a
exploradas), a lo sumo 5 salas y 20 salidas. `puerta_cambio`: O(g), g ≤ 4. El repartidor: O(observadores) por aviso.

**Evidencia** (B4, B5 y B8; la entrada al centro con la antorcha revela siempre 5 salas y 8 caras):

| Medición | Resultado |
|---|---|
| B4 entrada con antorcha, resto del mapa explorado | 13,1 / 13,3 / 13,5 µs: el mayor contra el menor, 1,03 veces; **SC-204 se cumple** |
| B5 entrada + recalcular «avistadas» (descartada) | 49 / 400 / 4 844 µs: crece con S |
| B8 ciclo con antorcha, 1 024 salas, 30 cazadores y 20 errantes y rastreadores, el jugador se mueve | peor ciclo 5,71 ms (mediana 0,43 ms): **NFR-205 y SC-206 se cumplen** |
| B8, además una puerta de la sala del jugador cambia en cada ciclo, avisada por `motor.mazmorra.observador_puertas` | peor ciclo 5,50 ms (mediana 0,47 ms): **se cumplen** |

Antes de cronometrar B8 se juegan 30 ciclos de cada variante comparando, casilla por casilla, el mapa del motor
medido (aviso por el repartidor) con el de un motor de control (aviso a las rutas y al mapa por separado), y en la
sala del jugador cada cara recordada con la real: son iguales.

**¿Coincide con el plan?** Sí.

#### 3. Pergamino: reversión por casilla en el historial (R3)

**Problema.** El pergamino debe dejar el mapa exactamente como antes de la acción, incluidas las salas de la
antorcha y las puertas observadas (FR-222), con registro e inversión proporcionales a lo que cambió (NFR-203,
SC-207).

**Alternativas.** Copiar el mapa entero al empezar cada acción y restaurarlo (O(S) por acción); una sola función de
reversión por entrada con la lista de casillas (misma complejidad, más difícil de explicar); inversas también para
la línea de tiempo (no hacen falta: la 004 reconstruye hacia adelante).

**Decisión.** `_poner_estado` y `_poner_cara` no hacen nada si el valor no cambia; si cambia, registran en el
`HistorialRetroceso` existente una función que devuelve **esa casilla** a su valor anterior (índice y valor ligados) y
después escriben. Como deshacer recorre el intervalo de atrás hacia adelante, una casilla que cambió dos veces en la
acción vuelve al primer valor. El conocimiento inicial se descarta con la preparación del motor y no se deshace.

**Complejidad.** Registrar: O(1) por casilla cambiada. Deshacer: O(casillas cambiadas en el intervalo); una entrada
con antorcha cambia a lo sumo 5 estados de exploración, 16 de avistamiento y 8 caras. No depende de S ni de X.

**Evidencia** (B6 y B7, las mismas 13 casillas en los tres tamaños):

| Medición | Resultado |
|---|---|
| B6 entrar con antorcha, cerrar el intervalo y deshacer | 15,9 / 25,8 / 15,7 µs (el mejor, 16 µs en los tres): el mayor contra el menor, 0,99 veces; **SC-207 se cumple** |
| B7 copiar el mapa entero y restaurarlo (descartada) | 10,7 / 24,9 / 159,9 µs: crece con S |

**¿Coincide con el plan?** Sí.

#### 4. Copia por punto de control y bloque propio en el binario versión 2 (R4)

**Problema.** Guardar y cargar el mapa idéntico (FR-221), que cada punto de control de la línea de tiempo lleve el
mapa de ese instante (FR-223) y que `--replay` dé el mismo mapa (FR-224), sin `copy` y con una copia proporcional al
tamaño del mapa una vez por punto (NFR-203).

**Alternativas.** Para el archivo: el mapa dentro del bloque global; solo las exploradas y las caras observadas
(lista de pares, O(X)); una copia por casilla dentro del bloque de cada sala; reconstruir el mapa al cargar
re-simulando. Para cargar un DTO sin mapa: lanzar `ValueError` (rompe unas 109 construcciones en 11 archivos de
prueba de otros integrantes sin proteger ningún archivo real) o un `if` en `PartidaGuardada.cargar`.

**Decisión.** `MapaConocidoGuardadoDTO(estado_salas, caras)` como campo `mapa` de `PartidaGuardadaDTO`, antes de
`linea`, que sigue siendo el último. `a_guardado` copia los dos arreglos con `list(...)` y `restaurar` los vuelve a
copiar (si no, la re-simulación de la 004 escribiría dentro del punto de control), comprueba los largos (si no
coinciden con la `Mazmorra`, `ValueError`) y **reemplaza** el mapa en curso sin registrar en el historial (H-8).
`restaurar(None)` arma el mapa inicial desde la sala del jugador, como FR-202, así `PartidaGuardada.cargar` suma una
sola línea, sin `if`. El cambio a `Logic/PartidaGuardada.py` quedó en el commit `4aac926`, junto con T041 a T044 (el
integrante 1 aceptó no rehacerlo como commit propio; aprobado el 15/11); el comentario se reordenó después en el
commit de los ajustes de su revisión. En el archivo, el mapa va en un **bloque propio**: 1 byte de estado y 1 byte con las 4 caras
(2 bits cada una) por sala; el mismo codificador sirve para el mapa de cada punto de control dentro del bloque de la
línea (T003 de la 004).

**Antes y después del formato binario** (cambia una decisión de la primera parte; el antes es el formato del archivo
de partida del Documento de Decisiones de la primera entrega y de P1 §4.10):

- *Antes*: versión 1; cabecera con magia `CRPT`, versión, offset y largo del bloque global, offset del índice,
  entradas e id mínimo; bloque global, bloques de sala e índice al final.
- *Después*: versión 2, definida una sola vez con los dos bloques nuevos (el del mapa de esta feature y el de la línea
  de T003 de la 004): la cabecera pasa a 58 bytes (`<4sHQIQIIQIQI>`) con offset y largo del mapa y de la línea; el
  bloque global, los bloques de sala y el índice no cambian, y `cargar_sala` sigue sin leer ni el mapa ni la línea.
  Un archivo de la versión 1 se rechaza con la versión leída y la esperada, sin cargar nada (FR-421 de la 004).

**Complejidad.** Copiar para guardar o para un punto de control: O(S) en tiempo y memoria (5 casillas por sala en
memoria, 2 bytes por sala en el archivo). Cargar: O(S).

**Evidencia** (B9, con el mapa completo):

| Medición | Resultado |
|---|---|
| B9 `a_guardado` + `restaurar` | 2,6 / 16,3 / 145,7 µs (26, 16 y 15 ns por sala): crece en forma lineal con S, una vez por punto de control |

**¿Coincide con el plan?** Sí. `restaurar(None)` en lugar de un error se decidió en el plan el 14/11 (riesgo R-9),
antes de implementar.

#### 5. Lo que el mapa le ofrece al integrante 3 (R5)

**Problema.** «Ir a» y la interfaz solo pueden usar lo que el jugador conoce (FR-217, FR-225), con el desempate de
la búsqueda de la 001 (FR-253).

**Alternativas.** Para el grafo: que el mapa avise a una búsqueda guardada entre pasos (nadie lo usaría: YAGNI); una
segunda búsqueda propia de «ir a» (la 001 ya decidió compartirla). Para la vista: mantener una lista de exploradas
para armar el DTO en O(X) (más estado que revertir y guardar). Para el nombre: un índice ordenado con búsqueda
binaria (O(log S), pero hay que mantenerlo con cada exploración y cada pergamino, y la búsqueda ocurre una vez por
orden).

**Decisión.** `GrafoMapaConocido(mapa)` con la interfaz exacta de la 001 (`cantidad_salas`, `salidas`, `entradas`):
una salida es utilizable si sus dos salas están exploradas y la cara de la sala de origen se recuerda abierta; costo
igualado; ids reales; lee el mapa en vivo. «Ir a» empieza una búsqueda nueva por paso. `MapaConocido.a_dto()` arma el
`MapaConocidoDTO` en Logic (solo exploradas, por id creciente; destino `None` para una avistada; nunca una
desconocida ni el contenido). `buscar_exploradas(nombre)` compara `strip().casefold()` solo contra exploradas
(H-3). `es_explorada(sala)` sirve al integrante 3 para el H-2.

**Complejidad.** `salidas(u)`: O(4); `entradas(x)`: O(grado de entrada), más O(S + E) la primera vez (índice inverso
del esqueleto); constructor O(1). `a_dto` y `buscar_exploradas`: O(S).

**Evidencia** (B10 y B11, con el mapa completo):

| Medición | Resultado |
|---|---|
| B10 `a_dto` | 0,28 / 3,04 / 39,7 ms (2,8, 3,0 y 4,0 µs por sala) |
| B10 `buscar_exploradas` | 11 / 194 / 1 247 µs (109, 190 y 125 ns por sala) |
| B11 armar el grafo (constructor + índice inverso) | 0,08 / 0,94 / 13,6 ms |
| B11 un `paso_desde_cero` de esquina a esquina con el grafo armado | 0,27 / 3,79 / 50,5 ms |
| B11 armar el grafo + un paso (búsqueda nueva por paso) | 0,56 / **4,52** / 65,0 ms: con 1 024 salas queda **por debajo de 5 ms** (NFR-250 del integrante 3) |

**¿Coincide con el plan?** Sí. El plan no afirmaba si «armar el grafo + un paso» entraba en 5 ms; ahora está medido,
y la frase de research R5 y del contrato (a) dice el número.

#### Decisiones tomadas por diseño, sin medición

- **El `RepartidorAvisosPuertas`**, frente a un solo observador o a que la `Mazmorra` avise a dos observadores: es una
  cuestión de responsabilidades y de no modificar la `Mazmorra` (código P1 del integrante 1), no de rendimiento. Las
  tres opciones cuestan O(1) por aviso; el repartidor deja a las rutas y al mapa con una sola responsabilidad cada
  uno, y el orden de la lista no cambia ningún resultado (el mapa no cambia puertas y las rutas no leen el mapa).
- **El bloque propio del mapa en el binario**, frente a meter el mapa en el bloque global: es formato y
  compatibilidad, con el mismo costo O(S). El bloque global lo reutiliza cada punto de control de la línea (que va con
  `linea = None`) y `cargar_sala` no debe leer conocimiento.

#### Límites conocidos y hallazgos

- **Dos salidas de una sala hacia la misma vecina** (H-4). El mapa empareja las caras con
  `Mazmorra._salida_inversa` (del integrante 1, solo lectura), que da solo la **primera** cara de vuelta. Con dos
  salidas de x hacia la misma vecina v, la segunda cara de v hacia x no queda emparejada y no se observa desde x. Es la
  misma regla que usan `abrir_puerta` y `CierrePuerta`, y queda fuera de las criptas publicadas, que no tienen salidas
  repetidas (H-1 de la 001).
- **Dependencia de `_salida_inversa`** (H-7), que es privada de la `Mazmorra`, como ya la usa `PartidaGuardada`. Si
  el integrante 1 cambia esa regla o su nombre, avisa antes (está en su lista de funciones privadas usadas por la 002
  y la 003); las pruebas H2-6 y A16 lo detectan.
- **`observador_puertas` del motor** (H-1): ahora es el repartidor, no `self.rutas`. `Logic/BenchRutas.py` lo reasigna
  en dos mediciones; en esas dos el mapa deja de escuchar, sin efecto en lo que miden. El data-model de la 001 dice
  `observador_puertas = self.rutas` y quedó desactualizado.
- **Lectura de H2-5** (H-5): si el jugador estuviera en A, la puerta A–C no podría estar «sin observar»; el escenario
  se reescribió en la spec (el jugador está en B y A y C se exploraron con la antorcha) y la prueba se arma así.
- **Cuadrícula de 1 024 salas** (H-6): SC-206 dice «1 000 salas»; B8 usa la cuadrícula de 32 × 32 del bench de la 001,
  para medir en la misma cripta.
- **Cargar reemplaza el mapa** (H-8): una partida guardada puede tener menos salas exploradas que el mapa vivo; no
  contradice FR-203 (es otra partida), y FR-221 lo dice desde la Sesión 2026-11-14.
- **Margen de B11**: con 1 024 salas, «armar el grafo + un paso» tarda 4,52 ms de mediana: cumple, pero con poco
  margen (casi 3,8 ms son la búsqueda, que recorre toda la cripta de esquina a esquina). Lo usa el integrante 3 para
  NFR-250.
- **Alcance de B8**: el jugador va y viene entre dos salas, así que después del primer ciclo la antorcha casi no
  revela salas nuevas; el costo de una entrada que sí revela está en B4 (13 µs) y es despreciable frente a los 20 ms.
- **`a_dto` con 10 000 salas** cuesta 4,0 µs por sala frente a 2,8 y 3,0 con mapas menores (crea 5 objetos por sala);
  sigue siendo O(S) y se llama una vez por consulta del mapa, no por paso.

Mediciones: `python main.py --bench` (`Logic/BenchMapaConocido.py`), tabla completa en
[bench-2026-11-15.txt](specs/002-niebla-ir-a/bench-2026-11-15.txt). Máquina: AMD Ryzen 5 5500, 32 GB, Windows 11 Pro,
Python 3.14.7. Semilla `SEMILLA = 2026`: los conteos son reproducibles; los tiempos son medianas y dependen de la
máquina.

### §5.4 Resolubilidad

(pendiente: 003)

---

## Integrante 3 — 004

Spec: [specs/004-linea-tiempo/spec.md](specs/004-linea-tiempo/spec.md) ·
Plan: [specs/004-linea-tiempo/plan.md](specs/004-linea-tiempo/plan.md) ·
Investigación: [specs/004-linea-tiempo/research.md](specs/004-linea-tiempo/research.md)

### §5.3 Banco de pruebas de la línea de tiempo (`--bench`)

`Service/BenchLineaTiempo.py` (con `Service/Cronometro.py` y `ResultadoBenchDTO`, igual que
`Service/BenchInventario.py`) corre sin ventana y con cargas **sintéticas** (Principio VI): una cripta en
cuadrícula de 4 × 4 salas, dos enemigos errantes inofensivos y un jugador que no puede morir, que juega una
secuencia fija (esperar y dar la vuelta a una manzana de salas) con la semilla 2026. Cada partida de 5 000 acciones se
juega una vez por K y la comparten M1, M2 y M3: como la partida es determinista, la historia de las primeras n
acciones es la de una partida de n. `BenchInventario.medir()` devuelve también este grupo (una línea), y así `--bench`
lo muestra sin tocar `Service/ServicioBench.py` (cambio registrado en el plan, NFR-401).

Tabla completa: [bench-tabla.txt](specs/004-linea-tiempo/bench-tabla.txt) (`python -m Service.ServicioBench`, 74 s,
Windows 11 Pro). Los tiempos son medianas y dependen de la máquina; los conteos son reproducibles.

### §5.5 Línea de tiempo y puntos de control

Cada decisión sigue [research.md](specs/004-linea-tiempo/research.md) R1 a R10. «¿Coincide con el plan?» compara
con el `plan.md` original.

**1. Hacia adelante o hacia atrás (R1, diseño A).**

- *Problema*: obtener el estado de un instante pasado sin que una consulta re-simule más de K acciones del jugador
  (FR-416, SC-404).
- *Alternativas*: hacia atrás (invertir cambios desde el estado vivo, como el pergamino); hacia adelante desde el
  punto de control anterior; sin puntos de control (re-simular desde el inicio).
- *Decisión*: **hacia adelante**. `ReconstructorEstado` ubica el punto más cercano anterior, arma con él un **Motor
  aparte** (`PartidaGuardada.cargar`, sin función de mensajes) y re-simula las acciones vigentes. Hacia atrás exigiría
  un segundo historial completo y guardable (el actual guarda funciones, tiene tope de 5 y el pergamino actúa fuera
  de él). La comparación con hacia atrás es teórica: no se implementó un segundo mecanismo solo para medirlo.
- *Complejidad*: O(log P) para ubicar + O(S + E + V + I) para armar el Motor + O(K · ciclo de eventos). Memoria
  O(A) acciones + O(A/K) copias.
- *Evidencia*: M1 y M2 (decisión 10). *Límites*: un cambio de reglas del motor que rompa el determinismo
  (Principio IV) rompe también la línea.
- *¿Coincide con el plan?* Sí.

**2. Reconstrucción sin efectos y `DespachoAcciones` propio (R2).** Reconstruir no escribe `partida.log`, no toca la
caché del catálogo ni gasta solicitudes (Principio VII). Se descartó cargar con `ServicioGuardado.cargar` y ejecutar con
`ServicioAccionJugador`. `Service/DespachoAcciones.py` traduce un `AccionDTO` a la llamada del Motor (mover, abrir,
atacar, esperar, recoger, soltar, equipar, usar; nunca `retroceder`) **sin Data**. Repite la correspondencia de
`ServicioAccionJugador` a propósito, para no modificar la primera entrega (Principio III), y una prueba compara los dos
caminos. *Límite*: si el Motor cambia la firma de un método, hay que actualizar el despacho; esa prueba lo detecta.
*¿Coincide con el plan?* Sí.

**3. Línea autocontenida: grabadores con registros de carga y ordinal (R3, hallazgo H-1).**

- `ContenidoGrabador` y `ResolvedorGrabador` envuelven `contexto.contenido` y `contexto.resolvedor` y guardan en la línea
  lo que **la partida viva ya pidió**: el `SalaDTO` de cada sala cargada (registro de carga) y cada ficha, una vez por
  id. Delegan todo lo demás (incluidos `rechazo()` y `resolver_contenido()`) y, si el original lanza `ErrorDatos`, no
  registran nada. No hacen solicitudes nuevas.
- Se descartó pedir al catálogo las fichas de todo lo que una sala pueda necesitar (gastaría solicitudes que la partida
  viva no gastaba) y guardar el catálogo completo.
- **Ordinal**: cada registro de carga guarda cuántas acciones vigentes llevaba la partida. Los registros se guardan en
  el orden real y no se recortan con el pergamino, porque cargar una sala no se deshace y el contador por tipo de
  `Mazmorra.cargar_contenido` numera los enemigos según el orden de carga («Rata #3»).
- *Tamaño*: ≤ una entrada por sala y una ficha por id usado; no depende de K ni de las acciones (4 cargas en las
  partidas medidas).
- *¿Coincide con el plan?* Sí en el diseño. **T032 (regla del prefijo por ordinal al reconstruir) no fue necesaria**: el
  punto nuevo en c (decisión 4) copia el estado vivo, ya con las salas cargadas y sus contadores. Se verificó con
  `FuenteConRatas` en T034 (dos salas nuevas con el mismo tipo de enemigo, una cargada dentro de una acción revertida).
  El ordinal queda registrado, pero el reconstructor solo toma de la línea las salas que el punto no trae.

**4. Pergamino sin marcador: punto de control nuevo en c (R4, FR-413, FR-424, NFR-403).**

- *Problema*: las acciones revertidas dejan de existir sin recorrer la historia, y el pergamino actúa fuera del
  historial (los pergaminos recogidos o soltados en la acción revertida persisten, hallazgo H-2).
- *Alternativas*: guardar `retroceder` y re-ejecutarla; marcar acciones como revertidas; **marcadores de pergamino**
  (`quitados`/`agregados`) comparando el inventario vivo con el reconstruido.
- *Decisión*: acciones vigentes + **un punto de control nuevo en c** tras el pergamino. `ServicioLineaTiempo.ejecutar`
  compara `jugador.acciones` antes y después: +1 acción nueva, −1 pergamino (llama a `LineaTiempo.retroceder_una` con
  `PartidaGuardada.guardar` del estado vivo ya revertido), sin cambio rechazada. `retroceder_una` quita la última
  acción, quita los puntos con c acciones o más y agrega el de c.
- *Por qué es más simple y exacta que los marcadores*: desaparecen el DTO, el bloque binario, el recorte y la regla de
  aplicación del marcador; y la copia describe **todo** el estado vivo (inventario, suelo, azar, cola), no solo lo
  que alguien previó comparar. Las consultas de instantes anteriores a c usan los puntos anteriores, que reflejan lo
  vivido en ese momento. Consecuencia: tras un pergamino los puntos pueden quedar más cerca que K, nunca más lejos.
- *Complejidad*: O(1 + r) más una copia O(S + E + V + I), sin depender de la historia.
- *Evidencia*: M6: 0,034 ms con 100 acciones de historia y 0,055 ms con 5 000.
- *¿Coincide con el plan?* Sí: es la versión del plan tras `plan(004): punto de control tras el pergamino`.

**5. Búsqueda binaria propia (R5).** Los puntos de control y las acciones nacen ordenados (todo se agrega al final y todo
recorte quita del final), así que `Estructuras/BusquedaBinaria.ultimo_menor_o_igual` (sin `bisect`) basta: O(log n),
sin ordenar. Se descartaron el recorrido lineal y un índice directo `k // K` (frágil con el pergamino y con otro K).
Evidencia (M4, 200 consultas por tanda): con 10 000 puntos, 0,285 ms contra 20,673 ms; con 1 000, 0,281 contra
1,782 ms; con 100 puntos casi empatan (0,199 contra 0,282 ms). *¿Coincide con el plan?* Sí.

**6. `Motor.avanzar_hasta(t)` y la regla de consulta de un instante (R6, FR-402).**

- Método nuevo en `Logic/motorJuego.py`, sin tocar `avanzar_hasta_jugador`: mira el siguiente evento válido, y si es
  posterior a t o es una decisión del jugador, se detiene **justo antes**; si la partida terminó, no ejecuta los demás
  eventos de ese instante. Una corrección posterior (`fix(004): avanzar_hasta usa el evento extraído y cierra el
  intervalo`) hizo que usara el evento ya extraído de la cola.
- **Regla de la consulta**: `j` es la última acción con tiempo **estrictamente menor** que t. Si en t hay una decisión
  del jugador, esa acción no se hace: `historia <t>` coincide con `historia #k`. Si el último punto con
  `acciones_completadas == j` ya tiene reloj igual a t, **ese punto es** el estado pedido y no se llama a
  `avanzar_hasta`; si no, se parte del último punto con `<= j − 1`, se re-simula hasta `j − 1`, se ejecuta la `j` y se
  llama a `avanzar_hasta(t)`. Excepción: si la partida terminó y t es el reloj del final, la acción de t sí se aplica.
- **El error que se corrigió** (commit `d3ddf90`, T021): la primera versión usaba el punto de control directamente
  cuando su reloj era **mayor o igual** que t. Con un instante a mitad de un intervalo, el punto siguiente ya incluía
  eventos posteriores a t y el resumen salía distinto según K. Lo detectó la prueba H5-1 (K = 1 daba otro resumen que
  K = 50). Ahora solo se usa directo si el reloj del punto es **igual** a t. Quedó la prueba de regresión
  `test_instante_entre_decisiones_no_usa_el_punto_posterior_fr402` (`tests/test_reconstructor_estado.py`): compara los
  resúmenes de todos los instantes pares de una partida con K = 1 y con K = 1000 (solo existe el punto 0).
- *¿Coincide con el plan?* No del todo: la regla de consulta se precisó en `spec(004): retraso de efectos y regla de
  consulta de un instante` y el error de arriba obligó a cambiar la condición de «mayor o igual» a «igual».

**7. Validación de t y k en Logic (FR-409).** `LineaTiempo.validar_instante` y `validar_accion` lanzan `ValueError` con
el motivo y el rango válido (t entre 0 y el reloj actual; k entre 1 y las acciones vigentes); es regla de negocio.
`ServicioLineaTiempo` solo la propaga y `ControladorBackend` la devuelve como `ErrorOperacion`. El Controlador valida
**solo la estructura** (`historia <t>` con entero ≥ 0; `historia #k` con entero ≥ 1). Una consulta no consume tiempo, no
cuenta como acción, no se anexa a `partida.log` y no toca el historial de retroceso (FR-407; R9: la feature no registra
nada nuevo ahí). *¿Coincide con el plan?* Sí.

**8. Interfaz: línea de comandos con Enter y Esc (FR-423, T056).** `Enter` abre la línea como un campo de texto durante la
partida; `Enter` acepta y ejecuta, y `Esc` la cierra **sin pausar**. Con la línea abierta las teclas del juego se
escriben y no actúan. El panel de `historia` es de solo lectura y no calcula nada: solo formatea el
`ResumenHistoriaDTO`; `Esc` lo cierra primero (el juego sigue tal cual estaba) y recién el siguiente `Esc` pausa. Una
acción nueva también cierra el panel, porque describe un estado pasado. La misma línea la usará «ir a» (spec 002).
*¿Coincide con el plan?* Sí.

**9. Contenido de la línea en el archivo y K al cargar (R7).** Decisión de diseño: campos nuevos al final de
`PartidaGuardadaDTO`, un bloque propio en el binario con `VERSION_FORMATO = 2`, y los archivos de la primera parte se
rechazan como incompatibles (no se migran). **Todavía no implementado**: depende de T002 y T003 (integrante 2) y de
T044 a T048; por eso M3 mide los bytes con el escritor de la versión 1 (ver «Memoria»).

**10. K por defecto: 20, confirmado (R8, T062).**

- *Problema*: elegir el K más grande (menos memoria) con el que `historia` tarde menos de 50 ms con 5 000 acciones (SC-405).
- *Alternativas medidas (M1)*: K = 1, 5, 20, 100 y **sin puntos de control** (solo el punto 0). Peor caso del bloque
  (la acción que obliga a re-simular K − 1 acciones), mediana:

| K | `historia #k` | `historia <t>` | Puntos | Bytes (5 000 acciones) |
|---|---|---|---|---|
| 1 | 0,090 ms | 0,079 ms | 5 001 | 16 600 279 |
| 5 | 0,186 ms | 0,186 ms | 1 001 | 3 380 623 |
| **20** | **0,620 ms** | **0,617 ms** | 251 | 901 877 |
| 100 | 3,587 ms | 2,978 ms | 51 | 240 877 |
| sin puntos | **147,382 ms** | **149,102 ms** | 1 | 75 627 |

- *Decisión*: **K = 20**, con 0,62 ms: unas 80 veces menos que el límite de 50 ms. Sin puntos de control, `historia`
  tarda 147 ms y **no cumple**: los puntos de control son necesarios. K = 100 también cumpliría (3 ms), pero K = 20 deja
  margen para estados más grandes, donde cada acción re-simulada y cada copia cuestan más (M5). La posición consultada
  importa poco con K = 20 (M2): inicio 0,068 ms, mitad 0,612 ms, final 0,590 ms; sin puntos crece con la posición
  (0,066, 73,5 y 147,4 ms).
- **¿Coincide con el plan?** Sí: coincide con el valor provisional (K = 20). No se cambió `CHECKPOINT_POR_DEFECTO`.
- *Límite*: la medición es con una partida sintética de 16 salas; con muchas salas cada copia cuesta más (M5).

**Costo de una copia (M5, riesgo R-1).** Un punto de control es una copia completa, O(S + E + V + I):

| Salas | 0 enemigos | 10 enemigos | 100 enemigos |
|---|---|---|---|
| 6 | 0,024 ms | 0,046 ms | 0,242 ms |
| 50 | 0,079 ms | 0,126 ms | 0,464 ms |
| 1 000 | 1,268 ms | 1,414 ms | 1,518 ms |
| 10 000 | 14,835 ms | 15,904 ms | 16,811 ms |

Crece con las salas y poco con los enemigos. Para las criptas publicadas (hasta 50 salas) una copia cuesta menos de
0,5 ms; solo con miles de salas llega a unos 15 ms, y se paga una vez cada K acciones. Si eso llegara a ser un
problema, la alternativa que el plan deja anotada (guardar solo las salas que cambiaron desde el punto anterior) no se
adelanta (YAGNI).

**Memoria (M3, NFR-402).** La memoria crece con el número de puntos, no con acciones × estado: con 5 000 acciones, K = 20
guarda 0,90 MB y K = 1 guarda 16,6 MB (unas 18 veces más). Las acciones pesan unos 14,5 bytes cada una (72 500 bytes en
5 000). *Límite*: el formato versión 2 con la línea no existe todavía (T003, integrante 2), así que los bytes son los que
escribe `GuardadoBinario` (versión 1) por cada punto (un archivo por punto, con su cabecera de unos 34 bytes) más las
acciones; las cargas y las fichas se cuentan, pero no se pesan.

**Supuesto: `--replay` sin `--hasta`.** Es headless (sin ventana ni línea de comandos) y no alimenta la línea de tiempo,
porque `ServicioReplay` ejecuta las acciones con `ServicioAccionJugador` directo. Por eso `historia` no es alcanzable en ese
modo y no se agregó código para él (YAGNI). Si se llamara a pesar de todo, el contexto del replay tiene una línea con solo
el punto 0 y respondería un estado del instante 0, que engaña; la defensa mínima, que **no** se aplicó por ser inalcanzable,
es `contexto.linea = None` en `ServicioReplay.reproducir`, para que salga el mensaje claro «Esta partida no tiene línea de
tiempo que consultar». Anotado como supuesto en la spec de la 004 (Suposiciones).

### §5.6 Revisión de decisiones de la primera parte

Las decisiones de la primera entrega que esta feature toca se volvieron a medir con la carga nueva (Principio VIII).

**Historial de retroceso (no cambia).** *Antes* (Documento de Decisiones de la primera entrega, §4.6): una función
inversa por cambio, con tope de 5 intervalos. *Después*: la 004 **no registra nada nuevo** en él (R9): consultar no
cambia el estado y la línea vive fuera de `Motor`; el Motor aparte tiene su propio historial, que se descarta con él.
El pergamino sigue funcionando igual; lo único nuevo es que, al leerlo, `ServicioLineaTiempo` toma una copia del estado
vivo (decisión 4), que cuesta entre 0,034 y 0,055 ms y no crece con la historia.

**Ciclo de eventos y agenda (no cambian).** `Motor.avanzar_hasta(t)` es un método nuevo que usa `cola.ver_siguiente()`
y no modifica `ColaEventos` ni `avanzar_hasta_jugador`. La re-simulación ejecuta el mismo ciclo de eventos que la
partida viva, y su costo ya está contenido en M1: con K = 20 re-simula 19 acciones en 0,62 ms, unos 30 µs por acción.
Las mediciones de la agenda y del ciclo de la primera entrega siguen siendo las de §5.6 del integrante 1; esta feature
no las modifica.

**Costo por acción con la línea activa (NFR-401).** `ServicioLineaTiempo.ejecutar` con K = 20 tarda **69,7 µs por acción**
(mediana de 200 acciones) y sin línea, 72,3 µs: la línea no agrega un costo medible, porque registrar una acción es un
`append` (O(1)) y la copia se paga una vez cada 20 acciones (unos 0,07 ms con 16 salas). El «antes» y el «después» son
iguales dentro del ruido de la medición; la decisión de la primera parte sigue siendo adecuada.

**Estructuras de la primera parte.** No se modificó ninguna (R0): `HistorialRetroceso`, `BufferCircular`, `Cola` y
`ListaDoble` no sirven como línea (tope fijo, funciones en lugar de datos, sin acceso por posición), y
`PartidaGuardada` se reutiliza tal cual.

**Pendiente de la sección.** Cuando exista el guardado con línea (T044 a T048), se agregará el tamaño real del archivo
versión 2 y se revisará si ese valor cambia la elección de K.

### Contador de daño recibido (`ActorBase.danio_recibido`, para «ir a» de la 002)

Cambio a la primera entrega (Principio III), propuesto por el integrante 3 y **pendiente de la revisión del integrante 1**.

**Problema.** «Ir a» debe detenerse cuando el jugador recibe daño (spec 002 FR-258 c, §3.4). Comparar `jugador.vida` antes y
después de un paso no basta: una Regeneración (`Logic/Efectos.py`, +vida por pulso) puede devolver la vida dentro del mismo
paso y ocultar el daño (R-I3-7).

**Alternativas.** (1) Comparar la vida y detenerse también si hay Regeneración activa, sin tocar Logic: no cambia la primera
entrega, pero detiene el viaje tras cada paso aunque no haya daño. (2) Contar los mensajes de daño del buffer: el buffer
guarda solo los últimos 20, no tiene contador total y el texto de la trampa no nombra a la víctima. (3) Un contador entero
en el único punto por el que pasa todo daño: **elegida**.

**Antes.**
```python
def Recibir_Dannio(self, Cant):
    if Cant <= 0:
        return
    self._registrar_vida()
    ...
```
**Después** (`Logic/ActorBase.py`: campo en `__init__` y una línea en `Recibir_Dannio`):
```python
self.danio_recibido: int = 0                 # en __init__

def Recibir_Dannio(self, Cant):
    """..."""
    if Cant <= 0:
        return
    self.danio_recibido += Cant              # la línea nueva
    self._registrar_vida()
    ...
```

**Por qué es seguro.** `Cant` ya es el daño final en los cuatro sitios que llaman a `Recibir_Dannio`: el ataque
(`Logic/motorJuego.py:256`, `max(1, ataque + azar - defensa_efectiva)`), la trampa (`:289`, `dano_al_activarse()`) y el veneno
(`Logic/Efectos.py:33`, su valor por pulso); la defensa se resta antes de llamar, no dentro. La guarda `Cant <= 0` sigue
primero, así que un daño de 0 no sube el contador. El contador **no** va al historial (deshacer con un pergamino no lo baja,
así que el pergamino no parece daño en la comparación de un paso) ni a `PartidaGuardada` (solo importa la diferencia dentro
de un paso; cargar una partida interrumpe el viaje). Los enemigos también lo tienen porque comparten `ActorBase`; nadie lo
lee. Costo: O(1). Pruebas: `tests/test_danio_recibido.py` (9).
