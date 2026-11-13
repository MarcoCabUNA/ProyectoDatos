# Contrato del reporte de resolubilidad (feature 003 → integrante 3)

> **Para el integrante 3, entrega del 13/11.** El DTO lo crea el integrante 2 en `DTO/ReporteResolubilidadDTO.py`.
> Lo arma Logic (`VerificadorResolubilidad`) o, si la verificación no concluyó, Service. La interfaz **no calcula
> nada**: todas las listas llegan completas y ya ordenadas (research R5). Solo transporta datos.
> **Regla de cambios**: un campo nuevo va **al final** de su clase y **con valor por defecto**.

## Clases

Todas son `@dataclass(frozen=True)` en `DTO/ReporteResolubilidadDTO.py`, salvo `UbicacionLlaveDTO`, que es la de
[contrato-llaves.md](contrato-llaves.md).

```python
RESOLUBLE = "resoluble"
NO_RESOLUBLE = "no_resoluble"
NO_CONCLUYO = "no_concluyo"
```

### `PuertaLlaveDTO`: una cara cerrada, vista desde la sala de la que sale

| Campo | Tipo | Significado |
|---|---|---|
| `sala_origen` | `int` | Sala desde la que se intenta pasar (en la frontera: la sala alcanzable) |
| `direccion` | `int` | Índice en `DTO/Direcciones.DIRECCIONES` (0 N, 1 S, 2 E, 3 O) |
| `sala_destino` | `int` | Sala del otro lado |
| `llave` | `str \| None` | Llave que pide **esa cara**. `None` ⇒ mostrar «sin llave: no se puede abrir» (FR-308) |

### `LlaveNoObtenibleDTO`

| Campo | Tipo | Significado |
|---|---|---|
| `id` | `str` | Id de la llave |
| `ubicaciones` | `list[UbicacionLlaveDTO]` | Todas, en orden (sala; sin enemigo primero; id de enemigo). **Vacía ⇒ mostrar «sin ubicación»** (FR-309, FR-321) |

### `PasoCicloDTO`: «llave está en sala → la puerta X requiere la siguiente»

| Campo | Tipo | Significado |
|---|---|---|
| `llave` | `str` | Llave de este paso |
| `ubicacion` | `UbicacionLlaveDTO` | La ubicación usada (la de menor nivel de puertas; research R6) |
| `puerta` | `PuertaLlaveDTO` | Puerta que la encierra; `puerta.llave` es la llave del paso siguiente (la del último paso es la del primero) |

### `DependienteCicloDTO`

| Campo | Tipo | Significado |
|---|---|---|
| `llave` | `str` | Llave no obtenible que no está en el ciclo |
| `ubicacion` | `UbicacionLlaveDTO` | Ubicación usada |
| `puerta` | `PuertaLlaveDTO` | Puerta que la encierra |
| `depende_de` | `str` | Llave **del ciclo** de la que depende (donde entra su cadena) |

### `CicloLlavesDTO`

| Campo | Tipo | Significado |
|---|---|---|
| `pasos` | `list[PasoCicloDTO]` | Empieza por la llave de menor id del ciclo; una llave sola es un ciclo de un paso (H2-1) |
| `dependientes` | `list[DependienteCicloDTO]` | Por id. Se muestran **inmediatamente después** del ciclo (FR-310) |

### `ReporteResolubilidadDTO`

| # | Campo | Tipo | Valor por defecto | Cuándo tiene datos |
|---|---|---|---|---|
| 1 | `id_cripta` | `str` | (obligatorio) | siempre |
| 2 | `veredicto` | `str` | (obligatorio) | siempre: `RESOLUBLE`, `NO_RESOLUBLE` o `NO_CONCLUYO` |
| 3 | `version_cripta` | `str \| None` | `None` | si se llegaron a leer los datos generales |
| 4 | `llave_salida` | `str \| None` | `None` | ídem |
| 5 | `orden_llaves` | `list[str]` | `[]` | `RESOLUBLE`: todas las llaves obtenibles, en el orden de FR-305 |
| 6 | `llaves_no_obtenibles` | `list[LlaveNoObtenibleDTO]` | `[]` | `NO_RESOLUBLE`, por id (FR-307, FR-309) |
| 7 | `frontera` | `list[PuertaLlaveDTO]` | `[]` | `NO_RESOLUBLE`, por (sala alcanzable, dirección) (FR-308) |
| 8 | `ciclos` | `list[CicloLlavesDTO]` | `[]` | `NO_RESOLUBLE`, por id de la llave inicial (FR-310) |
| 9 | `motivo` | `str \| None` | `None` | `NO_RESOLUBLE` por FR-322: texto explícito, listo para mostrar |
| 10 | `mensaje` | `str \| None` | `None` | `NO_CONCLUYO`: el error con contexto (qué llave, qué sala, qué salida, qué solicitud…) |

Las listas usan `field(default_factory=list)`. Con `RESOLUBLE`, los campos 6 a 10 quedan vacíos. Con `NO_CONCLUYO` no
hay veredicto: los campos 5 a 9 quedan vacíos (FR-323: «no debe mostrarse ningún veredicto»).

Texto de `motivo` (lo arma Logic, así consola y ventana dicen lo mismo, FR-315):
«Ninguna puerta cerrada por la que se entra a la sala de salida `<sala_salida>` pide `<llave_salida>` desde la sala
de la que se entra (las puertas que piden `<llave_salida>` pero no llevan a la sala `<sala_salida>` no cuentan): la
victoria es imposible (§3.5, P1 §2.12).»

Cuándo aparece (FR-304, FR-322): ninguna cara del esqueleto, ya combinada según FR-302, cumple a la vez que lleva
a `sala_salida`, que está cerrada y que **su propia** llave es `llave_salida`. Aparece aunque `llave_salida` sea
obtenible y aunque `sala_salida` se alcance por otro camino. En ese caso el motor de la primera parte podría dejar
ganar abriendo otra puerta que pide `llave_salida`: es la diferencia conocida que el integrante 1 registra en
`DECISIONES.md` (Sesión 2026-11-13 de la spec). La interfaz muestra el texto tal cual; no tiene que explicar la
diferencia.

## Ejemplo (escenario H2-2)

```python
ReporteResolubilidadDTO(
    id_cripta="prueba", veredicto=NO_RESOLUBLE, version_cripta="v1", llave_salida="S",
    llaves_no_obtenibles=[
        LlaveNoObtenibleDTO("A", [UbicacionLlaveDTO("A", 6)]),
        LlaveNoObtenibleDTO("B", [UbicacionLlaveDTO("B", 7)]),
        LlaveNoObtenibleDTO("S", [UbicacionLlaveDTO("S", 8)]),
    ],
    frontera=[PuertaLlaveDTO(2, <dir>, 6, "B"), PuertaLlaveDTO(3, <dir>, 7, "A"), PuertaLlaveDTO(5, <dir>, 8, "A")],
    ciclos=[CicloLlavesDTO(
        pasos=[PasoCicloDTO("A", UbicacionLlaveDTO("A", 6), PuertaLlaveDTO(2, <dir>, 6, "B")),
               PasoCicloDTO("B", UbicacionLlaveDTO("B", 7), PuertaLlaveDTO(3, <dir>, 7, "A"))],
        dependientes=[DependienteCicloDTO("S", UbicacionLlaveDTO("S", 8), PuertaLlaveDTO(5, <dir>, 8, "A"), "A")])],
)
```

## Cómo llega a la interfaz

| Momento | Quién lo entrega | Qué recibe la interfaz |
|---|---|---|
| `--verificar <cripta>` | `ControladorBackend.verificar(id)` → `ServicioResolubilidad.verificar(id)` | El DTO; `main.py` escribe sus líneas (`UIController/TextoResolubilidad.py`) en la **salida estándar** (FR-314). Es el único modo sin vista que verifica (FR-313) |
| Iniciar partida, resoluble o con `--forzar` | `ControladorBackend.iniciar(...)` guarda `contexto.resolubilidad` | `ControladorBackend.resolubilidad()` devuelve el DTO; la vista lo muestra **antes de la primera acción** (FR-313). Con `--forzar` y no resoluble, como advertencia (FR-312) |
| Iniciar partida, no resoluble o no concluyó, sin `--forzar` | `ServicioResolubilidad` lanza `ErrorPartidaNoIniciada` (con `.reporte`) | `iniciar` lanza `ErrorOperacion` con un mensaje corto y `resolubilidad()` devuelve el reporte para mostrarlo completo (FR-311) |
| Cargar partida, `--replay`, `--replay … --hasta` | — | Nada: no se verifica (FR-301). `resolubilidad()` devuelve `None` |
| `--bench` | — | Nada: no inicia partidas ni verifica como paso previo (FR-301); solo mide la verificación sobre criptas sintéticas (NFR-304) |

Mostrar el reporte completo al iniciar es la excepción de 002 FR-217: no forma parte del mapa conocido ni lo
modifica (FR-313).

## Texto de consola (`UIController/TextoResolubilidad.py`, integrante 2)

`lineas_reporte(reporte: ReporteResolubilidadDTO) -> list[str]`. La vista puede reutilizarlo para que el texto sea
idéntico (FR-315). Formato:

```text
Cripta cripta-01 (versión fd58f7743b9e): RESOLUBLE
Orden de obtención de llaves: itm_llave_bronce, itm_llave_negra
```

```text
Cripta prueba (versión v1): NO RESOLUBLE
Motivo: …                                    (solo con FR-322)
Llaves no obtenibles:
  - A: sala 6
  - B: sala 7
  - C: sin ubicación
  - S: sala 8; sala 12 (enemigo e-1203)
Frontera bloqueada:
  - puerta 2–6 (desde la sala 2, salida E): requiere B
  - puerta 3–7 (desde la sala 3, salida N): sin llave: no se puede abrir
Ciclos:
  1. A está en la sala 6 → la puerta 2–6 requiere B → B está en la sala 7 → la puerta 3–7 requiere A
     - S (sala 8, puerta 5–8 requiere A) depende de A
```

```text
Cripta cripta-01: la verificación NO CONCLUYÓ
Falló 'ubicación de llaves de cripta-01': se alcanzó el presupuesto de 9 solicitudes
```

## Línea de comandos (FR-314)

| Comando | Resultado | Código |
|---|---|---|
| `python main.py --verificar <cripta>` | Reporte en la salida estándar, sin vista y sin partida | 0 resoluble · 3 no resoluble · 1 no concluyó (incluidos FR-320, FR-321 y FR-323) |
| `… --verificar <cripta> --offline` | Igual, leyendo el paquete; ninguna solicitud de red | ídem |
| `… --verificar <cripta> --forzar` | Igual que sin `--forzar` (H3-9) | ídem |
| `… --verificar` sin valor o con texto vacío | Error de uso | 2 |
| `… --verificar X --replay L` o `--verificar X --bench` | Error de uso (grupo excluyente) | 2 |
| `… --forzar` (partida normal) | Inicia aunque no sea resoluble o no concluya; muestra el reporte como advertencia | — |
| `… --forzar` con un error de FR-323 | No inicia; la interfaz muestra el error con contexto | — |
| `… --replay L` o `… --bench` | No verifican (FR-301) | sin cambios |

`ConfiguracionDTO` gana `verificar: str | None = None` y `forzar: bool = False`, **después** de `hasta` y
`checkpoint_cada` de la 004. `--verificar` va en el mismo grupo excluyente que `--replay` y `--bench`. `--forzar`
con `--replay` o `--bench` se acepta y no tiene efecto (no inician una partida nueva).
