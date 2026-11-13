# Contrato de datos de las llaves (feature 003)

> **Entrega atrasada** (era para el 9/11). Todo el código de este contrato es de Data o DTO y lo hace el
> integrante 2. Lo consume Logic (`VerificadorResolubilidad`) a través de Service. Decisiones y alternativas en
> [research.md, R1](../research.md#r1-contrato-de-datos-de-las-llaves-entrega-atrasada-del-911).

## Entrada desde el API o el paquete (§4.2)

```http
GET /criptas/{id}/llaves
```

```json
{
  "llaves": [
    { "id": "itm_llave_bronce", "sala": 4 },
    { "id": "itm_llave_negra", "sala": 12, "enemigo": "e-1203" }
  ]
}
```

- Cuenta dentro de `presupuesto_solicitudes`, como toda solicitud (§4.3, FR-317). Un reintento por 429 también.
- Con `enemigo`, la llave está en el campo `suelta` de esa instancia y `sala` es donde el enemigo inicia (FR-303).
- Una misma llave puede aparecer varias veces (copias válidas, FR-316). Una lista vacía es válida.
- En el paquete offline es el archivo `paquete/<id>/llaves.json`, con la respuesta tal cual (FR-318).
- El formato exacto se confirma con Swagger (hallazgo H-4).

## DTO

`DTO/UbicacionLlaveDTO.py` (nuevo, integrante 2):

| Campo | Tipo | Ausente o `null` en el JSON | Requisito |
|---|---|---|---|
| `id` | `str` | obligatorio | FR-316 |
| `sala` | `int` | obligatorio | FR-316, FR-321 |
| `enemigo` | `str \| None` | `None` | FR-303, FR-316 |

- `@dataclass(frozen=True)`; solo transporta datos.
- `desde_diccionario(d)` lee un elemento de `llaves`; `a_diccionario()` produce **el mismo formato del API** y omite
  `enemigo` si es `None`.
- La lista se entrega como `list[UbicacionLlaveDTO]` **en el orden de la respuesta**. Data no ordena ni deduplica: el
  orden del reporte lo fija Logic (research R5).

## Métodos

| Dónde | Firma | Qué hace |
|---|---|---|
| `Data/FuenteDatos.py` | `obtener_llaves(self, id_cripta: str) -> list[UbicacionLlaveDTO]` | **No abstracto.** Por defecto lanza `ErrorRed(f"ubicación de llaves de {id_cripta}", "esta fuente no entrega la ubicación de las llaves")`, así las fuentes falsas que ya existen (`BenchDatos`, `tests/Utilidades.py`) no se rompen |
| `Data/FuenteJson.py` | `obtener_llaves(id_cripta)` | `get_json(f"criptas/{id}/llaves", op)` y traduce con `ubicaciones_desde_diccionario` dentro de `_traducir` |
| `Data/FuenteJson.py` | `@staticmethod ubicaciones_desde_diccionario(d: dict) -> list[UbicacionLlaveDTO]` | Pública: la usa también `AlmacenLlaves`. Valida el formato (tabla de abajo) |
| `Data/FuenteOffline.py` (`LectorPaquete.get_json`) | ruta `criptas/{id}/llaves` | Lee `<carpeta>/<id>/llaves.json`. Si falta, el `ErrorRed` «falta el archivo … en el paquete offline» que ya existe |
| `Data/DescargadorPaquete.py` | dentro de `descargar(id)` | Pide `criptas/{id}/llaves` después de las páginas del esqueleto y escribe `<id>/llaves.json` junto con lo demás, al final |
| `Data/AlmacenLlaves.py` (nuevo) | `leer(id_cripta, version) -> list[UbicacionLlaveDTO] \| None`; `guardar(id_cripta, version, ubicaciones) -> None` | Persistencia por versión (abajo) |
| `Data/GestorLlaves.py` (nuevo) | `__init__(fuente: FuenteDatos, almacen: AlmacenLlaves \| None)`; `obtener(cripta: CriptaDTO, esqueleto: GestorEsqueleto) -> list[UbicacionLlaveDTO]` | 1) almacén vigente; 2) si no, `fuente.obtener_llaves` y `almacen.guardar`; 3) `validar_ubicaciones` |
| `Data/ValidacionDatos.py` | `validar_ubicaciones(operacion: str, ubicaciones: list[UbicacionLlaveDTO], existe_sala: Callable[[int], bool]) -> None` | FR-321: lanza `ErrorDatos` con la primera ubicación cuya sala no existe |

## Validación de formato (Data, `FuenteJson`)

| Dato | Inválido si | Resultado |
|---|---|---|
| raíz | no tiene `llaves` o no es una lista | `ErrorRed` de formato (operación «ubicación de llaves de `<id>`») |
| `id` | falta, no es texto o es vacío | ídem |
| `sala` | falta o no es entero de verdad (`es_entero`: un `bool` no cuenta) | ídem |
| `enemigo` | está presente, no es `null` y no es texto no vacío | ídem |

Un error de formato hace que la verificación **no concluya** (efecto de FR-320). No es `ErrorDatos`: se sigue la
convención de la Parte 1 (formato → `ErrorRed` con contexto).

## Validación de coherencia con el esqueleto (Data, FR-321)

| Caso | Tratamiento |
|---|---|
| `sala` no existe en el esqueleto | `ErrorDatos("ubicación de llaves de <id>", "la llave <llave> está en la sala <sala>, que no existe en el esqueleto")` (con «(enemigo <e>)» si lo trae). La verificación no concluye; la partida no inicia salvo con `--forzar`; `--verificar` termina con código 1 (H2-7) |
| `enemigo` no existe en el contenido de la sala | **No se valida** (habría que descargar contenido, FR-301) |
| una puerta requiere una llave que no está en la lista | **No es error**: lo resuelve Logic como llave no obtenible «sin ubicación» |

`existe_sala` es `GestorEsqueleto.existe_sala` (O(1)). Se pasa la función y no el gestor porque `GestorEsqueleto` ya
importa `ValidacionDatos`. Los errores de costo de FR-323 los sigue lanzando `GestorEsqueleto.cargar` (T002 de la
001) antes de llegar aquí.

## Persistencia por versión (FR-317, FR-319)

```text
cache/llaves/<id_cripta>.json
{ "id": "cripta-01", "version": "<versión de la cripta>", "llaves": [ ...mismo formato del API... ] }
```

- `leer(id, version)`: devuelve las ubicaciones solo si el archivo existe, se puede leer, su `id` coincide y
  `validar_version(guardada, version)` (Security) es verdadero. Si el archivo está dañado, se borra y se devuelve
  `None`. Otra versión ⇒ `None` (se volverá a pedir y la escritura lo reemplaza): **nadie borra archivos a mano**.
- `guardar(id, version, ubicaciones)`: escribe en `.tmp` y reemplaza con `os.replace`.
- Ids que no pasan `es_nombre_seguro` no se leen ni se escriben (simplemente se piden).
- La versión es `CriptaDTO.version`, que ya llegó con los datos generales: **no se pide `/version` aparte**.
- Se persiste **antes** de validar FR-321 (la respuesta es la del API para esa versión; repetir la solicitud no la
  cambia).
- **Con `--offline` el almacén no se usa** (`GestorLlaves(fuente, None)`): las llaves salen solo del paquete
  (FR-318, H3-7). Lo decide `ServicioResolubilidad`, donde ya se mira `config.offline`.
- `cache/` ya está en `.gitignore`.

## Errores y efecto

| Situación | Excepción (Data) | Efecto en Service |
|---|---|---|
| Presupuesto agotado | `PresupuestoAgotadoError` (`ErrorRed`) | reporte `no_concluyo` (FR-320) |
| HTTP 429 repetido, error de red | `ErrorRed` | ídem |
| Paquete sin `llaves.json` | `ErrorRed` | ídem |
| Formato inválido | `ErrorRed` | ídem |
| Sala inexistente (FR-321) | `ErrorDatos` | ídem; con `--verificar`, código 1 (H2-7, FR-314) |
| Costo inválido en el esqueleto (FR-323) | `ErrorDatos` desde `GestorEsqueleto.cargar` | **se propaga**: la partida no inicia ni con `--forzar`; `--verificar` → `no_concluyo`, código 1 |

## Paquete offline (FR-318)

```text
paquete/
└── <id_cripta>/
    ├── general.json
    ├── salas_p<N>.json
    ├── contenido.json
    └── llaves.json        NUEVO: GET /criptas/<id>/llaves, tal cual
```

Costos (`costo` en `salas_p<N>.json`) y cazadores (`rango` en `catalogo.json`) **no necesitan código nuevo**: el
descargador ya guarda las respuestas tal cual. El paquete actual es de la primera parte y hay que **regenerarlo**
cuando el API publique las versiones nuevas (research, hallazgo H-3).

## Compatibilidad

- `FuenteDatos` gana un método con implementación por defecto: nada que ya exista se rompe.
- `UbicacionLlaveDTO` es nuevo; ningún DTO existente cambia.
- Un paquete de la primera parte se sigue leyendo igual; solo `--verificar --offline` informa que falta `llaves.json`.
