# Contrato: Línea de tiempo

**Feature**: `004-linea-tiempo` · **Plan**: [../plan.md](../plan.md) · **Modelo**: [../data-model.md](../data-model.md)

Cuatro contratos: el DTO que se guarda y el bloque binario (los dos son para Derek, integrante 2), el
método nuevo del motor (para Marco) y los comandos y banderas (integrante 3). Aquí van nombres de campos; el código llega en
`tasks.md`.

## 1. DTO guardado (Derek)

`PartidaGuardadaDTO` recibe **un campo nuevo al final**, con valor por defecto:

| Campo | Tipo | Valor por defecto |
|---|---|---|
| `linea` | `LineaTiempoGuardadaDTO \| None` | `None` |

Los DTO existentes no cambian de orden. `a_diccionario` / `desde_diccionario` se extienden con el
mismo campo (para comparar JSON contra binario, §4.10).

`LineaTiempoGuardadaDTO` (nuevo, `frozen`, solo datos):

| Campo | Tipo | Notas |
|---|---|---|
| `k` | `int` | ≥ 1 |
| `acciones` | `list[AccionGuardadaDTO]` | `tiempo: int`, `tipo: str`, `direccion: int \| None`, `objetivo: str \| None`, `objeto: str \| None` |
| `puntos` | `list[PuntoControlGuardadoDTO]` | `acciones_completadas: int`, `partida: PartidaGuardadaDTO` (con `linea=None`), `salas: list[SalaGuardadaDTO]`. Incluye el punto que se toma tras usar un pergamino: tiene el mismo formato que los demás |
| `cargas` | `list[RegistroCargaGuardadoDTO]` | `ordinal: int`, `sala: SalaDTO` (el contenido inicial) |
| `fichas` | `list` de fichas | enemigos, trampas y objetos ya existentes como DTO del catálogo, cada uno una vez |

La línea guardada lleva exactamente: `k`, `acciones`, `puntos`, `cargas` y `fichas`. No hay nada más
(el pergamino no deja marcadores: la línea toma un punto de control nuevo, ver
[research.md, R4](../research.md)).

Restricciones que Derek puede validar al leer:

- `k ≥ 1`.
- `acciones` en orden creciente de `tiempo`.
- `puntos` en orden **estrictamente** creciente de `acciones_completadas`, cada una entre 0 y la cantidad
  de `acciones`, y a lo sumo `k` acciones entre dos puntos consecutivos (después de un pergamino dos
  puntos pueden estar más cerca que `k`).
- El punto de `partida.linea` es siempre `None` (no se anida la línea dentro de sí misma).

## 2. Bloque binario (versión 2)

- `VERSION_FORMATO` pasa de 1 a **2**. La cabecera sigue empezando por la magia `CRPT` y la versión,
  que se compara **antes** de interpretar el resto (ya ocurre hoy).
- La cabecera gana el **offset y el largo** del bloque de la línea (campos nuevos en la cabecera; el
  índice de salas y los bloques de sala no cambian de formato).
- El bloque de la línea usa los mismos escritores y lectores primitivos de hoy (`entero`,
  `texto_opcional`, `cantidad`…) y escribe, en este orden: `k`, la cantidad y las acciones, la cantidad y
  los puntos (cada uno con su `acciones_completadas`, su bloque global y sus salas), la cantidad y las
  cargas, la cantidad y las fichas. No hay marcadores de pergamino.
- Si `linea` es `None`, el bloque ocupa largo 0.
- **Archivo de la primera parte (versión 1)**: se rechaza como incompatible con un mensaje que dice la
  versión leída y la esperada, sin cargar nada y sin modificar la partida actual (FR-421). No se migra.
- Leer solo una sala del archivo (`cargar_sala`) no debe leer el bloque de la línea.

## 3. Método nuevo del motor (Marco, revisa)

`Motor.avanzar_hasta(t)`: avanza ejecutando los eventos **válidos** con tiempo ≤ t.

| Situación | Resultado |
|---|---|
| Quedan eventos válidos con tiempo ≤ t | Los ejecuta en el orden determinista de la cola |
| El siguiente evento es del jugador (una decisión) con tiempo ≤ t | Se detiene justo antes de tomarla; el reloj queda en ese tiempo (FR-402) |
| El siguiente evento válido tiene tiempo > t, o no hay | Se detiene |
| La partida terminó en t | Se detiene al terminar; los demás eventos de t no se ejecutan (FR-402) |
| Eventos cancelados | No cuentan: la cola los descarta |

Devuelve `True` si se detuvo en una decisión del jugador, `False` en otro caso. **No** modifica
`avanzar_hasta_jugador`. Antes de devolver `True` hace lo mismo que `avanzar_hasta_jugador` (registra el reloj
y el evento pendiente del jugador en el historial y cierra el intervalo).

**Regla que se implementó para un instante t** (`ReconstructorEstado.hasta_instante`, que usa este método):

- `j` es la última acción con tiempo **estrictamente menor** que t. Si en t hay una decisión del jugador, esa
  acción no se hace: el estado pedido es el de justo antes de ella (así `historia <t>` coincide con `historia #k`).
- Se parte de un punto de control con `acciones_completadas == j` cuando ese punto ya está en la decisión de t
  (su reloj es mayor o igual que t). **No** se llama a `avanzar_hasta(t)` en ese caso: correría los eventos de ese
  instante que la cola ordena después de la decisión, y FR-402 pide el estado justo antes de ella.
- Si no, se parte del último punto con `acciones_completadas <= j − 1`, se re-simulan las acciones hasta la
  `j − 1`, se ejecuta la `j` y se llama a `avanzar_hasta(t)`.
- Excepción: si la partida terminó y t es el reloj del final, la acción que cae en t **sí** se aplica (fue la que
  terminó la partida): el estado de ese instante es el final, igual al vivo.


## 4. Comandos y banderas

### En la interfaz (FR-423, §7.3)

| Entrada | Efecto |
|---|---|
| `historia <t>` | Muestra el resumen del estado en el instante t (entero ≥ 0, no posterior al reloj actual) |
| `historia #k` | Muestra el resumen justo antes de la acción número k |
| `historia`, `historia abc`, `historia -3`, `historia #x` | Mensaje de uso; la partida no cambia (FR-409) |

Una consulta no consume tiempo, no cuenta como acción, no se anexa a `partida.log` y no modifica el
historial de retroceso (FR-407, FR-408).

### Línea de comandos

| Entrada | Efecto | Código |
|---|---|---|
| `--replay partida.log --hasta T` | Reproduce hasta T e imprime el mismo resumen que `historia T` (FR-411). Sin vista. | 0 |
| `--replay partida.log` | Reproduce la partida completa, como en la primera parte | 0 |
| `--replay` con T posterior al final | Resumen del estado final e indica que la partida terminó antes de T (FR-412) | 0 |
| `--hasta` sin valor, no entero o negativo | Error de uso | 2 |
| `--hasta` sin `--replay` | Error de uso | 2 |
| Archivo inexistente o ilegible | Error con contexto, sin caerse | 1 |
| `--checkpoint-cada K` con K entero ≥ 1 | Fija K para la partida nueva | — |
| `--checkpoint-cada` con 0, negativo o no entero | Error de uso; no inicia con ese valor (FR-415) | 2 |

Sin `--checkpoint-cada` se usa el valor por defecto **provisional** del plan (K = 20), que se confirma
con `--bench`. Al **cargar** una partida guardada se conserva el K con el que se guardó su línea de
tiempo, aunque se indique otro `--checkpoint-cada` (Suposiciones de la spec); el K guardado viaja en
`LineaTiempoGuardadaDTO.k`.
