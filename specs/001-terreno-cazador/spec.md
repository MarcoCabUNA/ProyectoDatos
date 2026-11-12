# Especificación: Terreno con costo por salida y enemigo cazador

**Feature**: `001-terreno-cazador`

**Creada**: 2026-11-09

**Estado**: Borrador

**Fuente**: Cripta - Parte II §3.1, §3.2, §4.1, §5.1, §5.2, §6.1, §7 y Apéndice B «Terreno y cazador»; Primer Proyecto (P1) §2.3, §2.4, §2.6 y §2.8

**Constitución**: v1.2.0 · Requisitos con prefijo FR-1xx (Principio IX)

**Fuera de alcance**:

- La búsqueda de rutas del jugador («ir a») y la niebla de guerra son de la feature `002-niebla-ir-a`,
  que reutiliza la búsqueda de rutas de esta feature. Esta spec solo exige que el cazador ignore la
  niebla (FR-112).
- FR-118 depende de otras features para dos de sus modos: `--replay … --hasta` lo define la
  `004-linea-tiempo` y `--verificar` lo define la `003-resolubilidad`. Esta spec solo exige que, cuando
  esos modos existan, `--replay … --hasta` aplique las reglas de terreno y del cazador igual que una
  partida con vista, y que `--verificar` rechace los datos inválidos de FR-122 (su veredicto no depende
  de los costos ni de los cazadores: 003 FR-302).

**Entrada**: Descripción del usuario: "Feature 001-terreno-cazador. Terreno con costo por salida y un nuevo enemigo "cazador". Cada salida puede declarar un costo entero >= 1 (100 si no lo declara), igual en ambos sentidos. Moverse por una salida cuesta su costo para todos los actores, con intervalo = max(1, costo*100 // velocidad); atacar, esperar y demás acciones no cambian. Errantes y rastreadores conservan su comportamiento. El cazador tiene un "rango" en unidades de costo. En su turno: si comparte sala con el jugador, ataca; si no, calcula el costo mínimo d hasta la sala del jugador usando solo salidas abiertas en ese instante; si no hay ruta o d > rango, espera (costo 100); si hay, avanza un paso cuyo costo es el de la salida. Desempate: entre las vecinas v con costo(u,v) + dist(v,jugador) = d, va a la de menor id. Conoce el esqueleto completo y el estado actual de las puertas, no lo afecta la niebla, no abre puertas. Su decisión debe ser idéntica a calcularla desde cero en ese instante, aunque se reutilicen cálculos. Incluir como escenarios de aceptación los 7 casos del Apéndice B "Terreno y cazador", con una tabla de trazabilidad. Requisitos FR-101 en adelante. No nombrar estructuras de datos, clases ni módulos."

> Este archivo contiene reglas del juego, historias, escenarios y requisitos. No nombra estructuras
> de datos, clases ni módulos: eso va en `plan.md` (Principio IX). Se confirma con un commit antes
> de cualquier código de esta feature.

## Convenciones de los ejemplos

- Las salas se identifican por su id numérico (por ejemplo, «sala 4»).
- «Salida 1–2 (costo 250)» es una salida entre la sala 1 y la sala 2 cuyo costo es 250 en ambos sentidos.
- «t» es el reloj virtual. «Velocidad» es la del actor en ese instante.
- Salvo que se diga otra cosa, todas las salidas mencionadas están abiertas y el `rango` del cazador es 600.
- *(Decisión del grupo)* marca una regla que el enunciado no fija y que el grupo decidió. Se puede cambiar
  con una nueva clarificación, sin contradecir el enunciado.

## Clarificaciones

### Sesión 2026-11-09

- P: Si una sala tiene dos salidas abiertas hacia la misma vecina con costos distintos, ¿qué hacen el cazador y el errante? → R: El cazador usa la salida abierta más barata hacia esa vecina. El errante sortea entre las salidas abiertas como en P1 §2.8, donde cada salida es una opción, y paga el costo de la salida que le toca.
- P: ¿Los demás enemigos, incluidos otros cazadores, bloquean el paso del cazador o cuentan al calcular su ruta? → R: No. Varios actores pueden compartir sala, como en P1, y la ruta depende solo del esqueleto, los costos y el estado de las puertas.
- P: Un cazador que se mueve y llega a la sala del jugador, ¿ataca en ese mismo turno o en el siguiente? → R: En el siguiente. Moverse es su acción del turno (P1 §2.8), y ataca en su próximo turno si el jugador sigue en la sala.
- P: Si la ficha de un cazador no trae `rango` o no es un entero ≥ 0, o una salida declara un costo menor que 1 o no entero, ¿qué debe pasar? → R: Es un error de datos sin valor por defecto. Se informa con contexto, la partida no inicia con esos datos y el programa no se cae (ampliada en la sesión 2026-11-11).
- P: Cuando el costo mínimo d es exactamente igual al `rango`, ¿el cazador se mueve o espera? → R: Se mueve. Solo espera si d > `rango` (lectura literal del §3.2).
- P: ¿La decisión del cazador usa el generador aleatorio de la partida? → R: La decisión de moverse o esperar (búsqueda de ruta y desempate) no lo usa: es determinista por completo gracias al desempate por menor id. Cuando el cazador ataca, el daño se calcula con la fórmula de combate de P1 §2.6, que sí usa el generador, igual que para cualquier enemigo (FR-115, Principio IV).
- P: Si una sala tiene dos salidas abiertas hacia la misma vecina con costos distintos, ¿por cuál se mueve el rastreador? → R: *(Decisión del grupo)* Igual que el cazador, por la más barata, y paga su costo. El errante sigue sorteando entre salidas como en P1 (FR-104).
- P: Si solo uno de los dos lados de una salida declara costo, o los dos declaran costos distintos, ¿cuánto cuesta atravesarla? → R: *(Decisión del grupo)* Si solo un lado lo declara, ese costo vale en ambos sentidos. Si ninguno lo declara, vale 100. Si los dos declaran valores distintos, es un error de datos (FR-101, FR-122).
- P: ¿Con qué cripta y cuántos cazadores se miden el ciclo de eventos y el crecimiento del tiempo de decisión? → R: *(Decisión del grupo)* Con una cripta sintética de 1 000 salas en cuadrícula y 30 cazadores activos. Al multiplicar por 10 el tamaño de la cripta, la decisión de un cazador con `rango` pequeño no tarda más del doble (NFR-101, SC-104, SC-105).
- P: ¿Qué valor es un `rango` pequeño en NFR-102 y SC-105? → R: *(Decisión del grupo)* `rango` = 200, el costo de dos salidas de costo por defecto (NFR-102, SC-105).

### Sesión 2026-11-11

- P (pregunta de Dereck, integrante 2, simplificada por el grupo para no cambiar el formato de `partida.log` ni el replay de la primera parte, Principio III): La ficha de un cazador puede llegar con la precarga, antes o durante la partida. Si su `rango` falta o es inválido, ¿qué pasa? → R: La ficha se rechaza con un error de datos que indica la ficha y el campo, y no se vuelve a pedir. Si la ficha inválida es de un cazador de la sala inicial, la partida no inicia. Para cualquier otra sala, llegue antes o durante la partida, la sala que contiene a ese cazador queda como contenido no disponible: si el jugador intenta entrar, el movimiento se rechaza con ese mensaje, sin consumir tiempo ni registrarse en `partida.log`, y la partida sigue. Los costos inválidos o distintos entre las dos caras se detectan con el esqueleto e impiden iniciar (FR-122, escenarios H2-9, H2-17 a H2-19).

---

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — El terreno cuesta distinto (Prioridad: P1)

Como jugador, quiero que atravesar una salida tarde según su costo, para que elegir el camino tenga
consecuencias para mí y para los enemigos.

**Por qué esta prioridad**: el cazador y la búsqueda de rutas dependen de que moverse tenga un costo
variable. Sin esta regla, la historia 2 no tiene sentido.

**Prueba independiente**: con una cripta de dos salidas de costos distintos, mover al jugador por cada
una y comparar el instante de su siguiente acción. Aporta valor aunque no exista ningún cazador.

**Escenarios de aceptación**:

1. **Dado** un actor de velocidad 100 en t = 0 y la salida 1–2 (costo 250), **cuando** la atraviesa,
   **entonces** su siguiente acción queda programada en t = 250.
2. **Dada** una salida que no declara costo, **cuando** un actor de velocidad 100 la atraviesa en t = 0,
   **entonces** su siguiente acción queda programada en t = 100, igual que en la primera parte.
3. **Dada** la salida 1–2 (costo 250), **cuando** un actor la atraviesa de 2 a 1, **entonces** cuesta 250,
   lo mismo que de 1 a 2.
4. *(Apéndice B, caso 6)* **Dado** un actor de velocidad 300 en t = 0 y una salida de costo 1,
   **cuando** la atraviesa, **entonces** el intervalo es max(1, 1 × 100 // 300) = 1 y su siguiente acción
   queda en t = 1 (nunca en t = 0).
5. *(Apéndice B, caso 7)* **Dado** un actor de velocidad 100 que en t = 0 atraviesa una salida de
   costo 400 (siguiente acción en t = 400), **cuando** en t = 100 su velocidad cambia a 200,
   **entonces** el tiempo restante se escala según P1 §2.3: max(1, (400 − 100) × 100 // 200) = 150, y su
   siguiente acción pasa a t = 250.
6. **Dado** un actor de velocidad 100 junto a un enemigo, **cuando** ataca, espera o usa un objeto,
   **entonces** esas acciones cuestan lo mismo que en la primera parte (100, 100 y 50), sin importar
   los costos de las salidas de la sala.
7. **Dado** un errante en una sala cuya única salida abierta es de costo 300, **cuando** decide moverse
   por ella, **entonces** elige la salida con la misma regla de la primera parte y su siguiente acción
   se programa con costo 300.
8. **Dada** la salida 1–2 donde solo el lado de la sala 1 declara costo 250, **cuando** un actor de
   velocidad 100 la atraviesa de 2 a 1 en t = 0, **entonces** cuesta 250 y su siguiente acción queda en
   t = 250.
9. **Dado** un actor de velocidad 100 en una sala cuyas salidas cuestan 400 y 300, **cuando** equipa,
   recoge, suelta un objeto o abre una puerta con llave, **entonces** esas acciones cuestan lo mismo que en
   la primera parte (50, 25, 25 y 50), sin importar los costos de las salidas de la sala.
10. *(Decisión del grupo)* **Dado** un rastreador en la sala 1 con dos salidas hacia la sala 2, de costos
    300 y 120, y el rastro más fresco en la sala 2, **cuando** decide moverse, **entonces** elige la sala 2
    con la misma regla de la primera parte, atraviesa la salida de costo 120 y su siguiente acción se
    programa con costo 120.
11. **Dado** un guardián en una sala con una salida de costo 250 y el jugador en otra sala, **cuando** le
    toca actuar, **entonces** no se mueve, como en la primera parte, y su siguiente acción se programa con
    costo 100.

---

### Historia 2 — El cazador persigue por la ruta más barata (Prioridad: P1)

Como jugador, quiero enfrentar un enemigo que me busca por el camino más barato dentro de su alcance,
para que moverme por el mapa tenga riesgo y planificar la ruta valga la pena.

**Por qué esta prioridad**: es la regla nueva central de la capacidad.

**Prueba independiente**: con una cripta pequeña, un cazador y rutas de costos distintos, verificar en
cada turno del cazador qué acción toma, a qué sala va y cuánto cuesta esa acción.

**Escenarios de aceptación**:

1. *(Apéndice B, caso 1)* **Dado** un cazador en la sala 1, el jugador en la sala 4 y todas las rutas
   de 1 a 4 pasan por al menos una puerta cerrada, **cuando** le toca actuar, **entonces** espera con
   costo 100 y no cambia de sala.
2. *(Apéndice B, caso 2)* **Dado** un cazador de `rango` 600 en la sala 1, el jugador en la sala 3 y la
   única ruta abierta es 1–2 (costo 400) y 2–3 (costo 300), con d = 700, **cuando** le toca actuar,
   **entonces** espera con costo 100 porque d > `rango`.
3. *(Apéndice B, caso 3)* **Dado** un cazador en la sala 1, el jugador en la sala 4 y dos rutas: 1–4
   directa (costo 500) y 1–2, 2–3, 3–4 (costo 100 cada una, total 300), **cuando** le toca actuar,
   **entonces** se mueve a la sala 2, aunque esa ruta tenga más salas, y su acción cuesta 100.
4. *(Apéndice B, caso 4)* **Dado** un cazador en la sala 1, el jugador en la sala 5 y dos rutas de costo
   mínimo 200: 1–7, 7–5 y 1–4, 4–5 (costo 100 cada salida), donde la salida hacia la sala 7 aparece
   antes en la descripción de la sala, **cuando** le toca actuar, **entonces** se mueve a la sala 4,
   la vecina de menor id.
5. **Dado** un cazador en la misma sala que el jugador, **cuando** le toca actuar, **entonces** ataca
   según P1 §2.8 (costo 100) y no se mueve, aunque exista una ruta.
6. **Dado** un cazador de `rango` 600, en la sala 1, con el jugador en la sala 3 y la ruta 1–2
   (costo 250), 2–3 (costo 350), con d = 600, **cuando** le toca actuar, **entonces** se mueve a la sala 2
   (d no es mayor que `rango`) y su acción cuesta 250.
7. **Dado** un cazador de velocidad 120 que atraviesa una salida de costo 250, **cuando** termina el
   movimiento, **entonces** su siguiente acción queda a max(1, 250 × 100 // 120) = 208 unidades.
8. **Dado** un cazador cuya única ruta hacia el jugador cruza una sala cuyo contenido aún no se ha
   descargado y que el jugador nunca ha visto, **cuando** le toca actuar, **entonces** decide igual que si
   el contenido estuviera descargado y la sala explorada.
9. **Dada** una partida ya iniciada en la que llegó con la precarga la ficha de un cazador sin `rango`,
   **cuando** el jugador intenta entrar a la sala de ese cazador, **entonces** el movimiento se rechaza
   con un error de datos que indica esa ficha y el campo `rango`, no consume tiempo, no se registra en
   `partida.log` y la partida sigue, sin que el programa se caiga.
10. **Dado** un cazador en la sala 1, el jugador en la sala 3, dos salidas de la sala 1 hacia la sala 2
    de costos 300 y 120, y la salida 2–3 (costo 100), **cuando** le toca actuar, **entonces** calcula
    d = 220, se mueve a la sala 2 por la salida de costo 120 y su acción cuesta 120.
11. **Dado** un cazador en la sala 1, el jugador en la sala 3, la ruta 1–2, 2–3 y un guardián y otro
    cazador en la sala 2, **cuando** le toca actuar, **entonces** se mueve a la sala 2: los otros actores
    no le bloquean el paso.
12. **Dado** un cazador en la sala 1 y el jugador en la sala 2 vecina, **cuando** le toca actuar,
    **entonces** se mueve a la sala 2 y no ataca en ese turno. En su siguiente turno, si el jugador sigue en
    la sala 2, ataca.
13. **Dado** un cazador dormido en la sala 3 y el jugador en la sala 1, **cuando** pasan varios turnos sin
    que el jugador entre a la sala 3, **entonces** el cazador no actúa ni tiene acción programada. **Cuando**
    el jugador entra a la sala 3, **entonces** el cazador se activa y su primera acción queda a 100 unidades
    del instante de entrada, como cualquier enemigo (P1 §2.4).
14. **Dado** un cazador que se mueve o espera, **cuando** decide, **entonces** el generador aleatorio de la
    partida queda en el mismo estado que antes. **Dado** un cazador en la sala del jugador, **cuando** ataca,
    **entonces** el daño se calcula con la fórmula de combate de P1 §2.6, que consume el generador igual
    que el ataque de cualquier enemigo: con la misma semilla, el daño es el mismo que el de un errante con
    los mismos atributos.
15. **Dado** un cazador en la sala 1 y el jugador en la sala 2, separados solo por una puerta cerrada con
    llave, **cuando** el jugador abre la puerta con la llave y luego le toca actuar al cazador, **entonces**
    la puerta cuenta como abierta y el cazador se mueve a la sala 2. Antes de que el jugador la abra, el
    cazador espera.
16. **Dado** un cazador en la sala 1, el jugador en la sala 3, la única ruta 1–2, 2–3 y un cierre automático
    de la puerta 1–2 en el mismo instante que el turno del cazador, **cuando** llega ese instante,
    **entonces** los dos eventos se atienden en el orden en que se programaron (FR-108): si el cierre se
    programó antes, el cazador ve la puerta cerrada y espera; si se programó después, el cazador decide con
    la puerta abierta, se mueve a la sala 2 y la puerta se cierra a continuación.
17. **Dado** un esqueleto con una salida que declara un costo menor que 1 o no entero (por ejemplo 0,
    `"250"` o `true`), **cuando** se intenta iniciar la partida, **entonces** no inicia y el error indica la
    sala, la dirección y el campo `costo`, sin que el programa se caiga.
18. *(Decisión del grupo)* **Dada** la salida 1–2 cuyo lado de la sala 1 declara costo 100 y cuyo lado de
    la sala 2 declara 250, **cuando** se intenta iniciar la partida, **entonces** no inicia y el error indica
    esa salida y el campo `costo`, sin que el programa se caiga.
19. **Dada** la ficha de un cazador de la sala inicial sin `rango` o con `rango` -1, **cuando** se intenta
    iniciar la partida, **entonces** no inicia y el error indica esa ficha y el campo `rango`, sin que el
    programa se caiga.

---

### Historia 3 — La decisión del cazador sigue siendo correcta cuando el mapa cambia (Prioridad: P2)

Como jugador, quiero que el cazador reaccione a las puertas que se abren o se cierran y a mis movimientos,
para que sus decisiones sean siempre coherentes con el estado actual de la cripta.

**Por qué esta prioridad**: el enunciado permite reutilizar cálculos entre turnos, pero solo si el
resultado coincide con un cálculo desde cero. Es lo que hace confiables las historias 1 y 2 a lo largo
de una partida completa.

**Prueba independiente**: en una partida con cambios de puertas y movimientos del jugador, comparar en
cada turno del cazador su decisión con la de un cálculo desde cero en ese mismo instante.

**Escenarios de aceptación**:

1. *(Apéndice B, caso 5)* **Dado** un cazador en la sala 1, el jugador en la sala 4 y las rutas 1–2,
   2–4 (costo 100 cada una) y 1–3, 3–4 (costo 150 cada una), **cuando** el cazador se mueve a la sala 2,
   luego la puerta 2–4 se cierra y le toca actuar de nuevo, **entonces** decide como si calculara desde
   cero: la ruta más barata pasa a ser 2–1, 1–3, 3–4 (d = 400 ≤ 600) y se mueve a la sala 1 con costo 100.
2. **Dado** que el jugador se mueve de sala entre dos turnos del cazador, **cuando** el cazador actúa,
   **entonces** su decisión corresponde a la sala actual del jugador y no a la anterior.
3. **Dado** un cazador que esperaba porque d > `rango`, **cuando** se abre una puerta que crea una ruta de
   costo ≤ `rango` y le toca actuar, **entonces** se mueve por la nueva ruta.
4. **Dada** una puerta con cierre automático que se cierra lejos de la ruta del cazador, **cuando** le toca
   actuar, **entonces** su decisión es la misma que la de un cálculo desde cero (que en este caso no cambia).
5. **Dado** que otro actor muere o cambia de sala, o que cambia la velocidad de algún actor, entre dos
   turnos del cazador, **cuando** el cazador actúa, **entonces** su decisión es la misma que la de un
   cálculo desde cero en ese instante.
6. **Dada** la misma cripta, la misma semilla y la misma secuencia de acciones del jugador, **cuando**
   se juega dos veces (o se reproduce con `--replay`), **entonces** todos los cazadores toman las mismas
   decisiones en los mismos instantes.
7. **Dada** una cripta con costos de salida válidos y un cazador, **cuando** se ejecuta `--verificar`
   sobre ella (feature `003-resolubilidad`), **entonces** el esqueleto con costos se carga sin error y el
   veredicto y el orden de llaves no dependen de los costos ni de los cazadores (003 FR-302), sin
   instanciar la vista. **Dado** un esqueleto con un error de datos de FR-122 (costo inválido o distinto
   entre caras), **cuando** se ejecuta `--verificar`, **entonces** la verificación no concluye y el
   programa termina con código de salida 1 (003 FR-314), sin caerse (FR-118, FR-122).
8. **Dada** una cripta sintética con costos de salida y cazadores, **cuando** se ejecuta `--bench`,
   **entonces** los cazadores deciden con las mismas reglas que en una partida (cada decisión coincide con
   un cálculo desde cero) y la medición corre sin vista (FR-118).

---

### Historia 4 — Ver el terreno y reconocer al cazador (Prioridad: P3)

Como jugador, quiero ver cuánto cuesta cada salida de la sala en la que estoy y distinguir a los
cazadores de los demás enemigos, para decidir por dónde moverme.

**Por qué esta prioridad**: es necesaria para jugar, pero las reglas de las historias 1 a 3 se pueden
probar sin ella.

**Prueba independiente**: entrar a una sala con salidas de costos distintos y un cazador, y comprobar lo
que muestra la interfaz.

**Escenarios de aceptación**:

1. **Dada** una sala con salidas de costo 100, 250, una sin costo declarado y una cerrada de costo 300,
   **cuando** el jugador está en ella, **entonces** la interfaz muestra 100, 250, 100 y 300 junto a cada
   salida, también junto a la cerrada.
2. **Dada** una sala con un cazador y un errante, **cuando** el jugador está en ella, **entonces** la
   interfaz muestra el texto «cazador» junto al nombre del cazador y «errante» junto al del errante, y
   solo el cazador lleva su marcador visual propio.

---

### Casos borde

- **d igual a `rango`**: el cazador se mueve. Solo espera cuando d > `rango` (FR-110, escenario H2-6).
- **`rango` 0**: el cazador solo ataca si comparte sala con el jugador. En los demás casos espera, porque
  toda ruta cuesta al menos 1.
- **Varias salidas de una sala hacia la misma vecina, con costos distintos**: el cazador (FR-119) y el
  rastreador (FR-104) usan la más barata. El errante sortea entre salidas y paga la que le toca (FR-104).
- **El jugador solo es alcanzable por puertas cerradas**: no hay ruta y el cazador espera (escenario H2-1).
  Para el cazador, una puerta cerrada no existe aunque tenga la llave a la vista: no abre puertas.
- **Muchas rutas de igual costo**: el desempate por menor id de la vecina siempre define un único paso,
  sin importar cuántas rutas empaten ni el orden en que se describen las salidas.
- **Decenas de cazadores persiguiendo al mismo jugador**: cada uno decide según su propia sala y su
  `rango`. El resultado es el mismo que si cada uno calculara desde cero.
- **Cazador dormido**: se activa como cualquier enemigo cuando el jugador entra a su sala (P1 §2.4). Hasta
  entonces no actúa.
- **Otros actores en el camino**: no bloquean al cazador (FR-120).
- **Un cazador entra a la sala del jugador**: moverse consume su turno. Ataca en su siguiente turno si el
  jugador sigue en la sala (FR-121).
- **Costo de salida mayor que 100 y velocidad baja**: el intervalo crece en proporción (por ejemplo, costo
  250 con velocidad 50 da 500).
- **Solo un lado de la salida declara costo**: ese costo vale en ambos sentidos (FR-101, escenario H1-8).
- **Datos inválidos**: una salida con costo menor que 1 o no entero, o una salida cuyos dos lados
  declaran costos distintos, se detecta con el esqueleto e impide iniciar la partida. Una ficha de cazador
  sin `rango` entero ≥ 0 impide iniciar si el cazador está en la sala inicial. En cualquier otra sala,
  llegue antes o durante la partida, la ficha no se vuelve a pedir y su sala queda como contenido no
  disponible: cada intento de entrar se rechaza con el error de datos, sin consumir tiempo, y la partida
  sigue. En todos los casos se informa con contexto y el programa no se cae (FR-122, escenarios H2-9 y
  H2-17 a H2-19).

---

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Terreno**

- **FR-101**: Cada salida PUEDE declarar un costo entero ≥ 1, en uno o en los dos lados. El costo DEBE
  ser el mismo en ambos sentidos: *(decisión del grupo)* si solo un lado lo declara, ese costo DEBE valer
  para los dos; si ninguno lo declara, DEBE ser 100. Si los dos lados declaran costos distintos, aplica FR-122.
- **FR-102**: Moverse a través de una salida DEBE ser una acción cuyo costo base es el costo de esa
  salida, para todos los actores (jugador y enemigos). El intervalo hasta la siguiente acción DEBE ser
  max(1, costo_salida × 100 // velocidad).
- **FR-103**: Atacar, esperar, usar, equipar, recoger, soltar y abrir una puerta con llave DEBEN conservar
  los costos de la primera parte.
- **FR-104**: Errantes, rastreadores y guardianes DEBEN conservar su forma de decidir de la primera parte.
  Solo cambia lo que tarda su movimiento, según FR-102. Cuando dos o más salidas abiertas llevan a la
  misma vecina: el errante sortea entre las salidas abiertas como en la primera parte, donde cada salida
  es una opción, y paga el costo de la salida que le toca; *(decisión del grupo)* el rastreador, igual que
  el cazador (FR-119), se mueve por la más barata de esas salidas y paga su costo.
- **FR-105**: Si la velocidad de un actor cambia mientras tiene programada una acción, incluso tras
  atravesar una salida costosa, el tiempo restante DEBE escalarse con la regla de P1 §2.3:
  restante_nuevo = max(1, (tiempo_siguiente − t) × velocidad_anterior // velocidad_nueva).

**Cazador**

- **FR-106**: El juego DEBE admitir un cuarto comportamiento de enemigo, «cazador», cuya ficha de catálogo
  incluye el campo `rango`, un entero en unidades de costo. El costo de cada salida llega en el esqueleto
  de la cripta, y `comportamiento` y `rango` llegan en el catálogo (Apéndice A). Su validez de versión sigue
  las reglas de la primera parte.
- **FR-107**: En su turno, si el cazador comparte sala con el jugador, DEBE atacar según P1 §2.8 y no
  moverse.
- **FR-108**: Si no comparte sala, el cazador DEBE considerar el costo mínimo d desde su sala hasta la sala
  actual del jugador. d es la suma de los costos de las salidas recorridas, contando solo las salidas
  abiertas en ese instante. «Abierta en ese instante» incluye las puertas que el jugador ya abrió con llave
  y excluye las que un cierre automático cerró en ese instante o antes, según el orden de eventos de
  P1 §2.3. Si el cierre automático de una puerta y el turno del cazador caen en el mismo instante, se
  atienden en el orden en que se programaron, como cualquier par de eventos con el mismo tiempo: si el
  cierre se programó antes, el cazador ya ve la puerta cerrada; si se programó después, el cazador decide
  con la puerta abierta (y puede atravesarla) y la puerta se cierra a continuación (escenario H2-16).
- **FR-109**: Si no existe ruta, o si d > `rango`, el cazador DEBE esperar con costo 100.
- **FR-110**: Si existe ruta y d ≤ `rango` (incluido d = `rango`), el cazador DEBE moverse un paso por una
  ruta de costo d. El costo de esa acción DEBE ser el costo de la salida que atraviesa, y el intervalo
  se calcula según FR-102.
- **FR-111**: Sea u la sala del cazador. Entre las vecinas v que cumplen costo(u, v) + dist(v, jugador) = d,
  el cazador DEBE moverse a la de menor id. Este resultado DEBE cumplirse siempre, aunque muchas rutas
  tengan el mismo costo e independientemente del orden en que se describen las salidas.
- **FR-112**: El cazador DEBE decidir con el esqueleto completo de la cripta (incluido el costo de cada
  salida) y el estado actual de todas las puertas. Su decisión NO DEBE depender de la niebla de guerra
  del jugador ni de si el contenido de una sala ya se descargó.
- **FR-113**: El cazador NO DEBE abrir puertas cerradas. Una salida cerrada no forma parte de ninguna ruta
  del cazador mientras siga cerrada.
- **FR-114**: La decisión del cazador en cada turno DEBE ser idéntica a la que daría un cálculo de la ruta
  desde cero en ese instante, aunque se reutilicen cálculos anteriores. En particular, DEBE reflejar las
  puertas que se abrieron o cerraron, el movimiento del jugador, los cambios de sala o la muerte de otros
  actores y los cambios de velocidad ocurridos desde su turno anterior. También DEBE reflejar lo que deshace
  un pergamino de retroceso, que puede devolver a los actores a salas anteriores y volver a cerrar o a
  abrir puertas.
- **FR-115**: La decisión del cazador de moverse o esperar (cálculo de d, elección del paso y desempate)
  DEBE ser determinista y NO DEBE consumir el generador aleatorio de la partida. Cuando el cazador ataca,
  el daño DEBE calcularse con la fórmula de combate de P1 §2.6, que sí consume el generador, igual que
  para cualquier enemigo. Misma cripta, misma semilla y mismas acciones DEBEN producir las mismas
  decisiones y los mismos ataques del cazador.

**Interfaz**

- **FR-116**: La interfaz DEBE mostrar el costo junto a cada salida de la sala actual del jugador, también
  junto a las salidas cerradas (escenario H4-1).
- **FR-117**: La interfaz DEBE mostrar, junto al nombre de cada enemigo, su comportamiento en texto
  («errante», «guardián», «rastreador» o «cazador»). Además, el cazador DEBE llevar un marcador visual
  propio que no tiene ningún otro enemigo (escenario H4-2).
- **FR-118**: Las reglas de FR-101 a FR-115 y de FR-119 a FR-123 DEBEN funcionar igual en los modos sin
  vista `--replay`, `--replay … --hasta` y `--bench`. En `--verificar`, que solo usa el esqueleto, los
  costos y los cazadores NO DEBEN afectar el veredicto (003 FR-302), y los datos inválidos de FR-122
  DEBEN hacer que la verificación no concluya, con código de salida 1 (003 FR-314; escenario H3-7).
  `--replay … --hasta` y `--verificar` los definen las features 004 y 003 (ver «Fuera de alcance»).

**Cazador: casos borde y datos**

- **FR-119**: Si varias salidas abiertas unen la sala u con la misma vecina v, costo(u, v) DEBE ser el
  menor de sus costos, tanto para calcular d como para el desempate. Al moverse a v, el cazador DEBE
  atravesar una salida de ese costo mínimo.
- **FR-120**: Los demás actores, incluidos otros cazadores, NO DEBEN bloquear el paso del cazador. Su
  posición no afecta d ni el paso escogido. Varios actores pueden compartir sala, como en la primera parte.
- **FR-121**: El cazador DEBE ejecutar una sola acción por turno. Si se mueve y llega a la sala del jugador,
  NO DEBE atacar en ese mismo turno. Ataca en su siguiente turno si el jugador sigue en esa sala (FR-107).
- **FR-122**: Una ficha de cazador sin `rango`, o con un `rango` que no sea un entero ≥ 0, una salida
  que declare un costo menor que 1 o no entero, y una salida cuyos dos lados declaren costos distintos,
  DEBEN tratarse como datos inválidos, sin valor por defecto. El programa DEBE informar el error con
  contexto (qué ficha o qué salida y qué campo) y NO DEBE caerse. Además:
  - Los costos inválidos o distintos entre las dos caras DEBEN detectarse con el esqueleto, antes de
    iniciar, y la partida NO DEBE iniciar.
  - Una ficha de cazador con `rango` ausente o inválido puede llegar con la precarga. DEBE rechazarse
    con un error de datos que indique la ficha y el campo, y NO DEBE volver a pedirse. Si es de un
    cazador de la sala inicial, la partida NO DEBE iniciar. Para cualquier otra sala, llegue antes o
    durante la partida, la sala que contiene a ese cazador DEBE quedar como contenido no disponible y
    la partida DEBE iniciar o seguir con normalidad; el cazador no se activa (FR-123). Si el jugador
    intenta entrar a esa sala, el movimiento DEBE rechazarse con ese mensaje, sin consumir tiempo ni
    registrarse en `partida.log` (escenarios H2-9 y H2-19).
  - *(Decisión del grupo)* Que los dos lados de una salida declaren costos distintos es un error y no se
    elige uno de los dos (escenario H2-18).
- **FR-123**: El cazador DEBE activarse y programar su primera acción igual que los demás enemigos
  (P1 §2.4). Mientras está dormido no actúa.

### Requisitos de rendimiento

- **NFR-101**: El ciclo de eventos entre dos decisiones del jugador DEBE tardar menos de 20 ms en una cripta
  sintética de 1 000 salas en cuadrícula con 30 cazadores activos *(decisión del grupo: tamaño y cantidad)*,
  medido en el equipo local sin red ni renderizado (§6.1).
- **NFR-102**: El trabajo de decidir el paso de un cazador con `rango` pequeño (*(decisión del grupo)*
  `rango` = 200, el costo de dos salidas de costo por defecto) DEBE crecer con la región de la cripta que queda dentro de su `rango`,
  y no con el tamaño total de la cripta (§5.1).
- **NFR-103**: Las afirmaciones de rendimiento de esta feature DEBEN respaldarse con mediciones de `--bench`:
  un cazador frente a muchos, `rango` pequeño frente a grande, y un escenario con puertas que cambian con
  frecuencia frente a otro donde casi no cambian (§5.1, §5.2, §6.3).

### Entidades clave

- **Salida**: conecta dos salas en una dirección de la sala de origen. Tiene costo (igual en ambos
  sentidos; lo declara uno de los lados, los dos con el mismo valor, o ninguno y vale 100), estado abierta o cerrada, llave opcional y cierre automático opcional.
- **Esqueleto de la cripta**: todas las salas y salidas con sus costos. Se conoce completo al iniciar la
  cripta, antes de que se descargue el contenido de las salas.
- **Cazador**: enemigo con comportamiento «cazador» y `rango`. Además tiene los atributos de cualquier
  enemigo (vida, ataque, defensa, velocidad, botín).
- **Ruta**: secuencia de salidas abiertas entre dos salas. Su costo es la suma de los costos de sus salidas.
- **Distancia d**: costo mínimo entre todas las rutas que van de la sala del cazador a la sala del
  jugador en un instante dado.

---

## Trazabilidad del Apéndice B «Terreno y cazador» (Principio X)

| # | Caso del Apéndice B | Escenario | Requisitos | Prueba |
|---|---|---|---|---|
| 1 | Un cazador no tiene ruta abierta hacia el jugador: espera con costo 100 | H2-1 | FR-108, FR-109, FR-113 | Se define en `tasks.md` |
| 2 | La ruta más barata del cazador cuesta más que su `rango`: espera con costo 100 | H2-2 | FR-108, FR-109 | Se define en `tasks.md` |
| 3 | Ruta de menos salas y mayor costo frente a otra de más salas y menor costo: sigue la de menor costo | H2-3 | FR-108, FR-110 | Se define en `tasks.md` |
| 4 | Dos vecinas inician rutas de costo mínimo: va a la de menor id | H2-4 | FR-111 | Se define en `tasks.md` |
| 5 | Una puerta de la ruta se cierra entre dos turnos: decide como si calculara desde cero | H3-1 | FR-113, FR-114 | Se define en `tasks.md` |
| 6 | Un actor de velocidad alta atraviesa una salida de costo 1: el intervalo es al menos 1 | H1-4 | FR-102 | Se define en `tasks.md` |
| 7 | Cambia la velocidad de un actor que atraviesa una salida costosa: el restante se escala según P1 §2.3 | H1-5 | FR-102, FR-105 | Se define en `tasks.md` |

Cada prueba citará el identificador del requisito que verifica (Principio X).

### Trazabilidad de los escenarios agregados en la revisión cruzada

| Escenario | Requisitos | Prueba |
|---|---|---|
| H1-9 | FR-103 | `test_h1_9_fr103_equipar_recoger_soltar_abrir_conservan_costo` |
| H1-10 | FR-104 | `test_fr104_rastreador_usa_la_salida_mas_barata` |
| H1-11 | FR-104 | `test_fr104_guardian_no_se_mueve` |
| H2-10 | FR-119 | `test_fr119_dos_salidas_misma_vecina_paga_la_mas_barata` |
| H2-11 | FR-120 | `test_fr120_otros_actores_no_bloquean` |
| H2-12 | FR-121 | `test_fr121_entra_a_la_sala_y_no_ataca_en_ese_turno` |
| H2-13 | FR-123 | `test_fr123_dormido_no_actua_hasta_activarse` |
| H2-14 | FR-115 | `test_fr115_decidir_no_consume_el_generador`, `test_h2_14_fr115_ataque_usa_la_formula_de_p1` |
| H2-15 | FR-108 | `test_h2_15_fr108_puerta_abierta_con_llave_cuenta_como_abierta` |
| H2-16 | FR-108 | `test_fr108_cierre_automatico_en_el_mismo_instante` |
| H2-17 | FR-122 | `test_h2_17_fr122_costo_invalido_no_inicia` |
| H2-18 | FR-101, FR-122 | `test_h2_18_fr122_costos_distintos_entre_caras_no_inicia` |
| H2-19 | FR-122 | `test_h2_19_fr122_ficha_invalida_en_la_sala_inicial_no_inicia` |
| H3-7 | FR-118, FR-122 | `test_h3_7_fr118_fr122_verificar_no_depende_de_costos_ni_cazadores` |
| H3-8 | FR-118 | `test_h3_8_fr118_bench_aplica_las_mismas_reglas` |
| H4-1 | FR-116 | `test_h4_1_fr116_el_costo_llega_a_la_vista` (datos); lo que se dibuja, en T041 |
| H4-2 | FR-117 | `test_h4_2_fr117_actor_dto_trae_el_comportamiento` (datos); lo que se dibuja, en T041 |

---

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-101**: Los 7 casos del Apéndice B «Terreno y cazador» pasan como pruebas automatizadas, y cada una
  cita su requisito.
- **SC-102**: En el 100 % de los turnos de cazador de las pruebas y de las partidas reproducidas, la decisión
  coincide con la de un cálculo desde cero en ese instante.
- **SC-103**: Misma cripta, misma semilla y mismas acciones producen la misma partida, con o sin
  cazadores. Las decisiones de moverse o esperar de los cazadores no consumen el generador aleatorio:
  en una partida donde ningún cazador ataca, agregar cazadores no cambia lo que eligen los errantes.
- **SC-104**: `--bench` muestra que el ciclo de eventos entre dos decisiones del jugador tarda menos de
  20 ms en una cripta sintética de 1 000 salas en cuadrícula con 30 cazadores activos *(decisión del
  grupo: tamaño y cantidad)*.
- **SC-105**: *(Decisión del grupo)* En `--bench`, al multiplicar por 10 el tamaño de la cripta, la decisión de un cazador con
  `rango` pequeño (`rango` = 200, el costo de dos salidas de costo por defecto) no tarda más del doble.
- **SC-106**: En todas las salas con salidas, el jugador puede ver el costo de cada salida y distinguir
  a un cazador de los demás enemigos sin salir de la pantalla de la sala.

---
