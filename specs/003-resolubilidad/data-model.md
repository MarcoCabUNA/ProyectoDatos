# Modelo de datos (fase 1): Verificación de resolubilidad

**Feature**: `003-resolubilidad` · **Plan**: [plan.md](plan.md) · **Research**: [research.md](research.md)

Notación: S salas, E caras de salidas, U ubicaciones, K llaves distintas, M menciones de llaves.
Ningún arreglo de este modelo es un `dict` ni un `set`; las listas se usan como almacenamiento contiguo indexado por
entero (Principio II).

## 1. DTO (transversal)

Detalle de campos y formato: [contrato-llaves.md](contracts/contrato-llaves.md) y
[contrato-reporte-resolubilidad.md](contracts/contrato-reporte-resolubilidad.md).

| DTO | Archivo | Campos | Reglas |
|---|---|---|---|
| `UbicacionLlaveDTO` | `DTO/UbicacionLlaveDTO.py` (nuevo) | `id: str`, `sala: int`, `enemigo: str \| None = None` | Inmutable. Formato del API en `desde_diccionario`/`a_diccionario` |
| `PuertaLlaveDTO` | `DTO/ReporteResolubilidadDTO.py` (nuevo) | `sala_origen`, `direccion`, `sala_destino`, `llave: str \| None` | `llave = None` ⇒ «sin llave» |
| `LlaveNoObtenibleDTO` | ídem | `id`, `ubicaciones: list[UbicacionLlaveDTO]` | Lista vacía ⇒ «sin ubicación» |
| `PasoCicloDTO` | ídem | `llave`, `ubicacion`, `puerta` | `puerta.llave` = llave del paso siguiente |
| `DependienteCicloDTO` | ídem | `llave`, `ubicacion`, `puerta`, `depende_de` | `depende_de` es una llave del ciclo |
| `CicloLlavesDTO` | ídem | `pasos`, `dependientes` | Empieza por la llave de menor id |
| `ReporteResolubilidadDTO` | ídem | `id_cripta`, `veredicto`, `version_cripta`, `llave_salida`, `orden_llaves`, `llaves_no_obtenibles`, `frontera`, `ciclos`, `motivo`, `mensaje` | Campos nuevos al final, con valor por defecto |
| `ConfiguracionDTO` | `DTO/ConfiguracionDTO.py` (modificado) | + `verificar: str \| None = None`, + `forzar: bool = False` | Detrás de `hasta`, el último campo de la 004 (`checkpoint_cada` y `hasta` ya están, commit `1b53bc9`) |

### Estados del veredicto

```text
                 ┌─ error al leer datos generales / esqueleto (FR-323, cripta inexistente) ─┐
 verificar(id) ──┤                                                                          ├─► NO_CONCLUYO (mensaje)
                 ├─ error en el paso de llaves (FR-320, FR-321, formato) ───────────────────┘
                 └─ datos completos ─► recorrido ─┬─► RESOLUBLE   (orden_llaves)
                                                  └─► NO_RESOLUBLE (no obtenibles, frontera, ciclos, motivo?)
```

Al **iniciar una partida**, el primer error (datos generales o esqueleto) no produce reporte: se propaga y la
partida no inicia, ni con `--forzar` (FR-323). El resto es igual.

| Veredicto | Sin `--forzar` | Con `--forzar` | Código con `--verificar` |
|---|---|---|---|
| `RESOLUBLE` | inicia; muestra el orden | igual | 0 |
| `NO_RESOLUBLE` | **no inicia**; muestra el reporte (FR-311) | inicia; reporte como advertencia (FR-312) | 3 |
| `NO_CONCLUYO` (llaves) | **no inicia**; muestra el mensaje (FR-320) | inicia; mensaje como advertencia | 1 |
| error del esqueleto (FR-323) | no inicia | **no inicia** | 1 |
| cripta inexistente (404, o ausente del paquete con `--offline`) | no inicia | **no inicia** (sin esqueleto no hay partida) | 1 (FR-314) |

`--forzar` solo se lee en `iniciar_partida_nueva`. Con `--replay`, con `--bench` o al cargar una partida no tiene
efecto (esos caminos no verifican, FR-301, FR-312), y con `--verificar` tampoco (H3-9).

## 2. Data

### `AlmacenLlaves` (`Data/AlmacenLlaves.py`, nuevo)

| Atributo | Tipo | Contenido |
|---|---|---|
| `_carpeta` | `str` | `cache/llaves` por defecto |

Archivo por cripta: `cache/llaves/<id_cripta>.json` = `{"id", "version", "llaves": [...]}`.
Transiciones: *ausente* → `guardar` → *vigente*; *vigente* → cambia la versión de la cripta → *vencido* (leer
devuelve `None`) → `guardar` → *vigente*; *dañado* → `leer` lo borra → *ausente*.

### `GestorLlaves` (`Data/GestorLlaves.py`, nuevo)

| Atributo | Tipo | Contenido |
|---|---|---|
| `_fuente` | `FuenteDatos` | La de la ejecución (red u offline) |
| `_almacen` | `AlmacenLlaves \| None` | `None` con `--offline`. Lo decide `ServicioPartida.fuente()` en el mismo `if` que elige la fuente, y llega por `ServicioPartida.almacen_llaves()`; ni `GestorLlaves` ni `ServicioResolubilidad` miran `config.offline` |

`obtener(cripta, esqueleto)`: almacén vigente → si no, una solicitud y `guardar` → `validar_ubicaciones`.

### Validación (`Data/ValidacionDatos.py`, función nueva)

`validar_ubicaciones(operacion, ubicaciones, existe_sala)`: O(U); lanza `ErrorDatos` en la primera ubicación con sala
inexistente (FR-321).

## 3. Logic

### `GrafoLlaves` (`Logic/GrafoLlaves.py`, nuevo): la preparación

Se arma una vez por verificación, a partir de `CriptaDTO`, `list[SalaDTO]` y `list[UbicacionLlaveDTO]`. Usa una
`Mazmorra` aparte para combinar las caras como en la primera parte y se descarta.

| Atributo | Tipo | Índice | Contenido |
|---|---|---|---|
| `cantidad_salas` | `int` | — | id máximo + 1 (las posiciones sin sala quedan vacías) |
| `existe[s]` | `list[bool]` | sala | hay una sala con ese id |
| `tipo_cara[c]` | `list[int]` | `c = sala*4 + dir` | 0 sin salida · 1 abierta · 2 cerrada con llave · 3 cerrada sin llave |
| `destino[c]` | `list[int]` | cara | sala destino, o −1 |
| `llave_cara[c]` | `list[int]` | cara | índice de llave, o −1 |
| `ids[k]` | `list[str]` | llave | id de la llave; **ordenado** (índice menor = id menor) |
| `ubicaciones` | `list[UbicacionLlaveDTO]` | posición | ordenadas por (llave, sala, enemigo), sin duplicados idénticos (FR-309): después de ordenar, una pasada O(U) descarta cada ubicación igual a la anterior (misma llave, sala y enemigo, o las dos sin enemigo) |
| `llave_ubicacion[i]` | `list[int]` | ubicación | índice de llave |
| `inicio_ubic[k]`, `fin_ubic[k]` | `list[int]` | llave | tramo de `ubicaciones` de la llave `k` (vacío ⇒ «sin ubicación») |
| `llaves_en_sala[s]` | `list[list[int]]` | sala | índices de llave ubicados en `s` |
| `llave_salida` | `int` | — | índice de `llave_salida` (siempre existe: se menciona siempre) |
| `sala_inicial`, `sala_salida` | `int` | — | de `CriptaDTO` |
| `es_cara_de_salida[c]` | `list[bool]` | cara | `c` lleva a `sala_salida`, está cerrada y su propia llave (ya combinada) es `llave_salida`: la cara de la sala desde la que se entra (FR-304) |
| `hay_puerta_de_salida` | `bool` | — | algún `es_cara_de_salida[c]` en todo el esqueleto; falso ⇒ motivo de FR-322 |

Las caras se leen ya combinadas por la `Mazmorra` auxiliar: una cara sin llave toma la llave y el estado cerrado de
su inversa si esta declara llave; si no, cada cara se rige por su llave y su estado cerrado (FR-302). **El cierre
automático no se lee**: no es por cara (se programa el de la cara desde la que se abre y cierra las dos) y, por el
supuesto de §3.5, nunca bloquea. El costo tampoco se lee.

Construcción del índice de llaves (research R3): menciones `(id, tipo, posición)` → `Ordenador.ordenar` → una
pasada que asigna índices consecutivos y los escribe en `llave_cara` y `llave_ubicacion`. O(M log M).

Ubicaciones sin repetir (research R5, FR-309): se ordenan por (índice de llave, sala, enemigo) con el `Ordenador`,
O(U log U), y una pasada O(U) copia cada una solo si es distinta de la anterior; las idénticas quedan juntas por el
orden. No cambia la obtenibilidad (una copia repetida está en la misma sala) y así el reporte y los pasos de los
ciclos las indican una sola vez. Data no deduplica: entrega la lista tal como llega (contrato de llaves).

### `RecorridoLlaves` (`Logic/RecorridoLlaves.py`, nuevo): oleadas y fase hacia afuera

| Atributo | Tipo | Índice | Contenido |
|---|---|---|---|
| `alcanzable[s]` | `list[bool]` | sala | en la región alcanzable |
| `estado_llave[k]` | `list[int]` | llave | 0 sin ver · 1 vista en la oleada actual · 2 obtenida |
| `oleada_llave[k]` | `list[int]` | llave | oleada en que se obtuvo, o −1 |
| `orden` | `list[int]` | — | índices de llave en orden de obtención (oleada, id) |
| `esperando[k]` | `list[list[int]]` | llave | caras cerradas con la llave `k` que salen de una sala alcanzable; se vacía al obtener `k` |
| `sin_llave` | `list[int]` | — | caras cerradas sin llave que salen de una sala alcanzable |
| `caras_de_salida` | `list[int]` | — | caras con `es_cara_de_salida[c]` que salen de una sala alcanzable |
| `frontera` | `list[int]` | — | caras de la frontera, ordenadas por `c` |
| `puerta_que_encierra[s]` | `list[int]` | sala | la puerta que bloquea la zona de `s` según FR-310 (menor nivel; desempate por sala de origen y dirección): la primera por la que se llegó a esa zona en la fase hacia afuera, o −1 |
| `nivel[s]` | `list[int]` | sala | puertas cruzadas desde la región (0 dentro de la región, −1 si no se llega) |

Ciclo de vida de una llave `k`:

```text
sin ver (0) ──sala con k se visita──► vista en la oleada (1) ──fin de oleada──► obtenida (2)
                                                                   │
                                          reabre esperando[k] ◄────┘ (solo esas caras)
```

Ciclo de vida de una cara `c` que sale de una sala alcanzable `u`:

```text
abierta, o con llave obtenida ─► destino alcanzable
con llave k no obtenida ─► esperando[k] ─┬─► k se obtiene ─► destino alcanzable
                                         └─► k nunca se obtiene y destino afuera ─► frontera
cerrada sin llave ─► sin_llave ─► destino afuera ─► frontera («sin llave»)
```

Complejidad: tiempo O(S + E + U + K log K); espacio O(S + E + U + K).

### `CiclosLlaves` (`Logic/CiclosLlaves.py`, nuevo)

| Atributo | Tipo | Índice | Contenido |
|---|---|---|---|
| `siguiente[k]` | `list[int]` | llave | llave de la puerta que encierra a `k`, o −1 (sin arista) |
| `ubic_usada[k]` | `list[int]` | llave | posición en `ubicaciones` de la ubicación usada, o −1 |
| `marca[k]` | `list[int]` | llave | número del recorrido que la visitó, o 0 |
| `pos_camino[k]` | `list[int]` | llave | posición de `k` en `camino` durante su recorrido (para saber dónde empieza un ciclo) |
| `camino` | `list[int]` | — | llaves del recorrido actual, en el orden en que se siguieron las aristas; se vacía al empezar cada recorrido |
| `ciclo_de[k]` | `list[int]` | llave | número de ciclo al que pertenece o del que depende, o −1 |
| `entrada[k]` | `list[int]` | llave | llave del ciclo donde entra su cadena (ella misma si está en el ciclo), o −1 |

**Sin recursión** (research R6): seguir las aristas es un `while` que agrega cada llave a `camino`; al terminar el
recorrido, un `for` sobre `camino` asigna `entrada` y `ciclo_de` (ciclo nuevo desde `pos_camino[k]`, la `entrada`
de una llave de un recorrido anterior, o −1). Una cadena de 1 000 o más llaves no llega al límite de recursión de
Python.

Complejidad: O(K) (cada llave entra una vez a `camino` y se recorre una vez al asignar) + O(K log K) para ordenar
dependientes.

### `VerificadorResolubilidad` (`Logic/VerificadorResolubilidad.py`, nuevo)

`verificar(cripta: CriptaDTO, salas: list[SalaDTO], ubicaciones: list[UbicacionLlaveDTO]) -> ReporteResolubilidadDTO`.
Arma `GrafoLlaves`, corre `RecorridoLlaves`, decide el veredicto (FR-304, FR-322), y si no es resoluble corre la fase
hacia afuera y `CiclosLlaves`; traduce índices a DTOs. Sin estado entre llamadas. No importa Data ni Service.

Regla del veredicto:

| Condición | Veredicto |
|---|---|
| `hay_puerta_de_salida` es falso | `NO_RESOLUBLE` con `motivo` (FR-322), aunque `llave_salida` sea obtenible o `sala_salida` se alcance por otro camino |
| `llave_salida` obtenida **y** `caras_de_salida` no vacía | `RESOLUBLE`: se llegó a `sala_salida` por una cara que pide `llave_salida` (FR-304) |
| cualquier otro caso | `NO_RESOLUBLE`, sin `motivo` |

No se mira `alcanzable[sala_salida]`: llegar por una salida abierta o por una cara que pide otra llave no cuenta. La
diferencia con el motor de la primera parte (que gana con cualquier puerta que pida `llave_salida`) es conocida y la
registra el integrante 1 en `DECISIONES.md` (research, H-1).

Reglas de negocio que viven aquí (y no en Data ni en Service): combinación de caras (vía `Mazmorra`), supuestos de
FR-302 y FR-303, FR-304, FR-305, FR-307 a FR-310, FR-316 (copias), FR-321 «sin ubicación», FR-322.

## 4. Service

| Clase | Archivo | Atributos | Operaciones |
|---|---|---|---|
| `ServicioResolubilidad` | `Service/ServicioResolubilidad.py` (nuevo) | `_partida: ServicioPartida` | `verificar(id) -> ReporteResolubilidadDTO`; `iniciar_partida_nueva(id, nombre, forzar, semilla=None) -> ContextoPartida`. Arma `GestorLlaves(partida.fuente(), partida.almacen_llaves())`: **no mira `config.offline`** |
| `ErrorPartidaNoIniciada` | ídem (se define aquí, como `ErrorCarga` en `ServicioGuardado.py` y `ErrorReplay` en `ServicioReplay.py`) | `reporte: ReporteResolubilidadDTO` | Subclase de `ValueError`; mensaje corto para el jugador. `Service/ErroresServicio.py` solo lo importa y lo agrega a `ERRORES_ESPERADOS` (sin import circular: `ServicioResolubilidad` no importa `ErroresServicio`) |
| `ServicioPartida` | `Service/ServicioPartida.py` (modificado, integrante 3) | + `_almacen_llaves: AlmacenLlaves \| None` (parámetro final `almacen_llaves=None` del constructor) | `fuente()`: el mismo `if` elige `FuenteOffline()` sin almacén o `FuenteRed()` con `AlmacenLlaves()`; nuevo `almacen_llaves() -> AlmacenLlaves \| None` (llama antes a `fuente()`); `iniciar_partida(..., datos=None)` |
| `ContextoPartida` | `Service/ContextoPartida.py` (modificado) | + `resolubilidad: ReporteResolubilidadDTO \| None = None`, al final | — |

## 5. Lo que la verificación NO toca (research R9)

| Pieza | Por qué no cambia |
|---|---|
| Motor, reloj, cola de eventos | No existen todavía cuando se verifica |
| Generador aleatorio | La semilla se elige aparte (`SystemRandom`) y el motor se crea después |
| `HistorialRetroceso` | No hay motor; la `Mazmorra` auxiliar no registra cambios |
| Línea de tiempo (004) | Se crea en `iniciar_partida`, después; la verificación no es una acción |
| `partida.log` | Se crea después, solo si la partida inicia |
| Contenido de salas | No se descarga (FR-301) |
| `--replay`, `--replay … --hasta`, `--bench` | No verifican como paso previo a una partida (FR-301); `--bench` solo llama a Logic con criptas sintéticas |
| `Logic/motorJuego.py` (victoria con `salida_abierta`) | Se mantiene como está (decisión del integrante 1; research, H-1) |
| `PartidaGuardada` | No guarda el reporte; cargar no verifica |
