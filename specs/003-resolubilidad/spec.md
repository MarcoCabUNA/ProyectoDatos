# Especificación: Verificación de resolubilidad

**Feature**: `003-resolubilidad`

**Creada**: 2026-11-11

**Estado**: Borrador

**Fuente**: Cripta - Parte II §3.5, §4.2, §4.3, §5.4, §6.1, §6.3, §7.3, Apéndice A y Apéndice B «Resolubilidad»; Primer Proyecto (P1) §2.12 (victoria) y §5.1 (presupuesto de red)

**Constitución**: v1.2.0 · Requisitos con prefijo FR-3xx, NFR-3xx y SC-3xx (Principio IX)

**Fuera de alcance**: cómo se dibuja el reporte en la interfaz gráfica (integrante 3); el costo de las
salidas y el cazador (`001-terreno-cazador`); el mapa conocido y «ir a» (`002-niebla-ir-a`); la línea de
tiempo (`004-linea-tiempo`). Esta spec solo exige que el reporte exista, qué contiene y cuándo se muestra.

**Entrada**: Descripción del usuario: "Verificación de resolubilidad de Cripta II. Antes de iniciar una
partida, el programa determina si la cripta puede ganarse usando el esqueleto y la ubicación de las llaves,
bajo los supuestos de §3.5. Si es resoluble, entrega un orden determinista de obtención de llaves; si no,
un reporte con las llaves no obtenibles, la frontera bloqueada, la ubicación de esas llaves y el ciclo
concreto si existe. La partida no inicia si no es resoluble, salvo con --forzar. --verificar <cripta>
ejecuta solo la verificación, sin vista, y funciona con --offline. Requisitos FR-301 en adelante. No
nombrar estructuras de datos, clases, módulos ni algoritmos."

> Este archivo contiene reglas del juego, historias, escenarios y requisitos. No nombra estructuras
> de datos, clases, módulos ni algoritmos: eso va en `plan.md` (Principio IX). Se confirma con un commit
> antes de cualquier código de esta feature.

## Convenciones de los ejemplos

- Las salas se identifican por su id numérico (por ejemplo, «sala 4»). Salvo que se diga otra cosa, la
  sala inicial es la 1 y `sala_salida` es la 9.
- «Puerta 4–5 (B)» es una salida cerrada entre la sala 4 y la sala 5 que requiere la llave B.
  «Salida 1–2» sin paréntesis es una salida abierta.
- «Puerta de salida» es una puerta cerrada que da a `sala_salida` y requiere `llave_salida`. Salvo que se
  diga otra cosa, es la puerta 8–9 (`llave_salida`).
- A, B, C… abrevian ids de llaves del catálogo (por ejemplo, `itm_llave_bronce`). `llave_salida` es la
  llave que indica la cripta.
- «Ubicación de una llave» es lo que entrega la consulta de llaves: su id, su sala y, opcionalmente, la
  instancia de enemigo que la suelta (§4.2).
- «Región alcanzable» es el conjunto de salas a las que el jugador puede llegar desde la sala inicial bajo
  los supuestos de la verificación (FR-302), con todas las llaves que puede obtener.

## Clarificaciones

### Sesión 2026-11-11

- P: ¿El orden de obtención de llaves incluye todas las llaves obtenibles de la cripta, o solo las necesarias
  para obtener `llave_salida` y cruzar la puerta de salida? → R: Todas las llaves obtenibles de la cripta,
  no solo las necesarias para ganar (FR-305).
- P: Si una ubicación de llave nombra una sala o una instancia de enemigo que no existen, o si una puerta
  requiere una llave que no aparece en la lista de ubicaciones, ¿es un error de datos o la llave es no
  obtenible? → R: Depende del caso. Una llave que requiere alguna puerta (incluida `llave_salida`) y no
  aparece en la lista de ubicaciones es no obtenible y aparece en el reporte con la indicación «sin
  ubicación»; no es un error de datos, porque el servicio publica criptas no resolubles (§4.3). Una
  ubicación cuya sala no existe en el esqueleto es un error de datos: se informa con contexto (qué llave y
  qué sala), la verificación no concluye y tiene el mismo efecto que FR-320, sin que el programa se caiga.
  La instancia de enemigo de una ubicación no se valida, porque comprobarla exigiría descargar el
  contenido de salas (FR-301); se usa la sala que trae la ubicación (FR-321).
- P: Si ninguna puerta hacia `sala_salida` requiere `llave_salida` (por ejemplo, una cripta sin puertas
  cerradas), ¿la cripta es resoluble? → R: No. En la primera parte (P1 §2.12) la victoria exige entrar a
  `sala_salida` después de abrir con la llave correspondiente la puerta que da acceso a ella, así que esa
  cripta no se puede ganar. El reporte indica ese motivo de forma explícita (FR-322).
- P: Si la lista de ubicaciones trae la misma llave más de una vez, con salas distintas, ¿cómo se trata?
  → R: Cada ubicación es una copia válida de la llave. La llave es obtenible si alguna de sus salas es
  alcanzable, y el reporte muestra todas sus ubicaciones en un orden determinista (FR-316).
- P: ¿`--verificar` devuelve un código de salida distinto según el resultado? → R: Sí: 0 si la cripta es
  resoluble, 3 si no es resoluble y 1 si la verificación no concluyó (error de datos, de red o de
  presupuesto). El código 2 sigue reservado para los argumentos inválidos, como en la primera parte, así
  que `--verificar` no lo usa para ningún veredicto (FR-314).
- P: ¿La verificación se ejecuta también al cargar una partida guardada o con `--replay`? → R: No. Solo
  al iniciar una partida nueva; cargar una partida y `--replay` no verifican ni bloquean (FR-301).

### Sesión 2026-11-12

Las dos preguntas de esta sesión surgen de la revisión cruzada del integrante 1.

- P: Si las dos caras de una misma puerta declaran llaves distintas (una requiere la llave A y la otra la
  llave B), ¿qué hace la verificación? → R: No es un error de datos. Igual que en la primera parte, cada
  cara se rige por lo que declara (su llave, su estado cerrado y su cierre automático): para atravesar la
  puerta desde una sala hace falta la llave que declara la cara de esa sala. Una cara cerrada sin llave
  sigue sin poder atravesarse en ese sentido. Motivo: en la primera parte, una cara que declara su propia
  llave no se iguala con la otra, así que el juego ya permite esa puerta, y el enunciado no dice que sea
  inválida. Los costos distintos entre caras sí son un error de datos (001 FR-122) porque §3.1 dice que el
  costo es el mismo en ambos sentidos; para las llaves no existe esa regla. Como en la primera parte,
  «cerrada» ausente, null o false significan lo mismo: la cara no declara cierre (FR-302, FR-308,
  escenario H2-9).
- P: ¿Qué hace la verificación con un esqueleto que tiene un error de datos de 001 FR-122 (una salida con
  un costo no entero o menor que 1, o con costos distintos en sus dos caras)? → R: La verificación no
  concluye: `--verificar` termina con el código de salida 1, muestra el error con contexto y no se cae. La
  partida no inicia, ni siquiera con `--forzar`, porque 001 FR-122 exige que con esos datos la partida no
  inicie y el juego supone datos válidos; a diferencia de FR-320, donde `--forzar` sí permite jugar. El
  costo sigue sin afectar el veredicto (FR-302). Concuerda con el escenario H3-7 de la feature 001
  (FR-323, escenarios H3-8 y H4-5).

---

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia 1 — Saber antes de jugar si la cripta es resoluble y en qué orden obtener las llaves (Prioridad: P1)

Como jugador, quiero saber antes de empezar si la cripta puede ganarse y en qué orden conviene obtener las
llaves, para no invertir una partida en una cripta imposible.

**Por qué esta prioridad**: es la regla central de la capacidad. Las demás historias reutilizan su
resultado.

**Prueba independiente**: con criptas pequeñas construidas a mano (esqueleto y ubicación de llaves),
ejecutar la verificación y comparar el veredicto y el orden con el esperado. Aporta valor aunque no exista
el reporte de no resolubilidad.

**Escenarios de aceptación**:

1. **Dada** una cripta sin puertas cerradas en su interior, cuya única puerta cerrada es la puerta de
   salida, y `llave_salida` ubicada en la sala 3, alcanzable desde la sala 1 por salidas abiertas,
   **cuando** se verifica, **entonces** la cripta es resoluble y el orden es [`llave_salida`]
   (FR-301, FR-304, FR-305).
2. **Dada** una cripta sin ninguna puerta cerrada, ni siquiera hacia `sala_salida`, con `sala_salida`
   alcanzable por salidas abiertas y `llave_salida` en la sala 3, **cuando** se verifica, **entonces** la
   cripta no es resoluble y el reporte indica de forma explícita el motivo: ninguna puerta hacia
   `sala_salida` requiere `llave_salida`, por lo que la victoria de P1 §2.12 es imposible. `llave_salida` no
   aparece entre las llaves no obtenibles y la frontera bloqueada está vacía (FR-304, FR-322).
3. **Dada** la llave A en la sala 2 (alcanzable por salidas abiertas), la puerta 1–3 (A), la llave B en la
   sala 3, la puerta 3–4 (B) y `llave_salida` en la sala 4, **cuando** se verifica, **entonces** la cripta
   es resoluble y en el orden A aparece antes que B, y B antes que `llave_salida` (FR-304, FR-305).
4. *(Apéndice B, caso 2)* **Dada** una ubicación `{ "id": B, "sala": 12, "enemigo": "e-1203" }`, donde
   e-1203 es un enemigo errante que inicia en la sala 12 y lleva B en su campo `suelta`, **cuando** se
   verifica, **entonces** B se considera obtenible en la sala 12, sin importar hacia dónde pueda moverse el
   errante durante la partida, y si B aparece en el orden o en el reporte, su ubicación indica la sala 12 y
   el enemigo e-1203 (FR-303, FR-316).
5. *(Apéndice B, caso 3)* **Dadas** las llaves A en la sala 2 y B en la sala 3, ambas alcanzables desde la
   sala 1 sin llaves, y la puerta 5–6 (A), la puerta 6–7 (B) con `llave_salida` en la sala 7, de modo que
   tanto [A, B, `llave_salida`] como [B, A, `llave_salida`] son órdenes válidos, **cuando** se verifica dos
   veces (en dos ejecuciones distintas del programa), **entonces** las dos producen exactamente el mismo
   orden (FR-305, FR-306).
6. **Dada** una cripta resoluble cuya ruta hacia `llave_salida` cruza una sala con un enemigo activo, una
   sala con trampa y la puerta 2–3 (A) con cierre automático, **cuando** se verifica, **entonces** es
   resoluble: el enemigo, la trampa y el cierre automático no bloquean, y el costo de las salidas no cambia
   el veredicto ni el orden (FR-302).
7. **Dada** la llave A en la sala 2 y dos puertas, 1–3 (A) y 4–5 (A), en el camino hacia `llave_salida`,
   **cuando** se verifica, **entonces** A abre las dos puertas: las llaves no se consumen (FR-302).
8. **Dada** una cripta resoluble con salas cuyo contenido aún no se ha descargado, **cuando** se verifica
   antes de iniciar una partida con semilla S, **entonces** la verificación no descarga contenido de salas
   ni consume el generador aleatorio, y la partida que sigue es idéntica a la que produce `--replay` del
   mismo `partida.log`, que no ejecuta la verificación (FR-301).
9. **Dada** una cripta resoluble, **cuando** el jugador inicia una partida normal, **entonces** la partida
   inicia y el resultado de la verificación (resoluble y el orden de llaves) queda disponible para
   mostrarse al iniciar (FR-313).
10. **Dada** la puerta 1–3 donde solo la cara de la sala 1 declara que está cerrada y que requiere la llave
    A, mientras la cara de la sala 3 no declara ni cierre ni llave, con A en la sala 2 y `llave_salida` en
    la sala 3, a la que solo se llega por la puerta 1–3, **cuando** se verifica, **entonces** la puerta 1–3
    se trata como cerrada y con llave A desde sus dos salas: la sala 3 solo es alcanzable después de
    obtener A, y en el orden A aparece antes que `llave_salida` (FR-302, FR-305).
11. **Dada** la llave A con dos ubicaciones, la sala 4 (alcanzable desde la sala 1 sin llaves) y la sala 12
    (detrás de la puerta 11–12 (B), con B no obtenible), y la puerta 5–6 (A) en el camino hacia
    `llave_salida`, **cuando** se verifica, **entonces** A es obtenible gracias a su copia en la sala 4 y
    aparece en el orden antes que `llave_salida`; ninguna de sus dos ubicaciones se trata como error de
    datos (FR-316, FR-305).
12. **Dada** la llave C con dos ubicaciones, la sala 10 y la sala 13, ambas fuera de la región alcanzable,
    en una cripta no resoluble, **cuando** se verifica varias veces, **entonces** el reporte lista C entre
    las llaves no obtenibles con sus dos ubicaciones, siempre en el mismo orden (FR-316, FR-309, FR-306).

---

### Historia 2 — Entender por qué una cripta no es resoluble (Prioridad: P1)

Como jugador, quiero que, si la cripta no puede ganarse, el programa me diga qué llaves no puedo conseguir,
qué puertas me bloquean, dónde están esas llaves y si hay un ciclo, para entender el problema sin revisar
los datos a mano.

**Por qué esta prioridad**: el enunciado exige el reporte y el servicio publicará criptas no resolubles
(§4.3). Sin el reporte, la historia 4 no tiene nada que mostrar.

**Prueba independiente**: con criptas no resolubles construidas a mano, ejecutar la verificación y
comparar cada parte del reporte (llaves no obtenibles, frontera, ubicaciones, ciclo) con la esperada.

**Escenarios de aceptación**:

1. *(Apéndice B, caso 1)* **Dada** `llave_salida` ubicada en la sala 5, cuya única puerta de acceso es la
   puerta 4–5 (`llave_salida`), con la sala 4 alcanzable desde la sala 1, **cuando** se verifica,
   **entonces** la cripta no es resoluble y el reporte indica: llaves no obtenibles: `llave_salida`;
   frontera bloqueada: puerta 4–5, que requiere `llave_salida`; `llave_salida` está en la sala 5; ciclo:
   `llave_salida` está en la sala 5 → la puerta 4–5 requiere `llave_salida` (FR-304, FR-307, FR-308,
   FR-309, FR-310).
2. **Dadas** la llave A en la sala 6, cuya única puerta de acceso es la puerta 2–6 (B), la llave B en la
   sala 7, cuya única puerta de acceso es la puerta 3–7 (A), con las salas 2 y 3 alcanzables desde la sala 1
   y `llave_salida` detrás de la puerta 5–8 (A), **cuando** se verifica, **entonces** la cripta no es
   resoluble y el reporte señala el ciclo de dos llaves: A está en la sala 6 → la puerta 2–6 requiere B →
   B está en la sala 7 → la puerta 3–7 requiere A (FR-307, FR-310).
3. **Dada** la cripta del escenario 2, **cuando** se verifica varias veces, **entonces** el reporte es
   idéntico en cada ejecución, incluido el ciclo señalado, la llave por la que empieza y el orden en que se
   listan llaves y puertas (FR-306, FR-310).
4. **Dada** la llave C en la sala 10, detrás de la puerta 4–10 (A), donde A forma parte del ciclo del
   escenario 2, **cuando** se verifica, **entonces** C aparece entre las llaves no obtenibles con su
   ubicación, pero no se presenta como parte de un ciclo propio: se lista junto con el ciclo A–B del que
   depende (FR-307, FR-309, FR-310).
5. **Dada** una región alcanzable rodeada por las puertas 2–6 (B), 3–7 (A) y 4–10 (A), donde la llave D es
   obtenible en la sala 2, **cuando** se verifica, **entonces** la frontera bloqueada lista las tres
   puertas, cada una una sola vez y con la llave que requiere, y D no aparece entre las llaves no
   obtenibles (FR-307, FR-308).
6. **Dada** la puerta 4–5 (C), con la sala 4 alcanzable y `llave_salida` en la sala 5, donde C no aparece
   en la lista de ubicaciones, **cuando** se verifica, **entonces** la verificación concluye: la cripta no
   es resoluble, C aparece entre las llaves no obtenibles con la indicación «sin ubicación», la puerta 4–5
   aparece en la frontera bloqueada con la llave C, y no se informa ningún error de datos (FR-307, FR-309,
   FR-321).
7. **Dada** una ubicación `{ "id": A, "sala": 99 }` donde la sala 99 no existe en el esqueleto, **cuando** se
   verifica, **entonces** se informa un error de datos con contexto (la llave A y la sala 99), la
   verificación no concluye, la partida no inicia salvo con `--forzar` y el programa no se cae (FR-321,
   FR-320).
8. **Dada** una ubicación `{ "id": B, "sala": 12, "enemigo": "e-9999" }` cuya sala 12 existe, pero cuya
   instancia e-9999 no está en el contenido de esa sala, **cuando** se verifica, **entonces** la instancia
   no se valida, no se descarga el contenido de ninguna sala y B se considera obtenible en la sala 12
   (FR-321, FR-301, FR-303).
9. **Dada** la puerta 2–6, cuya cara de la sala 2 está cerrada y requiere la llave A y cuya cara de la
   sala 6 está cerrada y requiere la llave B, con la sala 2 alcanzable, A obtenible, B no obtenible y la
   sala 6 sin otro acceso, **cuando** se verifica, **entonces** la sala 6 es alcanzable entrando por la
   cara de la sala 2 con A, la verificación concluye y no se informa ningún error de datos. **Si en
   cambio** A no es obtenible, la sala 6 queda fuera de la región alcanzable y la puerta 2–6 aparece en la
   frontera bloqueada con la llave A, la de la cara de la sala alcanzable (FR-302, FR-308).

---

### Historia 3 — Verificar una cripta sin jugar (Prioridad: P2)

Como integrante del grupo o revisor, quiero ejecutar `--verificar <cripta>` para obtener solo el reporte,
sin abrir la ventana ni iniciar una partida, también sin red con `--offline`.

**Por qué esta prioridad**: es la forma de revisar criptas nuevas y de automatizar las pruebas de esta
feature (Principio V), pero las historias 1 y 2 aportan valor sin ella.

**Prueba independiente**: ejecutar `--verificar` sobre criptas resolubles y no resolubles, en línea y con
`--offline`, y comprobar la salida, que no se instancia la vista y las solicitudes consumidas.

**Escenarios de aceptación**:

1. **Dada** una cripta resoluble, **cuando** se ejecuta `--verificar <cripta>`, **entonces** se muestra que
   es resoluble y el orden de obtención de llaves, no se instancia la vista, no se inicia ninguna partida
   y el código de salida es 0 (FR-314, FR-315).
2. **Dada** una cripta no resoluble, **cuando** se ejecuta `--verificar <cripta>`, **entonces** se muestra
   el reporte completo de FR-307 a FR-310, idéntico al que se mostraría al intentar iniciar una partida con
   esa cripta, no se instancia la vista y el código de salida es 3 (FR-314, FR-315).
3. **Dada** una cripta disponible en el paquete local, **cuando** se ejecuta `--verificar <cripta>
   --offline`, **entonces** la ubicación de las llaves se lee del paquete local, no se hace ninguna
   solicitud de red y el resultado es el mismo que en línea con la misma versión de la cripta (FR-314,
   FR-318, FR-306).
4. **Dada** una cripta cuya ubicación de llaves no está persistida, **cuando** se verifica en línea,
   **entonces** se hace una solicitud de ubicación de llaves, cuenta dentro de `presupuesto_solicitudes` y
   la respuesta queda persistida con el resto de los datos de la cripta (FR-317).
5. **Dada** la ubicación de llaves persistida con la misma versión de la cripta, **cuando** se verifica de
   nuevo, **entonces** no se repite la solicitud de ubicación de llaves (FR-317).
6. **Dados** datos de la cripta persistidos por la primera parte con una versión anterior, **cuando** se
   verifica la cripta de la segunda parte, **entonces** la validación de versión existente los invalida y
   se vuelven a obtener, sin que nadie borre archivos a mano (FR-319).
7. **Dado** `presupuesto_solicitudes` agotado, un HTTP 429 o un error de red al pedir la ubicación de
   llaves, o un paquete local sin ubicación de llaves en `--offline`, **cuando** se verifica, **entonces**
   se muestra un mensaje con contexto que indica que la verificación no pudo concluir, el programa no se
   cae y, con `--verificar`, el código de salida es 1 (FR-320, FR-314).
8. **Dado** un esqueleto con una salida que declara costo 0, **cuando** se ejecuta `--verificar <cripta>`,
   **entonces** se muestra el error de datos con contexto (qué salida y qué campo), la verificación no
   concluye, no se muestra ningún veredicto (ni resoluble ni no resoluble), el programa no se cae y el
   código de salida es 1. Concuerda con el escenario H3-7 de la feature 001 (FR-323, FR-314; 001 FR-122).

---

### Historia 4 — Jugar de todas formas con `--forzar` (Prioridad: P3)

Como jugador, quiero poder iniciar una partida aunque la cripta no sea resoluble, usando `--forzar`, para
explorarla de todos modos sabiendo que no se puede ganar.

**Por qué esta prioridad**: es una excepción a la regla de la historia 1; sin ella el programa sigue siendo
correcto.

**Prueba independiente**: intentar iniciar una partida con una cripta no resoluble, con y sin `--forzar`, y
comprobar si la partida inicia y si se muestra el reporte.

**Escenarios de aceptación**:

1. *(Apéndice B, caso 4)* **Dada** una cripta no resoluble, **cuando** el jugador intenta iniciar una
   partida sin `--forzar`, **entonces** la partida no inicia, no se consume tiempo virtual ni se crea
   estado de partida, y se muestra el reporte de no resolubilidad (FR-311).
2. **Dada** una cripta no resoluble, **cuando** el jugador inicia una partida con `--forzar`,
   **entonces** la partida inicia normalmente y el reporte de no resolubilidad se muestra igual, como
   advertencia (FR-312, FR-313).
3. **Dada** una cripta resoluble, **cuando** el jugador inicia una partida con `--forzar`, **entonces** el
   resultado es el mismo que sin `--forzar` (FR-312).
4. **Dada** una partida iniciada con `--forzar` sobre una cripta no resoluble, guardada y registrada en
   `partida.log`, **cuando** el jugador la carga sin `--forzar` o la reproduce con `--replay`, **entonces**
   no se ejecuta la verificación, no se muestra el reporte y la partida se carga o se reproduce
   normalmente (FR-301).
5. **Dada** una cripta cuya salida 3–4 declara costo 150 en la cara de la sala 3 y costo 200 en la cara de
   la sala 4, **cuando** el jugador intenta iniciar una partida con `--forzar`, **entonces** se muestra el
   error de datos con contexto (qué salida y qué campo), la partida no inicia, no se consume tiempo virtual
   ni se crea estado de partida, y el programa no se cae (FR-323; 001 FR-122).

---

### Casos borde

- **La sala inicial es `sala_salida`, o `llave_salida` está en la sala inicial**: se aplica la definición
  de FR-304 sin excepciones; en el segundo caso `llave_salida` es obtenible desde el instante 0.
- **Ninguna puerta hacia `sala_salida` requiere `llave_salida`** (incluida una cripta sin puertas
  cerradas): la cripta no es resoluble, porque la victoria de P1 §2.12 es imposible, y el reporte indica
  ese motivo de forma explícita (FR-322, escenario H1-2).
- **`sala_salida` es alcanzable por una salida abierta, pero también existe una puerta de salida**: la
  definición exige llegar «a través de una puerta que requiere `llave_salida`»; basta con que esa puerta
  tenga un lado en la región alcanzable y `llave_salida` sea obtenible (FR-304).
- **Una llave obtenible pero innecesaria para ganar**: aparece igual en el orden, porque el orden incluye
  todas las llaves obtenibles de la cripta (FR-305).
- **Varios ciclos independientes**: cada llave no obtenible que forma parte de un ciclo aparece en al menos
  un ciclo señalado, sin repetir ciclos y en un orden determinista (FR-310).
- **Una llave no obtenible que no está en un ciclo, sino que depende de uno** (escenario H2-4): aparece en
  la lista de llaves no obtenibles y se lista junto con el ciclo del que depende (FR-310).
- **Una puerta declara llave solo en una de sus caras**: la llave, el estado cerrado y el cierre automático
  de esa cara valen para las dos salas que une (FR-302, escenario H1-10). Si ninguna cara declara llave,
  cada cara se rige por lo que declara: una cara cerrada sin llave no se atraviesa en ese sentido.
- **Las dos caras de una puerta declaran llaves distintas**: no es un error de datos. Cada cara se rige
  por lo que declara; para atravesar la puerta desde una sala hace falta la llave de la cara de esa sala,
  y en la frontera bloqueada la puerta aparece con la llave de la cara de la sala alcanzable (FR-302,
  FR-308, escenario H2-9).
- **Esqueleto con un error de datos de 001 FR-122** (costo no entero o menor que 1, o costos distintos
  entre las dos caras de una salida): la verificación no concluye; `--verificar` termina con código 1 y la
  partida no inicia, ni siquiera con `--forzar` (FR-323, escenarios H3-8 y H4-5).
- **La misma llave aparece en varias ubicaciones**: cada una es una copia válida; basta con que una sea
  alcanzable, y el reporte muestra todas en un orden determinista (FR-316, escenarios H1-11 y H1-12).
- **Una salida sin vuelta que solo va de una sala de afuera hacia la región alcanzable**: no es parte de la
  frontera bloqueada (FR-308).
- **Una misma llave abre varias puertas**: no se consume (FR-302, escenario H1-7).
- **El enemigo que suelta una llave se mueve o está dormido**: no importa; la llave es obtenible en la sala
  donde el enemigo inicia (FR-303).
- **Puerta con cierre automático o trampa en el camino**: no bloquea (FR-302).
- **Una puerta cerrada aparece desde sus dos salas**: en la frontera bloqueada se lista una sola vez
  (FR-308).
- **Llave requerida por una puerta sin ubicación en la lista** (incluida `llave_salida`): es no obtenible y
  aparece en el reporte como «sin ubicación»; no es un error de datos (FR-321, escenario H2-6).
- **Ubicación con una sala que no existe en el esqueleto**: error de datos; la verificación no concluye
  (FR-321, escenario H2-7).
- **Ubicación con una instancia de enemigo inexistente**: no se valida; se usa la sala de la ubicación
  (FR-321, escenario H2-8).
- **Cargar una partida guardada o `--replay`**: no se verifica ni se bloquea, aunque la cripta no sea
  resoluble (FR-301, escenario H4-4).
- **`--verificar` junto con `--forzar`**: `--verificar` no inicia partida, así que `--forzar` no tiene
  efecto (FR-314).
- **Código de salida de `--verificar`**: 0 resoluble, 3 no resoluble, 1 verificación no concluida
  (incluidos los errores de datos de FR-321 y FR-323) (FR-314).
- **No se pudo obtener la ubicación de llaves**: la verificación no concluye; ver FR-320.

---

## Requisitos *(obligatorio)*

### Requisitos funcionales

**Reglas de la verificación**

- **FR-301**: Antes de iniciar una partida nueva, el programa DEBE determinar si la cripta es resoluble,
  usando únicamente el esqueleto (salas, salidas, estado abierto o cerrado de cada salida y llave que
  requiere), `sala_inicial`, `sala_salida`, `llave_salida` y la ubicación de las llaves. La verificación
  NO DEBE requerir el contenido de las salas, NO DEBE consumir el generador aleatorio de la partida y NO
  DEBE modificar ningún estado del juego. Cargar una partida guardada y `--replay` NO DEBEN ejecutar la
  verificación ni bloquearse por ella, porque reanudan o reproducen una partida que ya inició.
- **FR-302**: La verificación DEBE suponer que: el jugador puede atravesar cualquier salida abierta y
  cualquier salida cerrada cuya llave ya obtuvo; las llaves no se consumen; todo enemigo puede ser
  derrotado; las trampas y los cierres automáticos no bloquean, porque una puerta puede volver a abrirse
  con la misma llave. El costo de las salidas NO DEBE afectar el veredicto, el orden ni el reporte. Las
  caras de una puerta DEBEN combinarse como en la primera parte: si una cara declara la llave que requiere
  y la otra no declara ninguna llave, la llave, el estado cerrado y el cierre automático de la primera
  DEBEN valer para las dos. Si ninguna de las dos caras declara llave, cada cara DEBE regirse por lo que
  declara: una cara cerrada sin llave no puede atravesarse en ese sentido. «Cerrada» ausente, null o false
  significan lo mismo: la cara no declara cierre. Si las dos caras declaran llave, cada cara DEBE regirse
  por lo que declara (su llave, su estado cerrado y su cierre automático): para atravesar la puerta desde
  una sala hace falta la llave que declara la cara de esa sala. Que las dos caras declaren llaves
  distintas NO DEBE tratarse como error de datos.
- **FR-303**: Una llave cuya ubicación indica un enemigo DEBE considerarse obtenible en la sala indicada en
  su ubicación, que es la sala donde ese enemigo inicia, independientemente del comportamiento del enemigo
  y de hacia dónde pueda moverse durante la partida.
- **FR-304**: Una cripta DEBE considerarse resoluble si, partiendo de la sala inicial y bajo los supuestos
  de FR-302 y FR-303, el jugador puede obtener `llave_salida` y llegar a `sala_salida` a través de una
  puerta que requiere `llave_salida`. En cualquier otro caso DEBE considerarse no resoluble.
- **FR-305**: Si la cripta es resoluble, el resultado DEBE incluir un orden de obtención de llaves en el
  que cada llave aparece después de todas las llaves necesarias para alcanzarla. Un orden es válido si,
  para cada llave del orden, alguna de sus salas es alcanzable desde la sala inicial usando solo salidas abiertas y
  puertas cuyas llaves aparecen antes en el orden. El orden DEBE incluir todas las llaves obtenibles de la
  cripta, incluida `llave_salida`, y no solo las necesarias para ganar.
- **FR-306**: El resultado de la verificación (veredicto, orden de llaves y reporte, incluido el ciclo
  señalado) DEBE ser determinista: la misma cripta, en la misma versión, DEBE producir siempre el mismo
  resultado, en cualquier ejecución, en línea o con `--offline`. Cuando hay varios órdenes válidos, DEBE
  producirse siempre el mismo.

**Reporte de una cripta no resoluble**

- **FR-307**: Si la cripta no es resoluble, el reporte DEBE listar todas las llaves que no pueden
  obtenerse bajo los supuestos de FR-302 y FR-303, y ninguna llave obtenible.
- **FR-308**: El reporte DEBE listar las puertas de la frontera bloqueada, es decir, las salidas cerradas
  que van desde una sala de la región alcanzable hacia una sala fuera de ella, indicando para cada una las
  dos salas que une y la llave que requiere. Una salida sin vuelta que solo va de una sala de afuera hacia
  la región alcanzable NO DEBE considerarse frontera. Cada puerta DEBE aparecer una sola vez. Si las caras
  de la puerta declaran llaves distintas, la llave indicada DEBE ser la de la cara de la sala alcanzable
  (FR-302).
- **FR-309**: El reporte DEBE indicar dónde se encuentra cada llave que aparece en él (las no obtenibles y
  las que requieren las puertas de la frontera): su sala y, si la suelta un enemigo, la instancia de ese
  enemigo. Si la llave tiene varias ubicaciones, DEBE indicarlas todas en un orden determinista (FR-306).
  Si la llave no aparece en la lista de ubicaciones, DEBE indicar «sin ubicación» (FR-321).
- **FR-310**: Si una llave está ubicada detrás de puertas que solo ella abre, directamente o mediante una
  cadena de llaves, el reporte DEBE señalar el ciclo concreto: la secuencia de llaves que lo forman y, para
  cada una, la sala donde está y la puerta que la bloquea con la llave que esa puerta requiere, hasta
  volver a la primera llave. Cada llave no obtenible que forma parte de un ciclo DEBE aparecer en al menos
  un ciclo señalado; NO DEBEN repetirse ciclos, y qué ciclos se señalan, por qué llave empiezan y en qué
  orden se listan DEBE ser determinista (FR-306). Las llaves no obtenibles que no forman parte de un ciclo,
  pero dependen de uno, DEBEN listarse junto con el ciclo del que dependen.

**Inicio de partida y banderas**

- **FR-311**: Si la cripta no es resoluble y no se usa `--forzar`, la partida NO DEBE iniciar y DEBE
  mostrarse el reporte de no resolubilidad.
- **FR-312**: Con `--forzar`, la partida DEBE iniciar aunque la cripta no sea resoluble, y el reporte DEBE
  mostrarse igual. Con una cripta resoluble, `--forzar` NO DEBE cambiar nada. `--forzar` NO permite
  iniciar con un esqueleto que tiene un error de datos de 001 FR-122 (FR-323).
- **FR-313**: Al iniciar una partida, el resultado de la verificación (resoluble con su orden de llaves,
  o el reporte de no resolubilidad) DEBE quedar disponible para que la interfaz lo muestre (§7.3). Cómo se
  dibuja queda fuera de alcance.
- **FR-314**: `--verificar <cripta>` DEBE ejecutar únicamente la verificación y mostrar su resultado, sin
  instanciar la vista y sin iniciar una partida. DEBE funcionar también con `--offline`. Al terminar, el
  programa DEBE devolver el código de salida 0 si la cripta es resoluble, 3 si no es resoluble y 1 si la
  verificación no concluyó (FR-320, FR-321, FR-323). El código 2 sigue reservado para los argumentos
  inválidos, como en la primera parte, y `--verificar` NO DEBE usarlo para ningún veredicto.
- **FR-315**: El resultado de `--verificar` DEBE ser idéntico al de la verificación que se hace al iniciar
  una partida con la misma cripta.

**Datos de ubicación de llaves**

- **FR-316**: La ubicación de cada llave DEBE leerse con su id, su sala y, opcionalmente, la instancia de
  enemigo que la suelta. Cuando existe el enemigo, la llave está en el campo `suelta` de esa instancia y la
  sala es donde el enemigo inicia. Una misma llave PUEDE aparecer en varias ubicaciones: cada una DEBE
  tratarse como una copia válida, y la llave DEBE considerarse obtenible si alguna de sus salas es
  alcanzable.
- **FR-317**: Obtener la ubicación de las llaves del servicio DEBE contar dentro de
  `presupuesto_solicitudes`. La respuesta DEBE considerarse válida mientras coincida la versión de la
  cripta, DEBE poder persistirse con el resto de los datos de la cripta y, mientras sea válida, NO DEBE
  volver a pedirse.
- **FR-318**: Con `--offline`, la ubicación de las llaves DEBE leerse del paquete local, sin ninguna
  solicitud de red.
- **FR-319**: Los datos persistidos por la primera parte DEBEN invalidarse con la validación de versión ya
  existente, sin borrar archivos a mano.
- **FR-320**: Si la ubicación de las llaves no puede obtenerse (presupuesto agotado, HTTP 429, error de red
  o ausencia en el paquete local), el programa DEBE mostrar un mensaje con contexto, indicar que la
  verificación no concluyó y NO DEBE caerse. En ese caso la partida NO DEBE iniciar salvo con `--forzar`.
- **FR-321**: Las inconsistencias entre la ubicación de las llaves y el esqueleto DEBEN tratarse así:
  - Una llave que requiere alguna puerta (incluida `llave_salida`) y que no aparece en la lista de
    ubicaciones DEBE considerarse no obtenible y aparecer en el reporte con la indicación «sin ubicación».
    NO DEBE tratarse como error de datos, porque el servicio publica criptas no resolubles (§4.3).
  - Una ubicación cuya sala no existe en el esqueleto DEBE tratarse como error de datos: el programa DEBE
    informarlo con contexto (qué llave y qué sala), la verificación no concluye y el efecto DEBE ser el
    mismo que en FR-320 (la partida no inicia salvo con `--forzar`). El programa NO DEBE caerse.
  - La instancia de enemigo de una ubicación NO DEBE validarse en la verificación, porque comprobarla
    exigiría descargar el contenido de salas (FR-301); DEBE usarse la sala que trae la ubicación.
- **FR-322**: Si ninguna puerta hacia `sala_salida` requiere `llave_salida` (por ejemplo, en una cripta sin
  puertas cerradas), la cripta DEBE considerarse no resoluble, porque la victoria de P1 §2.12 exige entrar a
  `sala_salida` después de abrir con la llave correspondiente la puerta que da acceso a ella. El reporte
  DEBE indicar ese motivo de forma explícita.
- **FR-323**: Si el esqueleto tiene un error de datos de los que define 001 FR-122 (una salida con un costo
  no entero o menor que 1, o con costos distintos entre sus dos caras), la verificación NO DEBE concluir:
  NO DEBE mostrarse ningún veredicto, el programa DEBE mostrar el error con contexto (qué salida y qué
  campo) y NO DEBE caerse. `--verificar` DEBE terminar con el código de salida 1 (FR-314). La partida NO
  DEBE iniciar, ni siquiera con `--forzar`, porque 001 FR-122 exige que con esos datos la partida no inicie
  y el juego supone datos válidos (a diferencia de FR-320, donde `--forzar` sí permite jugar). Con costos
  válidos, el costo sigue sin afectar el veredicto (FR-302). Concuerda con el escenario H3-7 de la feature
  001.

### Requisitos de rendimiento

- **NFR-301**: La verificación DEBE tardar menos de 200 ms con la cripta publicada más grande, medida en
  el equipo local con los datos ya disponibles, sin red ni renderizado (§6.1).
- **NFR-302**: El costo total de la verificación DEBE crecer aproximadamente de forma lineal con la
  cantidad de salas, salidas y llaves. Obtener una llave NO DEBE implicar repetir el recorrido completo de
  la cripta (§5.4).
- **NFR-303**: El reporte de una cripta no resoluble (frontera bloqueada, dependencias entre llaves y
  ciclo) DEBE obtenerse del mismo recorrido que decide la resolubilidad, sin recorridos adicionales por
  cada llave (§5.4).
- **NFR-304**: `--bench` DEBE comparar la verificación contra la alternativa de repetir el recorrido
  completo cada vez que se obtiene una llave, en criptas sintéticas deterministas por semilla con muchas
  llaves encadenadas y al menos tres tamaños distintos (§5.4, §6.3, Principio VIII).

### Entidades clave

- **Esqueleto de la cripta**: todas las salas y salidas, con el estado abierto o cerrado de cada salida y
  la llave que requiere cada puerta. Se conoce completo al iniciar la cripta.
- **Ubicación de una llave**: id de la llave, sala y, opcionalmente, instancia de enemigo que la suelta.
  Válida mientras coincida la versión de la cripta. Una llave puede tener varias ubicaciones (copias).
- **Región alcanzable**: salas a las que el jugador puede llegar desde la sala inicial bajo los supuestos
  de la verificación.
- **Frontera bloqueada**: salidas cerradas que van desde una sala de la región alcanzable hacia una sala
  fuera de ella. Una salida sin vuelta que solo va de afuera hacia adentro no es frontera.
- **Orden de obtención de llaves**: secuencia de llaves en la que cada una aparece después de todas las
  necesarias para alcanzarla.
- **Ciclo de dependencia**: secuencia de llaves en la que cada una está bloqueada por una puerta que
  requiere la siguiente, y la última por una que requiere la primera.
- **Reporte de resolubilidad**: veredicto y, según el caso, orden de llaves o llaves no obtenibles,
  frontera bloqueada, ubicaciones y ciclo.

---

## Trazabilidad del Apéndice B «Resolubilidad» (Principio X)

| # | Caso del Apéndice B | Escenario | Requisitos | Prueba |
|---|---|---|---|---|
| 1 | `llave_salida` está detrás de la única puerta que ella misma abre: no resoluble; el reporte señala el ciclo | H2-1 | FR-304, FR-307, FR-308, FR-309, FR-310 | Se define en `tasks.md` |
| 2 | Una llave está en el campo `suelta` de un enemigo errante: la verificación la ubica en la sala inicial del enemigo | H1-4 | FR-303, FR-316 | Se define en `tasks.md` |
| 3 | Existen varios órdenes válidos de obtención de llaves: dos ejecuciones producen el mismo orden | H1-5 | FR-305, FR-306 | Se define en `tasks.md` |
| 4 | Cripta no resoluble sin `--forzar`: la partida no inicia y se muestra el reporte | H4-1 | FR-311 | Se define en `tasks.md` |

Cada prueba citará el identificador del requisito que verifica (Principio X).

### Cobertura de requisitos funcionales

| Requisito | Escenarios |
|---|---|
| FR-301 | H1-1, H1-8, H2-8, H4-4 |
| FR-302 | H1-6, H1-7, H1-10, H2-9 |
| FR-303 | H1-4, H2-8 |
| FR-304 | H1-1, H1-2, H1-3, H2-1 |
| FR-305 | H1-1, H1-3, H1-5, H1-10, H1-11 |
| FR-306 | H1-5, H1-12, H2-3, H3-3 |
| FR-307 | H2-1, H2-2, H2-4, H2-5, H2-6 |
| FR-308 | H2-1, H2-5, H2-6, H2-9 |
| FR-309 | H1-12, H2-1, H2-4, H2-6 |
| FR-310 | H2-1, H2-2, H2-3, H2-4 |
| FR-311 | H4-1 |
| FR-312 | H4-2, H4-3 |
| FR-313 | H1-9, H4-2 |
| FR-314 | H3-1, H3-2, H3-3, H3-7, H3-8 |
| FR-315 | H3-1, H3-2 |
| FR-316 | H1-4, H1-11, H1-12 |
| FR-317 | H3-4, H3-5 |
| FR-318 | H3-3 |
| FR-319 | H3-6 |
| FR-320 | H2-7, H3-7 |
| FR-321 | H2-6, H2-7, H2-8 |
| FR-322 | H1-2 |
| FR-323 | H3-8, H4-5 |

---

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **SC-301**: Los 4 casos del Apéndice B «Resolubilidad» pasan como pruebas automatizadas, y cada una cita
  su requisito.
- **SC-302**: El 100 % de los escenarios de aceptación de esta spec tiene al menos una prueba automatizada
  o un `partida.log` de reproducción.
- **SC-303**: Al verificar 10 veces cada cripta de prueba (en ejecuciones separadas, en línea y con
  `--offline`), el resultado es idéntico en las 10 ejecuciones.
- **SC-304**: En todas las criptas resolubles de prueba, el orden entregado es válido según FR-305:
  recorrerlo llave por llave nunca exige una llave que aparece después.
- **SC-305**: En todas las criptas no resolubles de prueba, una persona puede identificar, leyendo solo el
  reporte, qué llaves faltan, qué puertas bloquean, dónde está cada llave y, si existe, el ciclo concreto,
  sin consultar los datos de la cripta.
- **SC-306**: `--bench` muestra que la verificación de la cripta publicada más grande tarda menos de 200 ms.
- **SC-307**: En `--bench`, al multiplicar por 10 la cantidad de salas, salidas y llaves de una cripta
  sintética con llaves encadenadas, el tiempo de la verificación crece a lo sumo 20 veces, mientras que el
  de la alternativa de repetir el recorrido por cada llave crece de forma claramente mayor.
- **SC-308**: `--verificar` produce su resultado sin instanciar la vista, con y sin `--offline`, y con
  `--offline` no hace ninguna solicitud de red. En el 100 % de las criptas de prueba, su código de salida
  (0, 3 o 1) coincide con el veredicto esperado.

---

## Supuestos

- Si ninguna cara de una puerta declara llave, cada cara se rige por lo que declara: una cara cerrada sin
  llave no puede abrirse y nunca se atraviesa en ese sentido en la verificación (FR-302). Si las dos caras
  declaran llave, aunque sean distintas, también se rige cada una por lo que declara (FR-302).
- Los costos del esqueleto son válidos según 001 FR-122 para que la verificación concluya y la partida
  inicie; si no lo son, ni `--forzar` permite jugar (FR-323).
- La sala que trae la ubicación de una llave soltada por un enemigo es confiable como sala inicial de ese
  enemigo (§4.2); la verificación no la contrasta con el contenido de las salas, que no descarga (FR-301,
  FR-321).
- Si la ubicación de las llaves no puede obtenerse, la verificación no concluye: el programa informa que
  la verificación no concluyó (no que la cripta sea no resoluble); para iniciar la partida, solo `--forzar`
  permite jugar (FR-320).
- El umbral de SC-307 (10× de tamaño, a lo sumo 20× de tiempo) concreta «aproximadamente lineal» de §5.4;
  si se ajusta, se corrige primero esta spec (Principio IX).
- El límite de 200 ms puede ajustarse si se publica una enmienda con la cripta de referencia (§6.1).
