# Investigación (fase 0): Verificación de resolubilidad

**Feature**: `003-resolubilidad` · **Plan**: [plan.md](plan.md) · **Spec**: [spec.md](spec.md) · **Fecha**: 2026-11-13

Cada decisión tiene: decisión, por qué, alternativas descartadas con su complejidad y medición prevista. Notación:
S = salas, E = salidas (caras; E ≤ 4S), U = ubicaciones de llaves, K = llaves distintas, M = menciones de llaves
(caras con llave + ubicaciones + `llave_salida`, M ≤ E + U + 1), F = puertas de la frontera.

No quedó ningún NEEDS CLARIFICATION: los puntos abiertos están como hallazgos (al final), y ninguno bloquea.

---

## R0. Revisión de las estructuras ya implementadas (Principio II)

Lo que pide la Parte II (§3.5, §5.4): un recorrido que no se repita al obtener cada llave, la frontera y las
dependencias del mismo recorrido, ciclos deterministas, sin `dict`, `set`, `collections`, `heapq`, `bisect` ni
`sorted`/`list.sort`.

| Estructura | Qué ofrece | Limitación frente a la 003 | Decisión |
|---|---|---|---|
| `Estructuras/Cola.py` | FIFO con nodos, todo O(1) | Ninguna para un recorrido por anchura | **Se usa** como cola del recorrido (R4) y de la fase hacia afuera (R6) |
| `Estructuras/Ordenador.py` | Ordenamiento estable propio (inserción o mezcla), O(n log n) peor caso | Recibe un comparador; no deduplica | **Se usa** para el índice de llaves (R3), cada oleada, la frontera, las ubicaciones y los niveles de puertas (R5) |
| `Estructuras/MonticuloMinimo.py` | Mínimo por prioridad | El costo no afecta la verificación (FR-302): no hay prioridad | No se usa |
| `Estructuras/ListaDoble.py` | Inserción y borrado en el medio | No hace falta borrar en el medio: las listas de espera se recorren una vez | No se usa |
| `Estructuras/BufferCircular.py` | Pisa lo más antiguo | La verificación no descarta nada | No se usa |
| `Data/GestorEsqueleto.py` | Array indexado por id de sala, `existe_sala` O(1) | Ninguna para validar ubicaciones | **Se usa** en Data para FR-321 (R2) |
| `Logic/Mazmorra.py` (`cargar_esqueleto`, `salida`) | Combinación de caras de la primera parte (`_igualar_caras`) | Es estado vivo del juego; se usa una instancia **aparte**, que se descarta | **Se usa** solo para leer las caras combinadas (R4) |
| `Logic/GrafoEsqueleto.py` (001) | Salidas abiertas **ahora**, con costo | Lee el estado vivo y no conoce llaves | No se usa |
| `Estructuras/BusquedaBinaria.py` (004, aún no existe) | Último ≤ clave entera | No hace falta: el índice de llaves se arma ordenando y compactando, sin búsquedas (R3) | No se usa; la 003 no depende de la 004 |

Lo único nuevo es código de Logic (R3 a R6). **No se agrega nada a `Estructuras/`.**

---

## R1. Contrato de datos de las llaves (entrega atrasada del 9/11)

**Decisión**: detalle en [contracts/contrato-llaves.md](contracts/contrato-llaves.md).

- **DTO**: `DTO/UbicacionLlaveDTO.py`, `UbicacionLlaveDTO(id: str, sala: int, enemigo: str | None = None)`,
  inmutable, con `desde_diccionario` y `a_diccionario` (este omite `enemigo` si es `None`, igual que el API). La
  lista se entrega como `list[UbicacionLlaveDTO]` **en el orden de la respuesta**; Data no ordena ni deduplica
  (eso es de Logic, R5).
- **FuenteDatos**: método nuevo `obtener_llaves(id_cripta) -> list[UbicacionLlaveDTO]`, **no abstracto**, cuya
  implementación por defecto lanza `ErrorRed` («esta fuente no entrega la ubicación de las llaves»). Es una sola
  solicitud a `GET /criptas/{id}/llaves` y, en `FuenteRed`, cuenta en el presupuesto porque pasa por `ClienteHttp`
  como todas (FR-317, Principio VII).
- **FuenteJson**: `obtener_llaves` y el estático público `ubicaciones_desde_diccionario(d)` (como
  `ficha_desde_diccionario`, porque también lo usa el almacén). Valida **formato**: `llaves` es una lista; cada
  elemento tiene `id` texto no vacío, `sala` entero de verdad (`es_entero`: un `bool` no cuenta) y `enemigo`
  ausente, `null` o texto no vacío. Cualquier falla pasa por `_traducir` y llega como `ErrorRed` de formato,
  igual que el resto de la Parte 1. Una lista vacía es válida (todas las llaves quedan «sin ubicación», FR-321).
- **FuenteOffline** (`LectorPaquete`): ruta nueva `criptas/{id}/llaves` → `paquete/<id>/llaves.json`. Si falta,
  el `ErrorRed` «falta el archivo» que ya existe es el «paquete local sin ubicación de llaves» de FR-320.
- **DescargadorPaquete**: descarga `GET /criptas/{id}/llaves` después de las páginas del esqueleto y escribe
  `<id>/llaves.json` **tal cual**, junto con lo demás al final (si algo falla, el paquete anterior queda intacto).
  **Costos y cazadores**: no hace falta código nuevo. El paquete guarda las respuestas tal cual: `costo` viaja en
  `salas_p<N>.json` y `rango` en `catalogo.json`; los tipos de los cazadores entran al catálogo por el contenido de
  las salas, como cualquier enemigo. Lo que sí hace falta es **regenerar el paquete** cuando el API publique las
  versiones de la Parte II (hallazgo H-3).
- **Persistencia** (FR-317, FR-319): `Data/AlmacenLlaves.py`, un archivo por cripta en `cache/llaves/<id>.json`
  con `{"id", "version", "llaves": [...]}` (la respuesta del API más su versión). Al leer se compara con
  `validar_version` (Security, la validación de versión que ya existe) contra `CriptaDTO.version`, que ya se pidió
  para cargar el esqueleto: **no cuesta una solicitud extra**. Distinta versión, archivo dañado o id distinto ⇒ se
  trata como ausente y la siguiente escritura lo reemplaza: nadie borra archivos a mano (FR-319). Ids que no pasan
  `es_nombre_seguro` no se persisten (se vuelven a pedir). Escritura con `.tmp` + `os.replace`, como `AlmacenCatalogo`.
- **Con `--offline` no se usa el almacén** (FR-318: se lee del paquete). Así un `llaves.json` ausente del paquete no
  queda tapado por una respuesta en línea persistida (escenario H3-7). La única condición está donde ya se elige la
  fuente según `config.offline`, en Service; no hay `if` dispersos (Principio I).
- **Orquestación en Data**: `Data/GestorLlaves.py`, `obtener(cripta, esqueleto) -> list[UbicacionLlaveDTO]`:
  1) si hay almacén y tiene la versión vigente, la usa; 2) si no, `fuente.obtener_llaves` y la persiste; 3) valida
  FR-321 contra el esqueleto.
- **FR-321 (sala inexistente)**: función nueva en `Data/ValidacionDatos.py`,
  `validar_ubicaciones(operacion, ubicaciones, existe_sala)`, que lanza `ErrorDatos` con la llave, la sala y, si hay,
  el enemigo: «la llave A está en la sala 99, que no existe en el esqueleto». Recibe `existe_sala` (la función
  `GestorEsqueleto.existe_sala`) y no el gestor, porque `GestorEsqueleto` ya importa `ValidacionDatos` y se
  formaría un ciclo de importación. O(U). La instancia de enemigo **no** se valida (FR-321, FR-301).
- **Se persiste antes de validar FR-321**: la respuesta es la del API para esa versión; volver a pedirla no la
  arregla (es justamente la semántica de `ErrorDatos`). Así la segunda verificación da el mismo error sin gastar
  otra solicitud (FR-317).
- **FR-323** no cambia: `GestorEsqueleto.cargar` ya lanza `ErrorDatos` por costos (T002 de la 001).

**Por qué**: reutiliza el camino de la Parte 1 (proveedor de JSON → `FuenteJson` → DTO), así `--offline` es el mismo
código; la persistencia copia el patrón ya probado de `AlmacenCatalogo`.

**Alternativas descartadas**:

| Alternativa | Por qué no | Costo |
|---|---|---|
| `obtener_llaves` **abstracto** | Rompe `_FuenteCuadricula` de `BenchDatos` y `FuenteCuadricula` de `tests/Utilidades.py`, que no lo necesitan | — |
| Persistir en una carpeta por versión (`cache/llaves/<version>/…`) como el catálogo | La versión es por cripta, no global: un archivo por cripta con su versión adentro es más simple y no deja carpetas viejas | igual: O(1) archivos por cripta |
| Validar FR-321 en Logic | Constitución: Data valida formato y coherencia de datos; Logic supone datos válidos (igual que FR-122) | O(U) en los dos casos |
| Pedir `GET /criptas/{id}/version` para validar lo persistido | La versión ya llega en los datos generales, que siempre se piden antes del esqueleto | +1 solicitud por verificación |

**Medición prevista**: ninguna (no es un problema evaluado de §5). Pruebas: H3-3 a H3-7.

---

## R2. DTO del reporte para el integrante 3 (vence hoy, 13/11)

**Decisión**: `DTO/ReporteResolubilidadDTO.py`, detalle en
[contracts/contrato-reporte-resolubilidad.md](contracts/contrato-reporte-resolubilidad.md). Solo transporta datos,
ya ordenados y completos, para que la interfaz lo muestre sin calcular nada:

- `veredicto`: `"resoluble"`, `"no_resoluble"` o `"no_concluyo"` (constantes del módulo).
- `orden_llaves: list[str]` (solo si es resoluble).
- `llaves_no_obtenibles: list[LlaveNoObtenibleDTO]`, cada una con sus `ubicaciones: list[UbicacionLlaveDTO]`
  ordenadas; lista vacía ⇒ «sin ubicación».
- `frontera: list[PuertaLlaveDTO]` (sala alcanzable, dirección, sala de afuera, llave o `None` ⇒ «sin llave: no se
  puede abrir»).
- `ciclos: list[CicloLlavesDTO]`, cada uno con `pasos` y sus `dependientes`.
- `motivo: str | None` (FR-322, texto explícito) y `mensaje: str | None` (por qué no concluyó).
- Identificación: `id_cripta`, `version_cripta`, `llave_salida`.

Los campos nuevos que se agreguen después van **al final y con valor por defecto**, para no romper constructores.

**Por qué**: el texto del motivo de FR-322 lo arma Logic para que `--verificar` y la ventana muestren lo mismo
(FR-315). La consola usa un formateador propio (`UIController/TextoResolubilidad.py`) que la vista puede reutilizar.

**Alternativas descartadas**: (a) entregar los arrays crudos del recorrido y que la vista arme el reporte: la vista
calcularía reglas (prohibido por el Principio I); (b) un único texto ya formateado: la vista no podría dibujarlo a su
manera ni las pruebas comparar cada parte (SC-305); (c) un booleano para FR-322: obliga a cada interfaz a redactar
el motivo y puede divergir entre consola y ventana.

---

## R3. Índice propio de llaves: ordenar y compactar (sin `dict` ni búsquedas)

**Problema**: el recorrido necesita, para cada llave, un arreglo «esperando[k]» y un indicador «obtenida[k]», pero
las llaves son textos y no se puede usar `dict` como índice.

**Decisión** (`Logic/GrafoLlaves.py`): se arma una lista de **menciones** `(id_llave, tipo, posición)`: una por cara
cerrada con llave, una por ubicación y una por `llave_salida`. Se ordena con `Ordenador.ordenar` por `id_llave` (y
desempata por tipo y posición, así el resultado no depende del orden de entrada). Se recorre una vez: cada vez que
cambia el id se abre un índice nuevo `0, 1, 2…` y se **escribe ese índice de vuelta** en el arreglo de la cara o de la
ubicación mencionada. Resultado: `ids[k]` (texto de cada llave), `llave_cara[c]` y `llave_ubicacion[i]` como enteros.
**Los índices quedan en orden de id**, así que desempatar por índice es desempatar por id (R5).

**Complejidad**: tiempo O(M log M) por el ordenamiento + O(M) la compactación; espacio O(M + K).

**Alternativas descartadas**:

| Alternativa | Por qué no | Costo |
|---|---|---|
| `dict` id → índice | Prohibido como índice (Principio II) | O(M) esperado |
| Búsqueda lineal en la lista de ids | Cuadrático en la práctica: con 1 000 caras con llave y 100 llaves, ~10⁵ comparaciones de texto por verificación; crece O(M·K) y rompe NFR-302 | O(M·K) |
| Ids ordenados + búsqueda binaria por cada mención | Correcto, pero agrega una búsqueda por mención (O(M log K)) y necesita una búsqueda binaria de textos que hoy no existe (la de la 004 es para claves enteras y todavía no está) | O(M log M + M log K) |

**Medición prevista**: el desglose B4 de `--bench` (preparación frente a recorrido) muestra que el ordenamiento no
domina con 1 000 salas.

---

## R4. Recorrido incremental por oleadas, con la frontera agrupada por llave (§5.4, NFR-302, NFR-303)

**Preparación** (`Logic/GrafoLlaves.py`): se crea una `Mazmorra` **aparte** con `cargar_esqueleto(salas)`, que aplica
la regla de caras de la primera parte (`_igualar_caras`): una cara sin llave toma la llave y el estado cerrado de su
inversa si esta declara llave; si las dos declaran llave (la misma o distintas) o ninguna, cada cara se rige por su
llave y su estado cerrado (FR-302, H1-10, H2-9). Usar la misma `Mazmorra` garantiza que la verificación y el juego
combinen las caras igual, sin duplicar la regla. Después se leen las caras en arreglos planos indexados por
`c = sala*4 + dirección`:

- `tipo_cara[c]`: 0 sin salida, 1 abierta (`cerrada` falso), 2 cerrada con llave, 3 cerrada sin llave;
- `destino[c]`; `llave_cara[c]` (índice de R3, o −1).

`cerrada` ausente, `null` o `false` ya llegan como `False` en `SalidaDTO` (FR-302). Una cara con llave pero no
cerrada es abierta, como en P1 (`llave_requerida` devuelve `None`). El costo no se lee (FR-302). La `Mazmorra`
auxiliar se descarta: no toca el motor, el generador aleatorio ni el contenido de las salas (FR-301).

**El cierre automático no se lee.** No es un dato por cara: abrir una puerta abre sus dos caras y se programa el
cierre automático de la cara desde la que se abre, que cierra las dos (FR-302). `_igualar_caras` también lo copia a
la cara inversa, pero eso solo le importa al motor. Por el supuesto de §3.5 («una puerta puede volver a abrirse con
la misma llave»), la verificación no lo considera un bloqueo, ni siquiera en una puerta con llaves distintas por cara,
donde volver después del cierre podría exigir la llave de la otra cara (caso borde de la spec, *decisión del grupo*).

**Arreglos que se calculan una vez para la salida** (FR-304, FR-322):

- `es_cara_de_salida[c]`: la cara `c` lleva a `sala_salida`, está cerrada y **su propia** llave (ya combinada) es
  `llave_salida`. Es la cara de la sala desde la que se entra, que es la que vale al abrir en la primera parte. Una
  cara de `sala_salida` hacia afuera que pide `llave_salida` no cuenta, y una puerta que pide `llave_salida` pero no
  lleva a `sala_salida` tampoco.
- `hay_puerta_de_salida`: existe al menos una cara así en todo el esqueleto, sea o no alcanzable. Si es falso,
  corresponde el motivo de FR-322.

**Estado del recorrido** (todo arreglos, ninguno `dict` ni `set`):

| Arreglo | Índice | Contenido |
|---|---|---|
| `alcanzable[s]` | sala | `bool` |
| `llaves_en_sala[s]` | sala | lista de índices de llave ubicados en `s` |
| `estado_llave[k]` | llave | 0 sin ver, 1 vista en esta oleada, 2 obtenida |
| `oleada_llave[k]` | llave | número de oleada en que se obtuvo, o −1 |
| `esperando[k]` | llave | **lista de caras `c` cerradas con llave `k` que salen de una sala alcanzable** |
| `sin_llave` | — | lista de caras cerradas sin llave que salen de una sala alcanzable |
| `caras_de_salida` | — | caras con `es_cara_de_salida[c]` que salen de una sala alcanzable |

**Algoritmo** (cada sala y cada cara se procesan una sola vez):

1. Se marca `sala_inicial` y se encola (`Cola` de `Estructuras/`).
2. **Oleada**: mientras la cola no esté vacía, se saca `u`. Cada llave `k` de `llaves_en_sala[u]` con
   `estado_llave[k] == 0` pasa a 1 y se anota en `nuevas`. Cada cara `c` de `u` (N, S, E, O):
   abierta → si el destino no es alcanzable, se marca y se encola; con llave `k` y `estado_llave[k] == 2` → igual;
   con llave `k` todavía no obtenida → se agrega `c` a `esperando[k]`; cerrada sin llave → se agrega a `sin_llave`.
   Además, si `es_cara_de_salida[c]`, se agrega `c` a `caras_de_salida` (sin importar si la llave ya se obtuvo).
3. **Fin de la oleada**: si `nuevas` está vacía, termina. Si no, se ordena `nuevas` por índice (= por id), cada una
   pasa a 2 con su número de oleada y se agrega al orden. Luego, **solo** para esas llaves, se recorre
   `esperando[k]`: cada cara cuyo destino aún no es alcanzable lo marca y lo encola. La lista se vacía. Vuelve a 2.
4. **Resoluble** (FR-304): `llave_salida` obtenida **y** `caras_de_salida` no vacía. Es decir, se llegó a
   `sala_salida` **por una cara que pide `llave_salida`** desde una sala alcanzable, porque esa cara se abre con esa
   llave. **No se usa `alcanzable[sala_salida]`**: llegar a `sala_salida` por una salida abierta, o por una cara que
   pide otra llave, no cuenta (caso borde «`sala_salida` alcanzable por una salida abierta»). Si
   `hay_puerta_de_salida` es falso, el veredicto es no resoluble con el motivo de FR-322, aunque `llave_salida` sea
   obtenible y `sala_salida` alcanzable por otro camino (H1-2 y caso borde de la Sesión 2026-11-13). Las dos
   comprobaciones son O(1) al final; las listas se arman durante el recorrido.
5. **Frontera** (FR-308): las caras que quedaron en `esperando[k]` de llaves no obtenidas y en `sin_llave` cuyo
   destino **sigue** fuera de la región. Cada cara sale de una sala alcanzable, así que una salida sin vuelta de
   afuera hacia adentro nunca entra (H2-11); como cada cara se agrega una vez, cada puerta aparece una vez (H2-5).
   La llave informada es la de la cara de la sala alcanzable (H2-9).

**Por qué es incremental**: obtener una llave reabre solo las puertas que la esperaban; nunca se vuelve a recorrer
lo ya alcanzado. Cada cara entra a lo sumo una vez en una lista de espera y sale a lo sumo una vez. Cada cara
(FR-302) se procesa por separado desde su propia sala.

**Complejidad**: tiempo O(S + E + U) del recorrido + O(K log K) de ordenar todas las oleadas juntas; espacio
O(S + E + U + K). Con la preparación (R3): O(S + E + U + M log M), «aproximadamente lineal» (NFR-302).

**Alternativas descartadas**:

| Alternativa | Por qué no | Costo |
|---|---|---|
| **Repetir el recorrido completo cada vez que se obtiene una llave** (la ingenua de §5.4) | Viola NFR-302; es la que mide `--bench` (R7) | O(K · (S + E + U)) |
| Frontera en una sola lista y revisarla entera al obtener cada llave | Cada llave revisa toda la frontera: O(K · F); con llaves encadenadas, F crece con la cripta | O(S + E + K·F) |
| Recorrido en profundidad con pila | Igual de lineal, pero el orden de obtención depende del orden de visita y no deja oleadas claras para el desempate (R5) | O(S + E + U) |
| `GrafoEsqueleto` de la 001 | Lee el estado vivo de la partida y solo salidas abiertas | — |

**Medición prevista**: B1 y B2 de `--bench` (R7).

---

## R5. Orden determinista (FR-305, FR-306) sin `sorted` ni `list.sort`

**Regla del orden de llaves**: el orden es la concatenación de las **oleadas** de R4. La oleada 0 son las llaves cuyas
salas se alcanzan sin ninguna llave; la oleada *i + 1*, las que se vuelven alcanzables al abrir las puertas de las
llaves de las oleadas ≤ *i*. **Dentro de cada oleada, por id ascendente** (comparación de texto de Python, por punto de
código, igual en cualquier máquina). Es válido según FR-305: cada llave de la oleada *i + 1* se alcanza usando solo
llaves de oleadas anteriores, que aparecen antes. Incluye todas las llaves obtenibles (FR-305).

Ejemplo H1-5: A (sala 2) y B (sala 3) son de la oleada 0 → `[A, B, llave_salida]`, sin importar en qué orden lleguen
las ubicaciones ni las páginas del esqueleto.

**Reglas de las demás listas del reporte**:

| Lista | Orden | Desempate |
|---|---|---|
| `orden_llaves` | oleada | id |
| `llaves_no_obtenibles` | id | — |
| `ubicaciones` de una llave | sala | sin enemigo antes que con enemigo; luego id de enemigo. Las ubicaciones **idénticas** se informan una vez |
| `frontera` | sala alcanzable | dirección N, S, E, O |
| `ciclos` | id de su llave inicial (la menor del ciclo) | — |
| `dependientes` de un ciclo | id | — |

**Cómo se ordena**: todo con `Ordenador.ordenar` (estable, sin `sorted`), con comparadores de enteros: los índices
de llave ya están en orden de id (R3), las caras se comparan por `c = sala*4 + dirección` y las ubicaciones se ordenan
una sola vez en la preparación por (índice de llave, sala, enemigo).

**Complejidad**: O(K log K + F log F + U log U) en total.

**Alternativas descartadas**: (a) orden de descubrimiento del recorrido sin ordenar: es determinista con la misma
entrada, pero depende del orden del JSON (de las ubicaciones o de las páginas), que no es una regla del juego;
(b) orden topológico global por id (siempre la menor llave disponible, con una cola de prioridad): también es válido,
pero necesita un montículo con claves de texto y no aporta nada sobre las oleadas, O((K + E) log K).

---

## R6. Ciclos de dependencia (FR-310) y llaves dependientes

**Definición operativa** (decisión del plan, coherente con H2-1, H2-2, H2-4 y H2-12): cada llave no obtenible con al
menos una ubicación alcanzable «desde afuera» tiene **una** puerta que la encierra; la llave depende de la llave de
esa puerta. Eso forma un grafo con **a lo sumo una arista de salida por llave** (grafo funcional), donde los ciclos son
disjuntos y fáciles de hallar sin repetir.

**Fase hacia afuera** (continuación del mismo recorrido, NFR-303; `Logic/RecorridoLlaves.py`):

1. Nivel 1 = las puertas de la frontera, ya ordenadas (R5). Para cada puerta, en ese orden: si su destino no tiene
   puerta asignada, se le asigna esa puerta y se inunda su **zona** con la `Cola`: salas unidas por caras abiertas o
   con llave ya obtenida. Las caras cerradas con llave no obtenida o sin llave que salen de la zona se anotan como
   puertas del nivel siguiente.
2. Al terminar un nivel, se ordenan sus puertas nuevas por (sala de origen, dirección) y se repite.

Así, la puerta que encierra a una sala es **la de menor (sala de origen, dirección) entre las del nivel más bajo
por las que se llega a su zona**: una regla de los datos, no del orden de entrada. Cada sala de afuera y cada cara se
procesan una vez: O(S + E) más ordenar las puertas de cada nivel, O(E log E) en el peor caso.

**Arista de cada llave no obtenible**: entre sus ubicaciones se usa la de menor nivel (desempate: orden de R5). Su
llave siguiente es la de la puerta que encierra esa sala; si la puerta no tiene llave («sin llave»), o la sala no se
alcanza ni cruzando puertas, o la llave no tiene ubicación, **no tiene arista** y no puede estar en un ciclo.

**Detección** (`Logic/CiclosLlaves.py`): se recorren las llaves no obtenibles por id. Desde cada una sin visitar se
sigue la arista marcando `marca[k] = número de recorrido`. Si se llega a una llave marcada **en este mismo
recorrido**, se encontró un ciclo nuevo; se rota para que empiece por su llave de menor id. Si se llega a una de un
recorrido anterior, no hay ciclo nuevo. Cada llave se visita una vez: no se repiten ciclos.

**Dependientes**: una llave que no está en un ciclo pero cuya cadena de aristas llega a uno depende de **la llave del
ciclo donde entra la cadena** (se calcula al volver del recorrido, sin repetir caminos). Se listan dentro de su ciclo,
por id (FR-310: «inmediatamente después del ciclo»). Las llaves que no llegan a ningún ciclo (por ejemplo, detrás de
una puerta sin llave o que dependen de una llave «sin ubicación») aparecen solo en `llaves_no_obtenibles`.

Comprobación con la spec: H2-1 → `llave_salida` → `llave_salida` (ciclo de una llave); H2-2 → A → B → A; H2-4 → C
depende de A; H2-12 → ciclos A–B y E–F, `llave_salida` y G dependen de A, H depende de E.

**Complejidad**: tiempo O(K) la detección + O(K log K) ordenar dependientes; espacio O(K).

**Alternativas descartadas**:

| Alternativa | Por qué no | Costo |
|---|---|---|
| Grafo completo de dependencias (todas las puertas que rodean cada llave) y componentes fuertemente conexas | Un ciclo «concreto» necesita elegir una puerta por paso igual; la complejidad extra (Tarjan, pila de recursión) no aporta a ningún escenario | O(K + D), D = dependencias |
| Para cada llave no obtenible, un recorrido aparte para ver qué la bloquea | Viola NFR-303 (recorridos adicionales por llave) | O(K · (S + E)) |
| Enumerar todos los ciclos simples | Puede ser exponencial y repetiría llaves en varios ciclos | exponencial |

**Límite conocido**: si una zona tiene varias puertas de entrada del mismo nivel, el ciclo señalado usa la de la regla
y no las otras; el reporte igual las lista todas en la frontera cuando salen de la región alcanzable.

---

## R7. `--bench` (NFR-304, SC-306, SC-307)

**Decisión**: `Service/BenchResolubilidad.py` (integrante 2), con `medir() -> list[ResultadoBenchDTO]`, agregado a la
lista por defecto de `Service/ServicioBench.py` (también del integrante 2). Mide con `Service/Cronometro.py` (mejor y
mediana) y no instancia la vista. **`--bench` no verifica como paso previo a una partida** (FR-301): no inicia
partidas, no llama a `ServicioResolubilidad` ni pide datos al API; llama directamente a `VerificadorResolubilidad`
(Logic) con las criptas sintéticas que genera.

**Criptas sintéticas** (`cripta_en_cuadricula(filas, columnas, semilla, resoluble)`), deterministas por semilla con
`random.Random(semilla)`:

- cuadrícula de `filas × columnas` salas, con salidas abiertas entre vecinas de la misma columna;
- entre la columna *c* y la *c + 1*, todas las salidas son puertas cerradas que requieren la llave *c*
  (llaves **encadenadas**; una llave abre varias puertas);
- la llave *c* está en una fila elegida por la semilla dentro de la columna *c*; el orden de la lista de ubicaciones
  también se mezcla con la semilla (para probar que el resultado no depende de él);
- `sala_salida` es la sala (fila 0, última columna); su única entrada es la puerta desde la fila 1 que requiere
  `llave_salida`, ubicada en la última columna. Llaves = `columnas` (las `columnas − 1` de las fronteras más
  `llave_salida`);
- variante **no resoluble**: desde la mitad de la cuadrícula, la llave *c* se ubica en la columna *c + 1* (detrás de
  su propia puerta): un ciclo y una cadena larga de dependientes, para medir el reporte.

| Tamaño | Salas | Llaves | Para qué |
|---|---|---|---|
| 10 × 10 | 100 | 10 | base |
| 10 × 100 | **1 000** | **100** | NFR-301 / SC-306 (< 200 ms) |
| 10 × 1 000 | 10 000 | 1 000 | SC-307 (×10 respecto del anterior) |

**Mediciones**:

| # | Qué mide | Tamaños | Para qué |
|---|---|---|---|
| B1 | Verificación completa (preparación + recorrido + reporte), resoluble | los tres | SC-306; crecimiento ≤ ×20 por cada ×10 (SC-307) |
| B2 | **Alternativa descartada**: repetir el recorrido completo cada vez que se obtiene una llave (misma preparación) | los tres (en 10 000, menos repeticiones) | SC-307: crece al menos el doble que B1 |
| B3 | Verificación completa, no resoluble (ciclo + dependientes) | los tres | NFR-303: el reporte no cambia el orden de crecimiento |
| B4 | Desglose a 1 000 salas: preparación (R3), recorrido (R4), ciclos y armado (R5, R6) | 1 000 | dónde se va el tiempo |

La columna `nota` informa el factor de crecimiento respecto del tamaño anterior, para leer SC-307 sin cuentas.

**La alternativa ingenua** vive solo en `BenchResolubilidad` (no en Logic: no es parte del juego) y reutiliza la
preparación de `GrafoLlaves`, así se compara solo el recorrido. Itera: recorrido completo desde `sala_inicial` con las
llaves obtenidas hasta ese momento; agrega las llaves nuevas (ordenadas como en R5); repite hasta que no haya nuevas.
Con llaves encadenadas hace K + 1 recorridos: O(K · (S + E + U)). Una prueba comprueba que da **el mismo orden** que la
verificación incremental (misma definición de oleada).

**Esperado**: B1 crece ~×10 por cada ×10; B2 ~×100. Si B1 a 1 000 salas no baja de 200 ms, se mira B4 antes de
cambiar el diseño.

**Alternativa descartada**: medir con las criptas publicadas: la mayor tiene 50 salas (el paquete actual), demasiado
chica para ver el crecimiento.

---

## R8. Dónde vive cada parte (Principio I) y cómo se inicia la partida

| Capa | Qué hace en esta feature |
|---|---|
| **Data** | Entrega y valida: `obtener_llaves` (FuenteDatos/FuenteJson/LectorPaquete), `AlmacenLlaves`, `GestorLlaves`, `validar_ubicaciones` (FR-321), `DescargadorPaquete` |
| **Logic** | Decide: `GrafoLlaves` (preparación), `RecorridoLlaves` (oleadas y fase hacia afuera), `CiclosLlaves`, `VerificadorResolubilidad` (arma el DTO). **No importa Data**: recibe `CriptaDTO`, `list[SalaDTO]` y `list[UbicacionLlaveDTO]` |
| **Service** | Orquesta: `ServicioResolubilidad.verificar(id)` y `iniciar_partida_nueva(id, nombre, forzar)`. No valida: convierte los `ErrorRed` del paso de llaves en un reporte «no concluyó» |
| **UIController / main.py** | `--verificar <cripta>` y `--forzar`; códigos 0, 3 y 1 (el 2 sigue siendo de argumentos); `--verificar` escribe el resultado en la **salida estándar** (`print` de las líneas de `TextoResolubilidad`), que es el único modo sin vista que verifica (FR-313, FR-314) |
| **View** | Muestra el reporte al iniciar, **antes de la primera acción** del jugador (FR-313); integrante 3 |

**Inicio de una partida nueva** (`ServicioResolubilidad.iniciar_partida_nueva`):

1. `datos = ServicioPartida.abrir_datos(id)` (datos generales, catálogo, esqueleto). Un error aquí, incluido el
   `ErrorDatos` de FR-323, **se propaga**: la partida no inicia, ni con `--forzar`.
2. Paso de llaves (`GestorLlaves.obtener`). Un `ErrorRed` aquí (presupuesto, 429, red, paquete sin llaves, formato o
   FR-321) **se atrapa** y da un reporte `no_concluyo` con el mensaje (FR-320, FR-321).
3. `VerificadorResolubilidad.verificar(...)`.
4. Si el veredicto no es `resoluble` y no hay `--forzar`: `ErrorPartidaNoIniciada(reporte)`. No se creó el motor,
   ni `partida.log`, ni guardado; el reloj no avanzó (FR-311).
5. Si no: `ServicioPartida.iniciar_partida(id, nombre, datos=datos)` (parámetro nuevo, para **no volver a pedir** los
   datos y el esqueleto) y `contexto.resolubilidad = reporte` (FR-312, FR-313).

**FR-301**: `ServicioReplay` sigue llamando a `ServicioPartida.iniciar_partida` y `ServicioGuardado.cargar` a
`abrir_datos`; ninguno pasa por `ServicioResolubilidad`, así que **no verifican ni se bloquean**. `--bench` tampoco:
no inicia partidas (R7). La verificación no
consume el generador aleatorio (la semilla se elige con `SystemRandom` en `ServicioPartida` y el motor se crea
después) ni descarga contenido.

**`--verificar`** (`ServicioResolubilidad.verificar`): solo datos generales, esqueleto y llaves (no crea el
resolvedor del catálogo: una solicitud menos). Cualquier `ErrorRed`, incluido FR-323 y el `ErrorDatos` de FR-321
(H2-7), da `no_concluyo` y el código 1. El resultado se escribe en la salida estándar (FR-314). El cálculo es la
misma función que al iniciar, así que el resultado es idéntico (FR-315).

**Alternativas descartadas**: (a) verificar dentro de `ServicioPartida.iniciar_partida` con una bandera: ese método lo
usa el replay, y una bandera olvidada rompería FR-301; (b) verificar en el controlador con su propia carga de datos:
pediría dos veces los datos generales y el esqueleto (gasto de presupuesto).

---

## R9. Historial de retroceso y línea de tiempo (riesgo principal del plan de trabajo)

**Decisión**: la verificación **no cambia el estado del juego**, así que **no registra nada** en el historial de
retroceso (`Logic/HistorialRetroceso.py`) ni en la línea de tiempo de la 004, ni escribe en `partida.log`.

- Ocurre **antes** de que existan el motor, el historial, la línea y la bitácora (R8, pasos 1 a 4).
- La `Mazmorra` de `GrafoLlaves` es una instancia aparte, sin motor: `cargar_esqueleto` no registra cambios (solo
  `abrir_puerta`, `mover_enemigo`, etc. lo hacen, y nunca se llaman).
- El reporte no es una acción (`AccionDTO`): no se reproduce, no se revierte con el pergamino y no aparece en
  `historia`. `--replay`, `--replay … --hasta` y `--bench` no verifican como paso previo a una partida (FR-301).
- `contexto.resolubilidad` es solo lectura para la vista; `PartidaGuardada` no lo guarda (al cargar no se verifica).

**Prueba**: después de `iniciar_partida_nueva`, el historial del motor está vacío, la línea de tiempo no tiene
acciones y el log solo tiene el encabezado; y el estado inicial es igual al de `iniciar_partida` sin verificación con
la misma semilla (H1-8).

**Alternativa descartada**: registrar la verificación como un evento en el instante 0 «para que se vea en el
replay»: cambiaría la cola de eventos, la numeración de la línea y el replay de partidas de la primera parte.

---

## R10. Pruebas (Principio X)

Todas con `unittest`, corridas por `tests/correr_pruebas.py`. Cada método de prueba **cita su FR** en el nombre o en
la primera línea del docstring (por ejemplo, `test_h2_1_llave_salida_detras_de_su_puerta` con docstring
«FR-304, FR-307, FR-308, FR-309, FR-310 — Apéndice B caso 1»). Las criptas se arman a mano con un ayudante que
entiende la notación de la spec («puerta 4–5 (B)»).

| Archivo | Qué cubre |
|---|---|
| `tests/ayudas_resolubilidad.py` | Ayudante: arma `CriptaDTO`, `list[SalaDTO]` y ubicaciones desde la notación de la spec |
| `tests/test_resolubilidad_logica.py` | H1-1 a H1-12 (veredicto, orden, caras, copias); validez del orden (SC-304); determinismo con entradas permutadas (FR-306); casos borde de la salida (FR-304, FR-322): `sala_salida` alcanzable por una salida abierta además de la puerta de salida (resoluble); la única puerta que pide `llave_salida` no lleva a `sala_salida` (no resoluble, con motivo; diferencia conocida con el motor, Sesión 2026-11-13); solo la cara de `sala_salida` hacia afuera pide `llave_salida` y la de la sala desde la que se entra pide otra llave (no cuenta); cierre automático en una puerta con llaves distintas por cara (no bloquea, FR-302) |
| `tests/test_resolubilidad_reporte.py` | H2-1 a H2-12 (no obtenibles, frontera, ubicaciones, ciclos, dependientes); SC-305 |
| `tests/test_resolubilidad_datos.py` | `UbicacionLlaveDTO`; formato en `FuenteJson`; `LectorPaquete` y `DescargadorPaquete` con `llaves.json`; `AlmacenLlaves` (versión, dañado, id inseguro); `GestorLlaves` (presupuesto, sin repetir, FR-321); H2-7, H2-8, H3-4 a H3-7 |
| `tests/test_resolubilidad_servicio.py` | `ServicioResolubilidad`: H4-1 a H4-5, H1-8, H1-9; R9 (historial, línea y log vacíos); cargar y replay no verifican (FR-301) |
| `tests/test_resolubilidad_cli.py` | `--verificar` / `--forzar` en `LectorArgumentos` (incluido el grupo excluyente: código 2); `main` con códigos 0, 3 y 1 y el resultado en la salida estándar (FR-314); sin vista (pygame no importado); `--offline` sin solicitudes; H2-7 con `--verificar` (código 1); H3-1 a H3-3, H3-8, H3-9; `--bench` no llama a `ServicioResolubilidad` (FR-301); SC-303 (10 ejecuciones en procesos separados) y SC-308 |
| `tests/test_resolubilidad_bench.py` | Generador determinista por semilla; mismos resultados entre incremental e ingenua; tamaños chicos (NFR-304). Los umbrales de tiempo (SC-306, SC-307) se leen en la tabla de `--bench`, no en pruebas, para que no fallen por la máquina |

---

## Hallazgos

- **H-1 (decidido, Sesión 2026-11-13 de la spec)**: el motor de la primera parte gana al entrar a `sala_salida` con
  `salida_abierta`, que se activa al abrir **cualquier** puerta cuya cara pide `llave_salida`, aunque no lleve a
  `sala_salida`. La verificación sigue el enunciado (FR-304, FR-322): solo cuenta una cara cerrada que lleva a
  `sala_salida` y pide `llave_salida` desde la sala desde la que se entra. Difieren en una cripta donde `sala_salida`
  se alcanza sin pasar por una puerta así: la verificación dice «no resoluble» con el motivo de FR-322, aunque el
  motor permitiría ganar. **El integrante 1 decidió mantener el motor como está** (cambiarlo sería tocar la primera
  parte sin un FR que lo pida) y **lo registra en `DECISIONES.md`** como diferencia conocida. La diferencia va hacia
  el lado seguro: la verificación puede rechazar una cripta que el motor dejaría ganar (para eso está `--forzar`),
  pero nunca aprueba una que el motor no deje ganar. Este plan no toca `Logic/motorJuego.py` ni `Logic/Mazmorra.py`
  y agrega una prueba del caso (R10).
- **H-2 (informativo, presupuesto)**: en una partida en vivo, la solicitud de llaves gasta 1 del presupuesto que el
  replay no gasta (no verifica). Solo importaría si la partida agota el presupuesto; con las llaves persistidas
  (FR-317) no se gasta nada. Lo pide FR-317; queda escrito.
- **H-3 (dependencia de datos)**: el paquete actual (`paquete/cripta-01` a `cripta-04`, 6, 20, 40 y 50 salas) es de la
  **primera parte**: versiones `fd58f7743b9e`, `8091a5cd8b7c`, `24d301ed6e9f`, `d6727c7f4950`, sin `costo`, sin
  `rango`/cazadores y **sin `llaves.json`**. Hasta regenerarlo con `DescargadorPaquete`, `--verificar … --offline`
  termina con código 1 (FR-320), que es el comportamiento correcto. Las pruebas usan paquetes temporales.
  Regenerarlo cambia archivos que usan pruebas de otros integrantes (coordinación).
- **H-4 (contrato HTTP)**: el formato de `GET /criptas/{id}/llaves` sale de §4.2; Swagger es la referencia exacta. Se
  confirma con Swagger al implementar la tarea de `FuenteJson`; si difiere, se corrige el contrato primero.
