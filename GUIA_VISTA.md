# Guía de implementación de la Vista (Pygame) — Proyecto Cripta

> **Para Claude Code.** Este documento describe cómo implementar la parte gráfica del videojuego **sobre el proyecto
> existente**. La arquitectura, la lógica, los controladores y los recursos gráficos ya están hechos y probados.
> Aquí solo se construye la **Vista** y se integra con lo que hay.
>
> Basado en el estado del repositorio al **15 de octubre de 2026**. Todo lo que se afirma aquí fue comprobado contra
> el código y los archivos. La Etapa 0 vuelve a comprobarlo en tu copia, porque el repositorio pudo cambiar.

---

## 0. Cómo usar este documento (leer primero)

### 0.1 Reglas de conducta

1. **No rediseñes.** La arquitectura en capas, los DTO, los controladores y el contrato de la Vista están cerrados. Si
   crees que algo debe cambiar, **detente y pregunta** al usuario antes de tocarlo.
2. **No inventes.** Si un dato no está en este documento ni en el repositorio, averígualo leyendo el código o pregunta.
   Los valores marcados como *inicial* o *a ajustar* se calibran con capturas (sección 10.3), no se dan por buenos.
3. **Lee antes de escribir.** Antes de cada etapa, lee los archivos que esa etapa dice "Usa".
4. **Una etapa a la vez.** No empieces la siguiente hasta cumplir el criterio de "Hecho cuando" de la actual.
5. **Idioma:** comentarios, docstrings, mensajes y nombres de dominio en **español**. Código en el estilo del
   repositorio (sección 3.2).
6. **No copies archivos enteros** de otras capas dentro de la Vista ni dupliques lógica que ya existe.
7. **Deja el repositorio limpio** al terminar cada etapa: sin `__pycache__`, sin `cache/`, `logs/` ni `saves/` generados
   por tus pruebas (las pruebas usan carpetas temporales), sin archivos de depuración.

### 0.2 Ciclo de trabajo por etapa

```
 leer → implementar (lo mínimo) → comprobar → ¿falla? → diagnosticar → corregir → volver a comprobar
                                      │
                                      └─ ¿pasa? → informar y esperar el OK del usuario
```

- **Comprobar** = ejecutar los comandos de la sección "Comprobaciones" de la etapa y mirar las capturas si las pide.
- **Si algo falla:** lee el error completo, encuentra la causa (no el síntoma), corrige y **repite toda la
  comprobación** de la etapa (no solo el caso que falló). Máximo **3 intentos** por problema; si no se resuelve,
  detente y explica al usuario qué probaste.
- **Un error en una capa que no es la tuya** (Controlador, Servicios, Lógica, Datos): no lo escondas con un parche en
  la Vista. Repórtalo con la prueba mínima que lo reproduce y espera instrucciones.
- **Informe al terminar cada etapa** (breve): qué se hizo · archivos creados/modificados · comandos ejecutados y su
  resultado · decisiones tomadas · pendientes o dudas.

### 0.3 Comandos

El usuario trabaja en **Windows (PyCharm, PowerShell)**. El PowerShell antiguo **no entiende `&&`**: escribe un comando por línea.
Los comandos asumen el entorno virtual del proyecto activo (`.venv\Scripts\python` en Windows).

---

## 1. Alcance

### 1.1 Se implementa

- La clase `VistaPygame` (archivo `View/VistaPygame.py`) que cumple el **contrato de 4 métodos** de la sección 4, y
  los módulos de apoyo de `View/` que haga falta (sección 8).
- La carga y búsqueda de sprites con las reglas de la sección 6.
- Todas las pantallas de la sección 7: menú, criptas, nombre, juego, pausa, victoria, derrota y puntajes.
- El cableado de `main.py` (modo interactivo) y las pruebas de la Vista.
- (Opcional, al final) las animaciones.

### 1.2 NO se implementa

| No hacer | Por qué |
|---|---|
| Cambiar teclas, ratón, doble clic, hover o botones | Ya los resuelve `UIController/` (sección 4.5). |
| Llamar a Servicios, Lógica o Datos desde la Vista | Arquitectura en capas estricta. |
| Reglas del juego en la Vista | La Vista solo dibuja lo que dice el DTO. |
| Sonido, música, remapeo de teclas, arrastrar y soltar | Fuera de alcance (YAGNI). |
| Sprites de trampas, de efectos o de muertos | No se usan (sección 6.5). |
| Ids de entidades o de salas escritos en el código | Prohibido por el enunciado (§9). |

---

## 2. Estado actual del proyecto

### 2.1 Capas y carpetas

```
Datos  <->  Lógica  <->  Servicios  <->  Interfaz (Controlador + Vista)        DTO atraviesa todas las capas
```

| Carpeta | Contenido | ¿La toca esta guía? |
|---|---|---|
| `DTO/` | Datos que viajan entre capas (`@dataclass(frozen=True)`, sin lógica) | Solo `EstadoJuegoDTO` (Etapa 1) |
| `Data/`, `Logic/`, `Estructuras/`, `Security/` | Red/disco/caché, motor del juego, estructuras propias, validador | No (`Security` solo se *usa*) |
| `Service/` | Servicios y `ArmadorEstado` | Solo `ArmadorEstado` (Etapa 1) |
| `UIController/` | `ControladorBackend`, `ControladorPygame`, `ControlesJuego`, `LectorArgumentos` | **No** |
| `View/` | Vacía (solo `prueba.txt`, parece un marcador) | **Aquí se trabaja** |
| `tests/` | `Test*.py` (unittest) y `test_*.py` (scripts con funciones `probar_*`) | Se agregan pruebas de la Vista |
| `Assets/assets/` | Recursos gráficos (ver 2.4 sobre su ubicación) | Se usa |
| `main.py` | Hoy es un "¡Hola!" de prueba | Etapa 8 |

Las carpetas del proyecto **no tienen `__init__.py`** (excepto `tests/`). No lo agregues en `View/`.

### 2.2 Piezas existentes que la Vista usa o respeta

| Archivo | Qué es | Cómo se relaciona con la Vista |
|---|---|---|
| `UIController/ControladorPygame.py` | Flujo de pantallas, botones, bucle principal (`FPS = 30`). Su docstring define el contrato de la Vista. | Llama a los 4 métodos de la Vista. **No se modifica.** |
| `UIController/ControlesJuego.py` | Controles de la partida (teclado y ratón). Constantes `BOTONES`, `AYUDA_JUEGO`, `DOBLE_CLIC_MS`. | Decide qué hace cada clic sobre lo que la Vista dibuja. **No se modifica.** |
| `UIController/ControladorBackend.py` | Fachada única hacia los Servicios (`ErrorOperacion`, `CRITERIOS_INVENTARIO`, `CRITERIOS_PUNTAJES`, `LARGO_MAXIMO_NOMBRE = 16`). | La Vista **no** lo usa; lo usa el Controlador. |
| `DTO/PantallaDTO.py` | Lo que la Vista recibe en cada cuadro. | Entrada de `dibujar`. |
| `DTO/ElementoDTO.py` | Qué hay bajo un punto: `ElementoDTO(tipo, indice)` y las constantes `ELEMENTO_*`. | Salida de `elemento_en`. |
| `DTO/EstadoJuegoDTO.py` y los DTO de la sección 5 | Estado de la partida. | Se leen para dibujar. |
| `DTO/Direcciones.py` | `N = 0, S = 1, E = 2, O = 3`, `DIRECCIONES = ["N","S","E","O"]`. | Índices de las salidas y de las puertas. |
| `Security/ValidadorAcceso.py` | `es_nombre_seguro(texto)`: solo letras y números ASCII, `-` y `_`. | Validar ids **antes** de armar una ruta de archivo. |
| `Service/ArmadorEstado.py` | Construye el `EstadoJuegoDTO` (`armar_estado`). | Se amplía en la Etapa 1. |
| `tests/ayudas_pygame.py` | `VistaFalsa`, `Reloj`, `Modificadores`, eventos `tecla`, `letra`, `clic`, `movimiento`, `rueda`, `crear_fabrica`. | Se reutiliza en las pruebas. |
| `tests/ayudas_controladores.py` | `crear_backend`, `crear_partida`, `paquete_con_otra_version`, `CONFIG_OFFLINE`, `RAIZ`. | Se reutiliza (servicios reales, paquete offline, carpetas temporales). |
| `Assets/LEEME.md` | Reglas de nombres y de búsqueda de sprites. | Fuente de la sección 6. |

> **Contrato antiguo descartado.** El documento de contexto del equipo (`CONTEXTO_Y_PLAN_CRIPTA.md`) menciona una
> `VistaConsola` con `pedir_comando`, `mostrar_estado`, etc. y unas "etapas a–f" de la Vista. Eso quedó **superado**:
> la Vista de Pygame NO traduce teclas a comandos de texto. Rige el contrato de la sección 4.

### 2.3 Línea base de pruebas (antes de empezar)

| Comando | Resultado esperado |
|---|---|
| `python -m unittest discover -s tests -p "[Tt]est*.py"` | `Ran 319 tests … OK` |
| `python tests/test_controlador_backend.py` | `OK: todas las pruebas de ControladorBackend pasaron` (31 pruebas) |
| `python tests/test_controles_juego.py` | `OK: todas las pruebas de ControlesJuego pasaron` (41 pruebas) |
| `python tests/test_controlador_pygame.py` | `OK: todas las pruebas de ControladorPygame pasaron` (46 pruebas) |

Los scripts `test_*.py` **no son de `unittest`**: cada uno ejecuta sus funciones `probar_*` en el bloque
`if __name__ == "__main__":` e imprime una línea `OK` al final. `unittest discover` no los cuenta: hay que correrlos
uno por uno. Hay 17 scripts en total.

Esas cifras se verificaron con **Python 3.12 y pygame-ce 2.5.8**. El proyecto exige Python **≥ 3.14**
(`pyproject.toml`): la Etapa 0 las confirma en el intérprete real del usuario.

### 2.4 Hallazgos del entorno que requieren acción (Etapa 0)

| Hallazgo | Acción |
|---|---|
| **Los recursos están en `Assets/assets/`** (con `A` mayúscula y un nivel de más). El `LEEME.md` y las reglas esperan `assets/` en la raíz. | **Pregunta al usuario** si moverlos a `assets/` (raíz). No los muevas sin su OK. La Vista recibe la ruta como parámetro (sección 8). |
| `pyproject.toml` **no** lista `pygame-ce` (solo `requests`). | `uv add pygame-ce` (el profesor lo autorizó). |
| El `.venv` del usuario puede no existir (ya tuvo ese problema). | Si el intérprete falla: `uv sync` y luego `uv add pygame-ce`. |
| `.gitignore` **no** ignora `.venv/`. | Agregar `.venv/`. También `capturas/` (sección 10.3). |
| `main.py` es el "¡Hola!" de prueba. | Etapa 8. |
| `EstadoJuegoDTO` **no** trae la sala inicial ni la de salida. | Etapa 1 (los fondos `inicial`/`final` y la `puerta_final` dependen de eso). |

---

## 3. Reglas obligatorias

### 3.1 Del enunciado

| Regla | Qué implica para la Vista |
|---|---|
| **§7:** `dict` **no** puede ser índice, caché ni tabla de búsqueda. | **No uses `dict` ni `set` en la Vista** para guardar sprites ni para buscar nada. Usa **listas paralelas** y búsqueda lineal (hay unas decenas de sprites). |
| **§9:** nada de una cripta concreta en el código. | Sin ids de entidades (`ent_…`, `itm_…`), sin números de sala, sin presupuestos ni estadísticas fijas. Los sprites se buscan **por nombre de archivo**. |
| **§6:** `--replay` y `--bench` corren sin vista. | `pygame` y `View/` se importan **solo** en modo interactivo (`main.py`, Etapa 8). |
| **§10.2:** la vista debe mostrar suficiente información. | Sala actual, salidas, enemigos, objetos del suelo, vida y estadísticas, efectos y los **últimos 20 mensajes**. |
| **§5.1:** al terminar se reporta. | Solicitudes realizadas, presupuesto, aciertos y fallos de caché (`ReporteDatosDTO`). |
| **§2.12:** tabla de puntajes. | Nombre, id y versión de la cripta, acciones, enemigos derrotados, tiempo final (`PuntajeDTO`). |
| **§2.6:** cada enemigo debe ser identificable. | Mostrar `ActorDTO.nombre` (por ejemplo `Rata gigante #1`). |
| Bibliotecas: solo las del enunciado. | Se permite `pygame` (aquí **pygame-ce**), `dataclasses`, y de la biblioteca estándar solo lo mínimo (`os`/`pathlib` para rutas). Si necesitas otra, pregunta. |

### 3.2 Del equipo

- Archivos y clases en `PascalCase` (`VistaPygame.py`); métodos, funciones y campos en `snake_case` en español.
- **KISS, YAGNI y responsabilidad única.** No crees una clase, un parámetro o un archivo "por si acaso". Divide un
  archivo **solo si se justifica** (razón de cambio distinta, se prueba sin el resto, mejora la lectura). Si un módulo
  de apoyo te queda de menos de ~80 líneas, fusiónalo con su vecino.
- DTO: `@dataclass(frozen=True)`, sin `dict` como campo, sin lógica.
- Errores esperados con mensaje comprensible; los errores de programación no se esconden.
- Pruebas nuevas: **demuestra que fallan** quitando piezas a propósito (sección 10.4).

### 3.3 Específicas de la Vista

1. **Importa solo de:** `pygame`, `DTO/`, `Security/` y la biblioteca estándar mínima. **Nunca** de `UIController/`, `Service/`, `Logic/`, `Data/` ni `Estructuras/`.
2. **La Vista no lee el teclado ni el ratón.** No llames `pygame.event.get/poll/pump`, `pygame.key.get_mods`, ni `pygame.mouse.get_pos`. El bucle de eventos es del Controlador.
3. **No actives el repetidor de teclas** (`pygame.key.set_repeat`): mantener pulsada una tecla repetiría acciones del juego.
4. **No cambies ningún DTO** salvo `EstadoJuegoDTO` en la Etapa 1 y `PantallaDTO.elemento_bajo_el_raton` en la Etapa 6 (excepción autorizada por el usuario, junto con el cambio mínimo en `ControladorPygame` que lo llena; ver 4.3).
5. **Inicia pygame sin audio:** `pygame.display.init()` y `pygame.font.init()`, no `pygame.init()` (comprobado: así no se inicia el mezclador).
6. **`dibujar` no modifica nada:** recibe un DTO inmutable; no lo guardes para alterarlo ni lo uses para decidir reglas del juego.

---

## 4. Contrato Controlador ↔ Vista

### 4.1 Los 4 métodos (no se pueden cambiar)

```python
class VistaPygame:
    def abrir(self) -> None: ...                       # crea la ventana; se llama UNA vez antes del bucle
    def dibujar(self, pantalla: PantallaDTO) -> None: ...   # dibuja UN cuadro (≈30 por segundo)
    def cerrar(self) -> None: ...                      # se llama SIEMPRE al terminar, aunque el bucle falle
    def elemento_en(self, posicion: tuple[int, int]) -> ElementoDTO | None: ...
```

| Método | Semántica exacta |
|---|---|
| `abrir()` | Inicia `display` y `font`, crea la ventana, carga lo imprescindible. Se llama antes de cualquier `dibujar`. |
| `dibujar(pantalla)` | Dibuja todo el cuadro y **reconstruye las zonas de clic** (sección 4.4). Debe tardar bastante menos de 33 ms. |
| `cerrar()` | Libera pygame (`pygame.quit()` o equivalente). Debe ser seguro aunque `abrir` no se haya completado. |
| `elemento_en(posicion)` | Devuelve el `ElementoDTO` que hay en ese punto **en lo último que se dibujó**, o `None`. Debe poder llamarse **antes del primer `dibujar`** (devuelve `None`). Se llama en cada clic y en cada movimiento del ratón. |

### 4.2 Flujo por cuadro (lo hace `ControladorPygame.ejecutar`)

```
vista.abrir()
mientras el jugador no salga:
    para cada evento de pygame.event.get():  controlador.procesar_evento(evento)   # puede llamar a vista.elemento_en
    vista.dibujar(controlador.pantalla())                                          # un PantallaDTO nuevo cada cuadro
    reloj.tick(30)
finalmente: vista.cerrar()
```

### 4.3 `PantallaDTO`: qué llega en cada pantalla

Valores **reales** (generados con el controlador y los servicios reales). `seleccion` es la posición del botón
resaltado en `opciones` (teclado o ratón); **`-1` = ninguno**.

| `pantalla` | `titulo` | `opciones` (botones) | Otros campos llenos |
|---|---|---|---|
| `"menu"` | `"CRIPTA"` | `Comenzar juego`, `Modo: Offline` u `Online`, `Cargar partida`, `Puntajes`, `Salir` | `aviso`, `ayuda` (2 líneas) |
| `"criptas"` | `"Elige una cripta"` | una por cripta: `<nombre> - <salas> salas, dificultad <n>`; **y al final** `Volver` | `aviso`, `ayuda` (3) |
| `"nombre"` | `"¿Cómo te llamas?"` o `"Nombre para cargar la partida"` | `Aceptar`, `Volver` | `texto` (lo que se escribe, máx. 16), `aviso`, `ayuda` (3) |
| `"juego"` | `""` | `Esperar` | `estado`, `objetivo`, `elemento_bajo_el_raton`, `aviso`, `ayuda` (11 líneas), `seleccion` ∈ {-1, 0} |
| `"pausa"` | `"Pausa"` | `Continuar`, `Guardar partida`, `Cargar partida`, `Salir al menú` | `estado` (para dibujar la partida de fondo), `aviso`, `ayuda` (3) |
| `"victoria"` | `""` | `Jugar de nuevo`, `Ver puntajes`, `Menú principal` | `estado`, `puntaje` (puede ser `None`), `reporte`, `aviso`, `ayuda` (3) |
| `"derrota"` | `""` | las mismas tres | las mismas |
| `"puntajes"` | `"Puntajes"` | `Cambiar el orden`, `Volver` | `puntajes` (lista ya ordenada), `criterio` (`enemigos`, `tiempo`, `acciones` o `nombre`), `aviso`, `ayuda` (3) |

Notas:
- **Los textos de `opciones` y `ayuda` ya vienen listos**: la Vista los dibuja tal cual, no los reescribe ni los traduce.
- `aviso` es un mensaje breve (error o motivo de una acción rechazada); `None` si no hay. Dura hasta la siguiente acción del jugador.
- `objetivo` es el **id** del enemigo al que atacaría la tecla Espacio (`None` si no hay enemigos).
- En `"victoria"`/`"derrota"`, `puntaje` es `None` si no se pudo guardar; en ese caso `aviso` lo explica.
- **`elemento_bajo_el_raton`** (solo en `"juego"`; `None` en las demás): el `ElementoDTO` que `vista.elemento_en` devolvió en el último
  `MOUSEMOTION`. El controlador lo guarda sin consultas nuevas a la Vista y lo borra con cualquier tecla, clic o rueda y al cambiar de
  pantalla (para no mostrar un nombre desfasado). La Vista lo usa para escribir el nombre de un objeto del suelo junto a él; con cualquier
  otro tipo de elemento, o un índice fuera de rango, no dibuja nada. La Vista sigue sin leer el ratón.

### 4.4 `ElementoDTO` y zonas de clic

`dibujar` registra **un rectángulo por cada cosa clicable** que dibuja; `elemento_en` devuelve el elemento del
rectángulo que contiene el punto.

| `tipo` (constante en `DTO/ElementoDTO.py`) | `indice` | Registrar cuando |
|---|---|---|
| `ELEMENTO_BOTON` | posición en `pantalla.opciones` | siempre que se dibuje un botón (**en todas las pantallas con `opciones`**, incluido `Esperar`) |
| `ELEMENTO_ENEMIGO` | posición en `estado.enemigos` | por cada enemigo dibujado |
| `ELEMENTO_OBJETO_SUELO` | posición en `estado.objetos_suelo` | por cada objeto del suelo dibujado |
| `ELEMENTO_PUERTA` | dirección (`N=0, S=1, E=2, O=3`) | por cada salida **cerrada** (`salidas[d].cerrada`) que se dibuje |
| `ELEMENTO_INVENTARIO` | posición en `estado.inventario.objetos` | por cada casilla **ocupada** del inventario |

**Prioridad cuando se superponen:** gana lo que está dibujado encima. Regístralas **en el orden en que dibujas** (fondo
→ escena → panel → botones) y que `elemento_en` recorra la lista **de la última a la primera**.

**Coordenadas:** `elemento_en` recibe la posición del evento del ratón. Con la ventana creada con `pygame.SCALED`, se
espera que pygame entregue esas posiciones **ya convertidas a la resolución lógica**; dibuja y registra zonas en esa
misma resolución (sección 8). **Eso no está comprobado**: solo se puede confirmar a mano con una ventana real (Etapa 8).

### 4.5 Lo que el Controlador YA hace (no reimplementar en la Vista)

| Ya resuelto en `UIController/` | La Vista solo debe… |
|---|---|
| Movimiento del resaltado con ↑/↓ y con el ratón (`MOUSEMOTION` → `seleccion`) | dibujar el botón `seleccion` resaltado. |
| Activar un botón con Enter o clic izquierdo | dibujar los botones y registrar sus zonas. |
| Escribir el nombre (teclado, borrar, límite de 16) | dibujar `texto` (con cursor parpadeante si quiere) en un campo. |
| Atacar con clic en enemigo o Espacio; recoger con clic en el suelo; abrir con `E` o clic en la puerta | dibujar enemigos, suelo y puertas con sus zonas. Resaltar el enemigo `objetivo`. |
| Inventario: rueda/Tab recorren; clic selecciona; doble clic usa; clic derecho equipa; Mayús+clic suelta; `V` cambia la vista | dibujar `inventario` (cursor en `inventario.cursor`, criterio en `inventario.criterio`). |
| Guardar/cargar (`Ctrl+S`, `F5`, `Ctrl+L`, `F9`), pausa (`Esc`), pergamino (`Backspace`, `Ctrl+Z`), esperar (`Z`) | mostrar `aviso` y `ayuda`. |
| Cerrar la ventana (evento `QUIT`) | nada: lo atiende el Controlador. |

El inventario está **siempre visible** durante la partida (no hay tecla ni pantalla para abrirlo).

---

## 5. Datos del juego que la Vista dibuja (DTO reales)

| DTO | Campos |
|---|---|
| `EstadoJuegoDTO` | `sala: SalaDTO` · `jugador: ActorDTO` · `enemigos: list[ActorDTO]` · `objetos_suelo: list[ObjetoDTO]` · `efectos: list[EfectoDTO]` · `inventario: InventarioDTO` · `mensajes: list[str]` (los últimos 20, cronológicos, formato `"[t=150] Texto"`) · `reloj: int` · `terminado: bool` · `resultado: str \| None` (`"victoria"`, `"derrota"` o el motivo de un rechazo) · *(Etapa 1:)* `sala_inicial`, `sala_salida` |
| `SalaDTO` | `id: int` · `nombre: str` · `salidas: list[SalidaDTO \| None]` (4 posiciones: N, S, E, O) · `version` · … |
| `SalidaDTO` | `sala_destino: int` · `cerrada: bool` · `llave: str \| None` · `cierre_automatico: int \| None` |
| `ActorDTO` | `id` · `tipo` (**id del catálogo** en enemigos, p. ej. `ent_rata_gigante`; `"jugador"` en el jugador) · `nombre` (p. ej. `Rata gigante #1`) · `vida` · `vida_max` · `ataque` · `defensa` · `velocidad` · `sala_actual` |
| `ObjetoDTO` | `id` (id del catálogo) · `nombre` · `clase` (`arma`, `armadura`, `pocion`, `antidoto`, `llave`, `antorcha`, `pergamino_retroceso`) · `peso` · `valor` · `ataque_bonus` · `defensa_bonus` · `cura` · `modificador_velocidad` · `duracion` · `abre` (los opcionales pueden ser `None`) |
| `InventarioDTO` | `objetos: list[ObjetoDTO]` (**en el orden de la vista actual**) · `cursor: int` · `capacidad: int` (cuántos hay) · `capacidad_maxima: int` · `arma_equipada: str \| None` y `armadura_equipada: str \| None` (**ids**) · `criterio: str \| None` (`None` = orden real, o `peso`, `valor`, `nombre`) |
| `EfectoDTO` | `tipo` (`veneno`, `velocidad`, `antorcha`) · `restante: int` (unidades de tiempo virtual) · `valor: int \| None` (veneno: daño por pulso; velocidad: modificador, **positivo acelera y negativo ralentiza**; antorcha: `None`) |
| `PuntajeDTO` | `nombre` · `mazmorra` (id de la cripta) · `version` · `acciones` · `enemigos_derrotados` · `tiempo_final` |
| `ReporteDatosDTO` | `solicitudes_realizadas` · `presupuesto` (puede ser `None`) · `aciertos_cache` · `fallos_cache` · `lecturas_disco` · `fichas_descargadas` · `solicitudes_catalogo` · `lotes_contenido` · `salas_pedidas` · `offline: bool` |
| `ResumenCriptaDTO` | `id` · `nombre` · `salas` · `dificultad` (el controlador ya lo convierte en texto de `opciones`) |

**Limitación conocida del equipamiento:** `arma_equipada` y `armadura_equipada` son **ids**, no instancias. Si hay dos
objetos con el mismo id, marca como equipado **solo el primero** de `inventario.objetos` con ese id.

---

## 6. Recursos gráficos

### 6.1 Ubicación y contenido

Hoy: `Assets/assets/` (ver 2.4). Destino previsto por las reglas: `assets/` en la raíz. **52 imágenes** + `LEEME.md`
(las reglas de esta sección salen de ese `LEEME.md`; si difieren, manda el `LEEME.md` del repositorio).

| Carpeta | Archivos | Formato |
|---|---|---|
| `personajes/` (14) | `jugador_idle_1..3`, `jugador_ataque_1`, `jugador_caminar_1..3`, `jugador_muerte_1..3`, `jugador_direccion_{norte,sur,este,oeste}` | PNG con transparencia |
| `enemigos/` (20) | `enemigo_idle_1`, `enemigo_ataque_1..4`, `enemigo_muerte_1..4`, `enemigo_direccion_*` · `ent_rata_gigante_idle_1`, `ent_rata_gigante_ataque_1..2`, `ent_rata_gigante_direccion_*` | PNG con transparencia |
| `objetos/` (9) | `itm_antidoto`, `itm_antorcha`, `itm_coraza_cuero`, `itm_daga_oxidada`, `itm_llave_bronce`, `itm_llave_negra`, `itm_pergamino_retroceso`, `itm_pocion_menor`, y el respaldo `objeto` (una bolsa) | PNG con transparencia |
| `fondos/` (6) | `fondo_inicial`, `fondo_regular`, `fondo_final`, `fondo_menu`, `fondo_victoria`, `fondo_derrota` | **JPG** |
| `ui/` (3) | `puerta_cerrada`, `puerta_final`, `inventario` | PNG con transparencia |

`enemigo_*` es el conjunto **genérico** (figura encapuchada roja): es el respaldo de cualquier enemigo sin sprites
propios, **incluido `ent_guardian_oseo`** de `cripta-01`. `*_direccion_*` están **reservados**: la regla de búsqueda no
los usa todavía; no los uses.

### 6.2 Tamaños reales (para calibrar la escala)

| Grupo | Tamaño | Nota |
|---|---|---|
| Fondos de sala y menú | 1376×768 | `fondo_victoria` y `fondo_derrota`: 1375×768 (da igual: se escalan). |
| `puerta_cerrada` | 49×36 | Pixel art muy pequeño: ampliar **sin suavizar**. |
| `puerta_final` | 95×54 | Ídem. |
| `inventario` | 64×64 | Textura de panel (ladrillos/madera rojiza): se puede **repetir en mosaico** o estirar. |
| Objetos | 539×539 (la poción 250×250, el respaldo 160×160) | Se muestran mucho más pequeños (≈ 48–96 px). |
| Jugador | lienzos de 442–573 de ancho y 324–539 de alto | Fotogramas de **tamaño distinto** entre sí. |
| Enemigo genérico | 129–233 de ancho, 65–270 de alto | Mucho más pequeño que los demás. |
| Rata gigante | 539×539 (todos) | El animal ocupa solo parte del lienzo. |

### 6.3 Reglas de búsqueda (nombre de archivo = id del catálogo)

1. **Actor** (`ActorDTO.tipo`; el jugador tiene `tipo == "jugador"`), estado de animación `e` (`idle` por omisión):
   1. `<carpeta>/<tipo>_<e>_1.png`;
   2. si falta ese estado, `<carpeta>/<tipo>_idle_1.png`;
   3. si el conjunto no existe, lo mismo con `enemigos/enemigo` (solo para enemigos);
   4. si nada existe, **una figura dibujada** (por ejemplo un rectángulo con la inicial). Nunca debe fallar el juego por falta de un sprite.
   Carpetas: `personajes/` para `jugador`, `enemigos/` para los demás.
2. **Objeto:** `objetos/<id>.png`; si no existe, `objetos/clase_<clase>.png` (**opcional**, hoy no existe ninguno);
   si no existe, `objetos/objeto.png`; si tampoco, figura dibujada.
3. **Fondo de sala** (necesita la Etapa 1): `fondo_inicial` si `estado.sala.id == estado.sala_inicial`; `fondo_final` si
   `== estado.sala_salida`; **`fondo_regular` en todas las demás** (y en cualquier cripta que no conozcamos). Si
   inicial y salida coincidieran, usa `fondo_inicial`.
4. **Puertas:** una salida **abierta no dibuja nada** (los fondos ya traen el marco de las 4 puertas). Una salida
   **cerrada** dibuja `ui/puerta_cerrada.png`, salvo la que lleva a la sala de salida
   (`salidas[d].sala_destino == estado.sala_salida`), que dibuja `ui/puerta_final.png`.
5. **Seguridad:** antes de armar **cualquier** ruta con un id que venga de un DTO, valida con
   `Security.ValidadorAcceso.es_nombre_seguro`. Si no pasa, trátalo como "no existe" (ve al respaldo). Los ids vienen
   del servidor y podrían contener `..` o `/`.
6. **Fotogramas:** `n` = 1, 2, 3… consecutivos; se cargan hasta que falte uno. No se escribe cuántos fotogramas hay.

### 6.4 Reglas de dibujo de sprites

- **Escala:** pixel art (personajes, objetos, puertas) con `pygame.transform.scale` (vecino más cercano). Fondos con
  `pygame.transform.smoothscale`.
- **Anclaje:** los fotogramas tienen lienzos y márgenes distintos. Alinéalos por la **base del contenido real**:
  calcula `Surface.get_bounding_rect()` al cargar y ancla el `midbottom` de ese rectángulo en el punto de la escena.
  Así los pies quedan en la misma línea sin tocar los PNG. (Comprobado: `jugador_idle_1` es 523×523 pero su contenido
  es el rectángulo (28, 29, 467, 462).)
- Convierte con `convert_alpha()` (PNG) o `convert()` (JPG) **después** de crear la ventana.
- **Caché de imágenes** (cargadas y escaladas): listas paralelas (`nombres`, `superficies`…), **sin `dict`**. Recuerda
  también los fallos (un nombre que no existe) para no volver a mirar el disco en cada cuadro.
- **Puertas:** los sprites están hechos para el borde **norte**. Para S, E y O, rótalos con `pygame.transform.rotate`
  (grados antihorarios: N 0, S 180, E 270, O 90). Verifica con capturas que miran hacia el lado correcto.
- Las puertas se dibujan en el **centro del borde** correspondiente (en los fondos de sala, los marcos de puerta
  están en el centro de cada borde: **compruébalo mirando las imágenes** y fija esas posiciones como constantes).

### 6.5 Lo que NO usa sprites (se dibuja con código)

| Cosa | Cómo |
|---|---|
| **Efectos activos** (`veneno`, `velocidad`, `antorcha`) | Un **velo translúcido** del color del efecto sobre la pantalla de juego (superficie `pygame.SRCALPHA` creada **una vez**) **más** una línea de texto con su nombre y `restante` (el color solo no dice cuál es ni cuánto dura). |
| Barras de vida (jugador y enemigos), paneles, marcos, botones, cursor del inventario, número de casilla, texto | `pygame.draw` y fuentes. |
| Trampas | **No se muestran**: `EstadoJuegoDTO` no las incluye. No hay sprite. |
| Enemigos muertos | Desaparecen de `estado.enemigos`. No hay sprite. |
| Sonido | No hay. |

Colores propuestos para los velos (ajustables con capturas; **transparencia baja** para que el juego se siga leyendo):

| Efecto | Velo |
|---|---|
| `veneno` | verde |
| `velocidad` con `valor > 0` | azul |
| `velocidad` con `valor < 0` | violeta |
| `antorcha` | naranja cálido |
| otro `tipo` desconocido | sin velo, solo la línea de texto |

Con varios efectos a la vez, los velos se superponen.

### 6.6 Observaciones sobre las imágenes (afectan al diseño)

- `fondo_menu.jpg` **ya contiene el título** ("Crypta" con dos demonios, sobre fondo negro). **No dibujes `pantalla.titulo`**
  en el menú.
- `fondo_victoria.jpg` y `fondo_derrota.jpg` **ya contienen su mensaje** en un recuadro central ("¡Victoria!" / "¡Derrota!"
  y una frase). **No dibujes otro título ni otro mensaje**; coloca el puntaje, el reporte y los botones **fuera de ese
  recuadro** (míralo en la captura y fija las zonas libres).
- `fondo_inicial` muestra una habitación con una cama; `fondo_regular`, una con antorchas; `fondo_final`, una sala roja con
  un pentagrama y un cofre. Los tres traen marcos de puerta; **verifica con capturas** dónde están antes de fijar posiciones.
- Las salidas que **no existen** en una sala siguen mostrando su marco en el fondo. Decisión abierta (sección 12): lo
  recomendado es **oscurecer con código** esos marcos (un rectángulo oscuro) para que no parezcan salidas.

---

## 7. Requisitos visuales por pantalla

Fuente de verdad: enunciado §10.2 (qué debe mostrar), §5.1 y §2.12 (fin), más las reglas de la sección 6. Las
posiciones y tamaños **se deciden con capturas** y el usuario las aprueba.

### 7.1 Pantallas con botones (`menu`, `criptas`, `nombre`, `pausa`, `puntajes`)

- Fondo: `fondo_menu` para `menu`, `criptas`, `nombre` y `puntajes`. En `pausa`, la **partida de fondo**
  (`pantalla.estado`) con un velo oscuro encima.
- Los botones se dibujan como una columna centrada, uno por cada texto de `opciones`, con el de `seleccion` resaltado.
  Tamaño suficiente para hacer clic cómodamente. Cada uno registra su zona `ELEMENTO_BOTON`.
- `criptas`: puede haber muchas criptas: la lista debe seguir siendo legible (si no cabe, reduce el tamaño del botón).
- `nombre`: campo de texto con `pantalla.texto` y cursor; los botones `Aceptar` y `Volver` debajo.
- `puntajes`: tabla con una fila por `PuntajeDTO` (columnas: nombre, cripta, acciones, enemigos derrotados, tiempo
  final), indicando el `criterio` de orden, y los botones. Si no hay filas, un texto "Aún no hay puntajes".
- Siempre: `aviso` visible y destacado si no es `None`; `ayuda` como pie discreto.

### 7.2 Pantallas de fin (`victoria`, `derrota`)

- Fondo `fondo_victoria` / `fondo_derrota` (sección 6.6).
- Mostrar `puntaje` (si no es `None`): nombre, cripta (`mazmorra`), acciones, enemigos derrotados, tiempo final.
- Mostrar `reporte` (§5.1): **solicitudes realizadas, presupuesto, aciertos de caché y fallos de caché**. Muestra
  `presupuesto` como "—" si es `None`; si `offline` es verdadero, indícalo (las lecturas locales no cuentan como solicitudes).
- Tres botones (`Jugar de nuevo`, `Ver puntajes`, `Menú principal`) y `aviso`.

### 7.3 Pantalla de juego (`juego`)

Debe mostrar (§10.2):

| Qué | De dónde sale |
|---|---|
| **Sala actual** (nombre) | `estado.sala.nombre` |
| **Salidas** | `estado.sala.salidas`: puertas cerradas dibujadas (6.3); marcos del fondo para las abiertas |
| **Enemigos** | `estado.enemigos`: sprite (6.3), `nombre`, barra `vida`/`vida_max`; el `objetivo` resaltado; sin aura |
| **Objetos del suelo** | `estado.objetos_suelo`: sprite (6.3) con un **aura** (resplandor dorado suave, sin etiqueta permanente); su `nombre` aparece **solo al pasar el ratón** (`pantalla.elemento_bajo_el_raton`, ver 4.3) |
| **Jugador** | sprite `jugador` y barra `vida`/`vida_max` |
| **Estadísticas** | `estado.jugador`: vida, ataque, defensa, velocidad; y `estado.reloj` |
| **Efectos** | velo + línea de texto por cada `EfectoDTO` (6.5) |
| **Últimos 20 mensajes** | `estado.mensajes`: **mostrar los 20** (o todos los que haya), más recientes abajo; panel con capacidad para 20 líneas |
| **Inventario (siempre visible)** | ver abajo |
| **Botón `Esperar`** | `opciones[0]`, zona `ELEMENTO_BOTON` con índice 0 |
| `aviso` y `ayuda` | `aviso` destacado; `ayuda` (11 líneas) en un panel compacto |

**Inventario:** panel con `capacidad_maxima` casillas (usa `ui/inventario.png` como textura del panel o de las
casillas); cada objeto ocupa una casilla con su sprite y registra `ELEMENTO_INVENTARIO` con su posición en
`inventario.objetos`; el `cursor` resaltado; marca de "equipado" (limitación conocida en la sección 5); el `criterio` de la
vista ("Orden: real / peso / valor / nombre"); el contador `capacidad/capacidad_maxima`; y los datos del objeto bajo el
cursor (`nombre`, `clase`, `peso`, `valor` y los bonus que no sean `None`).

**Orden de dibujo (y de registro de zonas):** fondo → marcos oscurecidos → puertas → **protagonista, enemigos y objetos del suelo
ordenados por los pies (el de más abajo, encima)** → nombre del objeto bajo el ratón → velos de efectos → HUD (stats, mensajes,
inventario) → botón → aviso/ayuda. La prioridad de las zonas de clic coincide con ese orden.

**Tamaños de la escena** (alto del contenido del sprite, todo en `View/Componentes.py`; sin ids de cripta, §9). Son tres categorías,
no una tabla por nombre:

| Categoría | Cómo se reconoce | Alto |
|---|---|---|
| protagonista | `ActorDTO.tipo == "jugador"` | **90 px fijos** (`ALTURA_JUGADOR`), igual en todas las escenas |
| enemigo con sprites propios (la rata) | `ConjuntoSprites.origen` no es el genérico | 190 px (`ALTURA_ENEMIGO`) |
| enemigo de respaldo (conjunto `enemigo`, o figura dibujada) | `View.AlmacenSprites.es_de_respaldo(conjunto)` mira el `origen` | 85 % del anterior (`FACTOR_RESPALDO`) |

Se cumple propios ≥ genérico > protagonista. Con una escala común el genérico saldría diminuto (su contenido mide 226 px y el del
jugador 462), por eso la escala sale de la altura pedida (`AlmacenSprites.actor_a_altura`). Si hay tantos enemigos que no caben, **todos**
los enemigos se achican con el mismo factor (`FACTORES_ENEMIGOS`) para conservar sus proporciones; el protagonista no cambia.

**Dónde pisa el protagonista** (`posicion_del_protagonista(salidas, id_sala_anterior)`, función pura): sin sala anterior (inicio de
partida, partida cargada o vuelta desde el menú), en el **centro del suelo**; al entrar a una sala nueva, **delante de la puerta por la
que entró**, que es la salida de la sala nueva cuya `sala_destino` es la sala anterior. Si esa puerta no se puede determinar (la sala
anterior no es contigua, o hay varias salidas hacia ella), en el centro. La escena recuerda la sala anterior comparando el id de sala
entre cuadros y la olvida al mostrar `menu`, `criptas`, `nombre`, `victoria`, `derrota` o `puntajes` (la pausa no la olvida). Limitación:
una partida cargada desde la pausa no pasa por el menú, así que si la sala cargada fuera contigua a la anterior, el protagonista
aparecería junto a esa puerta.

**Reparto de enemigos y objetos** (`colocar`, función pura: tamaños, zonas ocupadas, suelo, pies del protagonista → rectángulos):
repartidos por el suelo (`SUELO`) **alrededor del protagonista** (cada uno toma la posición libre más cercana a un radio preferido:
enemigos cerca, objetos más lejos), sin tapar al protagonista ni los pasillos de las puertas con salida. Es determinista (nada de
azar), sus zonas no se solapan y caben de 1 a 12 enemigos y de 1 a 12 objetos a la vez, con el protagonista en el centro o junto a
cualquiera de las cuatro puertas. `repartir_escena` aplica `colocar` a enemigos y objetos y es lo que usan las pruebas para saber dónde
hacer clic. El resultado se guarda y solo se recalcula si cambia algo de lo que depende (el cálculo más pesado, 12+12, tarda unos 150 ms).

**Aura de los objetos del suelo:** silueta del sprite teñida de dorado, difuminada (`AlmacenSprites.aura_de_objeto`, una vez por
objeto y guardada en la caché). No cambia la zona de clic (que es la del sprite) ni tapa a otros. Los enemigos no llevan aura.
Intensidad en `AURA_INTENSIDAD`.

---

## 8. Estructura de archivos propuesta (`View/`)

Es una **propuesta dentro de la capa de la Vista**, no un rediseño. Crea cada archivo **solo cuando su etapa lo
necesite**, y fusiona los que te queden pequeños (regla de la sección 3.2).

| Archivo (nuevo) | Responsabilidad | Etapa |
|---|---|---|
| `View/VistaPygame.py` | La clase del contrato: ventana, resolución lógica (`1376×768` sugerida, `pygame.SCALED \| pygame.RESIZABLE`, título `Cripta`), despacho según `pantalla.pantalla`, `elemento_en`. Recibe la ruta de los assets por el constructor (`VistaPygame(ruta_assets=...)`); por omisión usa la carpeta de recursos que exista (`assets/` o `Assets/assets/`) **resuelta respecto a la raíz del proyecto**, no al directorio desde el que se ejecute. | 2 |
| `View/AlmacenSprites.py` | Carga, escala y caché (listas paralelas); las reglas de la sección 6.3 y el anclaje de 6.4. | 3 |
| `View/ZonasClic.py` | Lista de (rectángulo, `ElementoDTO`); `limpiar`, `agregar`, `buscar` (de la última a la primera). | 4 |
| `View/Componentes.py` | Elementos reutilizables: botón, panel translúcido, barra de vida, texto con ajuste de línea. | 4 |
| `View/PantallaMenus.py` | `menu`, `criptas`, `nombre`, `pausa`, `puntajes`. | 4 |
| `View/PantallaFin.py` | `victoria` y `derrota`. | 5 |
| `View/EscenaJuego.py` | Fondo, puertas, protagonista, enemigos y objetos del suelo; funciones puras `fondo_para`, `puertas_a_dibujar`, `posicion_del_protagonista`, `colocar`, `repartir_escena`, `orden_de_dibujo`. Todas sus medidas están en `View/Componentes.py`. | 6 |
| `View/HudJuego.py` | Estadísticas, mensajes, inventario, efectos, botón, aviso, ayuda. | 7 |
| `View/Animaciones.py` | Solo si se hace la Etapa 9. | 9 |

**Decisiones puras, sin pygame (para poder probarlas sin dibujar píxeles).** Extrae a funciones pequeñas lo que
decide *qué* dibujar, y pruébalas por separado:

- nombre de archivo de un actor, objeto o fondo según las reglas de 6.3 (`fondo_para(estado)`, `puertas_a_dibujar(estado)`);
- texto y color de cada efecto (`efectos_a_mostrar(efectos)`);
- qué casillas del inventario están equipadas;
- qué zonas se registran para un `PantallaDTO` dado.

Borra `View/prueba.txt` al crear el primer archivo de la carpeta.

---

## 9. Etapas de implementación

> Para **cada** etapa: ciclo de la sección 0.2; informe al terminar; **espera el OK del usuario** antes de la siguiente.
> Las pruebas nuevas siguen el estilo del equipo: scripts `tests/test_*.py` con funciones `probar_*`, un bloque
> `if __name__ == "__main__":` que las llama a todas y un `print("OK: …")` final. Fija `SDL_VIDEODRIVER=dummy` **antes**
> de importar pygame (como hace `tests/ayudas_pygame.py`). Las pruebas nunca escriben en `cache/`, `logs/` ni `saves/`.

### Etapa 0 — Verificación inicial y entorno

**Objetivo:** confirmar que el punto de partida es el descrito y dejar el entorno listo.

**Pasos**
1. Lee el repositorio y confirma las secciones 2.1 y 2.2 (los archivos existen; los controladores y DTO nuevos están).
2. Intérprete: `python --version` (debe ser ≥ 3.14). Si el `.venv` no existe o falla: `uv sync`.
3. Dependencia: si `python -c "import pygame"` falla o `pyproject.toml` no lista `pygame-ce`, ejecuta `uv add pygame-ce`.
4. `.gitignore`: agrega `.venv/` y `capturas/`.
5. Ubicación de los recursos (2.4): **pregunta** al usuario y actúa según su respuesta. Mientras tanto, usa la carpeta que exista.
6. Línea base: ejecuta los comandos de la sección 2.3.

**Comprobaciones**
```
python --version
python -c "import pygame; print(pygame.version.ver)"
python -m unittest discover -s tests -p "[Tt]est*.py"
python tests/test_controlador_backend.py
python tests/test_controles_juego.py
python tests/test_controlador_pygame.py
```

**Hecho cuando:** `import pygame` funciona; los 4 comandos de prueba dan lo esperado (si alguna cifra difiere, **informa
la diferencia** antes de seguir); el usuario respondió dónde están los recursos.

### Etapa 1 — Prerrequisito de servicios: sala inicial y sala de salida

**Objetivo:** que la Vista sepa cuál es la sala inicial y cuál la de salida (para `fondo_inicial`, `fondo_final` y
`puerta_final`).

**Usa:** `CriptaDTO.sala_inicial` y `CriptaDTO.sala_salida` (ya existen); `ContextoPartida.cripta`.

**Archivos a modificar:** `DTO/EstadoJuegoDTO.py` y `Service/ArmadorEstado.py` (método `armar_estado`). Pruebas: en la
carpeta `tests/` (un script nuevo o ampliar `tests/test_servicios.py`, el que resulte más natural).

**Pasos**
1. Agrega a `EstadoJuegoDTO`, **al final y con valor por omisión**, `sala_inicial: int | None = None` y
   `sala_salida: int | None = None`. Actualiza su docstring. (Con valor por omisión al final nada existente se rompe:
   `ArmadorEstado.armar_estado` es el único sitio que lo construye y las pruebas lo hacen con argumentos por nombre.)
2. En `armar_estado`, rellénalos desde `contexto.cripta.sala_inicial` y `contexto.cripta.sala_salida`.
3. No cambies nada más (los controladores usan `dataclasses.replace`, que conserva los campos nuevos).

**Comprobaciones**
- Prueba nueva con el backend real offline (`tests/ayudas_controladores.crear_backend`): el estado inicial tiene
  `sala_inicial == estado.sala.id` y `sala_salida` igual al valor de `general.json` de la cripta en `paquete/` (léelo
  en la prueba; **no lo escribas fijo**). Ambos campos se mantienen tras mover al jugador, y tras guardar y cargar.
- Línea base completa de la sección 2.3 sigue en verde.

**Hecho cuando:** la prueba nueva pasa y demuestra fallar si se quita el relleno en `armar_estado` (sección 10.4).

### Etapa 2 — Esqueleto de la Vista y ventana

**Objetivo:** una `VistaPygame` que cumple el contrato y muestra algo, integrada con el controlador real.

**Usa:** el contrato (sección 4); `ControladorPygame(vista, config).ejecutar()` y `ControladorPygame.pantalla()`.

**Archivos:** `View/VistaPygame.py`; `tests/test_vista_contrato.py`.

**Pasos**
1. `abrir`: `pygame.display.init()`, `pygame.font.init()`, `set_mode` con `pygame.SCALED | pygame.RESIZABLE`, título
   `Cripta`, fuentes (`pygame.font.Font(None, tamaño)`: comprobado que dibuja tildes y `¡ ¿`).
2. `dibujar`: por ahora, un fondo liso y el contenido de `PantallaDTO` como **texto de depuración** (para ver que llega todo).
3. `elemento_en`: devuelve `None` (aún no hay zonas).
4. `cerrar`: `pygame.quit()`, seguro aunque `abrir` no se haya llamado.

**Comprobaciones** (con `SDL_VIDEODRIVER=dummy`; `SCALED` imprime un aviso "no fast renderer available" que es inofensivo)
- `abrir → dibujar → cerrar` sin error, y `cerrar()` seguro sin `abrir()`.
- `dibujar` no falla con el `PantallaDTO` **real** de cada una de las 8 pantallas, obtenidos conduciendo
  `ControladorPygame` con servicios reales (`tests/ayudas_pygame.crear_fabrica`) y eventos simulados (`tecla`, `clic`).
- `elemento_en` antes del primer `dibujar` devuelve `None`.
- El bucle real `ControladorPygame.ejecutar(fuente_eventos)` con la Vista real termina con un evento `QUIT` y llama a `cerrar`.

**Hecho cuando:** esas pruebas pasan y una captura (sección 10.3) muestra el texto de cada pantalla.

### Etapa 3 — Almacén de sprites

**Objetivo:** cargar y buscar sprites con las reglas de 6.3 y 6.4, **sin `dict`**.

**Archivos:** `View/AlmacenSprites.py`; `tests/test_vista_sprites.py`.

**Pasos:** implementa las reglas de actor, objeto, fondo y puerta; el anclaje por `get_bounding_rect`; la escala; la caché
con listas paralelas (recordando también los fallos); la validación con `es_nombre_seguro`; y la figura dibujada de respaldo.

**Comprobaciones** (con los **recursos reales** y también con una carpeta temporal casi vacía)
- Jugador: `idle` devuelve 3 fotogramas; `ataque`, 1; un estado inexistente cae a `idle`.
- `ent_rata_gigante` tiene `idle` (1) y `ataque` (2); `caminar` y `muerte` caen a `idle`.
- `ent_guardian_oseo` y un id desconocido caen al conjunto `enemigo`.
- Objeto `itm_daga_oxidada` existe; un id desconocido cae a `objetos/objeto.png`; con la carpeta temporal vacía cae a la figura dibujada **sin fallar**.
- Un id como `../x` o con `/` se trata como inexistente (no sale de la carpeta).
- Dos pedidos iguales no vuelven a leer el disco (comprueba con un contador o con identidad de objeto).
- Prueba de higiene: el archivo no contiene `dict(`, `{}` como caché ni `set(`; no importa capas prohibidas (sección 3.3).

**Hecho cuando:** pasan y las mutaciones de la sección 10.4 hacen fallar las pruebas.

### Etapa 4 — Zonas de clic, componentes y pantallas con botones

**Objetivo:** `menu`, `criptas`, `nombre`, `pausa` y `puntajes` con botones clicables y resaltado.

**Archivos:** `View/ZonasClic.py`, `View/Componentes.py`, `View/PantallaMenus.py`; pruebas `tests/test_vista_zonas.py` y `tests/test_vista_menus.py`.

**Pasos:** implementa `ZonasClic` (de la última a la primera); el botón (normal/resaltado por `seleccion`); el panel
translúcido; el texto con ajuste; y las cinco pantallas según 7.1. `VistaPygame.elemento_en` consulta `ZonasClic`.

**Comprobaciones**
- `ZonasClic`: punto en una zona devuelve su elemento; punto fuera, `None`; **zonas superpuestas devuelven la última registrada**; `limpiar` vacía.
- Tras `dibujar` de un `PantallaDTO` de menú con 5 botones: `elemento_en(centro_de_cada_zona)` devuelve `ElementoDTO("boton", i)` para `i` en 0..4, y `None` fuera.
- **Prueba de punta a punta (Vista real + `ControladorPygame` real + servicios reales + eventos simulados):** un clic sobre el centro del botón "Comenzar juego" lleva a `criptas`; el clic sobre una cripta, a `nombre`; escribir un nombre y clic en `Aceptar`, a `juego`; `Esc` abre `pausa` y su botón "Salir al menú" vuelve a `menu`. Mover el ratón sobre un botón cambia `seleccion` y la Vista lo muestra resaltado.
- Capturas de las 5 pantallas revisadas por ti (10.3): botones legibles, sin solaparse, el título del menú **no duplicado** (6.6).

**Hecho cuando:** pasan las pruebas, las capturas son correctas y el usuario aprueba el aspecto.

### Etapa 5 — Pantallas de victoria y derrota

**Objetivo:** `victoria` y `derrota` con puntaje, reporte y sus 3 botones.

**Archivos:** `View/PantallaFin.py`; `tests/test_vista_fin.py`.

**Pasos:** según 7.2 y 6.6 (respeta el recuadro del fondo; no dupliques el mensaje).

**Comprobaciones**
- Derrota **real**: conduce una partida con servicios reales hasta perder (en `cripta-01`: entrar a la sala con las
  ratas y esperar con `Z` hasta que el controlador pase a `derrota`) y comprueba que `dibujar` funciona y que cada botón
  responde a un clic (`Jugar de nuevo` → `criptas`, `Ver puntajes` → `puntajes`, `Menú principal` → `menu`).
- Victoria: con un `PantallaDTO("victoria", …)` construido a mano (la victoria real depende de la llave y del azar),
  incluyendo el caso `puntaje=None` con `aviso`, y `reporte.presupuesto=None`.
- Captura de ambas, mirando que puntaje, reporte y botones **no tapen** el recuadro del mensaje.

**Hecho cuando:** pasan y el usuario aprueba las capturas.

### Etapa 6 — Escena de juego

**Objetivo:** fondo por rol de sala, puertas, enemigos, jugador y objetos del suelo, con sus zonas de clic.

**Archivos:** `View/EscenaJuego.py`; `tests/test_vista_escena.py`.

**Pasos:** según 6.3, 6.4, 7.3 y el orden de dibujo; registra `ELEMENTO_ENEMIGO`, `ELEMENTO_OBJETO_SUELO` y
`ELEMENTO_PUERTA` (solo salidas cerradas). Oscurece los marcos sin salida si el usuario lo aprueba (sección 12).

**Comprobaciones**
- Funciones puras: `fondo_para` devuelve `fondo_inicial` / `fondo_final` / `fondo_regular` según `sala_inicial` y `sala_salida`
  (incluido el caso en que coinciden); `puertas_a_dibujar` devuelve `puerta_final` para la salida que lleva a `sala_salida`,
  `puerta_cerrada` para las demás cerradas y nada para las abiertas.
- Con el estado inicial real de `cripta-01` (sala 1, una antorcha en el suelo, una salida al norte abierta): `elemento_en` sobre la antorcha devuelve `objeto_suelo` 0.
- Tras mover al jugador a la sala de las ratas (real): hay 2 enemigos y `elemento_en` sobre cada uno devuelve `enemigo` 0 y 1.
- Con un estado construido a mano con una salida cerrada hacia `sala_salida`: se dibuja `puerta_final` y `elemento_en` sobre ella devuelve `puerta` con la dirección correcta (prueba N, S, E y O).
- **Clic real de punta a punta:** un clic sobre la antorcha recoge el objeto (el controlador real y los servicios reales);
  un clic sobre un enemigo produce un mensaje "Jugador ataca a …".
- Tamaños (medidos sobre lo que se dibuja): propios ≥ genérico > protagonista; protagonista fijo.
- Posición del protagonista: centro sin sala anterior; delante de la puerta correcta al entrar por N, S, E y O; centro si la anterior no es contigua; olvido tras el menú.
- Reparto: de 1 a 12 enemigos y objetos, sin solapes, dentro del suelo, sin tapar al protagonista ni las puertas; orden de dibujo = prioridad de zonas.
- Clics de punta a punta en el punto que da la función pura de reparto (no según el índice que registró la Vista).
- Aura en los objetos y no en los enemigos; sin etiquetas permanentes; nombre al pasar el ratón (`elemento_bajo_el_raton`).
- Capturas de: sala inicial, sala de las ratas, entrada por cada puerta, puertas cerradas, puerta final, muchos enemigos y objetos, y el nombre de un objeto. Revisa anclaje de los pies, escala, rotación de puertas y que nada salga de la pantalla.

**Hecho cuando:** pasan y el usuario aprueba las capturas.

### Etapa 7 — HUD: estadísticas, mensajes, inventario, efectos, botón y ayuda

**Como quedó (medidas en `View/Componentes.py`, sección HUD; contenido en `View/HudJuego.py`):** columna izquierda: estadísticas
(8, 8, 264×128), efectos (8, 144, 264×148) y mensajes (8, 470, **350**×290, 20 líneas, fuente 17 elegida por medida); columna
derecha: inventario (1104, 8, 264×284, 10 casillas de 46 px en 2 filas) y, abajo, Esperar, aviso y ayuda (x 1028–1368, ayuda en
fuente 20 elegida por medida). `SUELO` no se reduce: los paneles que lo pisan (mensajes y el grupo de abajo a la derecha) entran en
`ocupadas` de `repartir_escena`. Los tramos y 296–470 de las bandas laterales quedan libres. Orden: escena, velos, HUD, botón,
aviso, ayuda y, por último, el nombre del objeto bajo el ratón (`EscenaJuego.dibujar_nombre`). La pausa dibuja la escena sin HUD.

**Objetivo:** todo lo demás que exige §10.2 durante la partida.

**Archivos:** `View/HudJuego.py`; `tests/test_vista_hud.py`.

**Pasos:** según 7.3 y 6.5 (velos y líneas de efectos; barras; panel de mensajes con capacidad para 20 líneas; inventario con
casillas, cursor, marca de equipado, criterio, contador y detalle del objeto bajo el cursor; botón `Esperar`; `aviso`; `ayuda`).

**Comprobaciones**
- Funciones puras: `efectos_a_mostrar` da el texto y el color correctos para `veneno`, `velocidad` positiva, `velocidad` negativa, `antorcha` y un tipo desconocido (sin velo).
- Equipado: con `arma_equipada` apuntando a un id repetido, se marca **solo el primero**.
- Zonas: con un inventario de 3 objetos, `elemento_en` sobre cada casilla ocupada devuelve `inventario` 0, 1 y 2, y sobre una casilla vacía devuelve `None`; el botón `Esperar` devuelve `boton` 0.
- Los **20 mensajes** de un estado con 20 líneas se dibujan completos (prueba que el panel tiene capacidad para 20).
- **Punta a punta con el controlador real y servicios reales:** recoger la antorcha con un clic y comprobar que aparece en el inventario; doble clic sobre su casilla la usa y aparece el efecto `antorcha` (línea de texto + velo); `V` cambia el criterio y se ve en el panel; clic en `Esperar` avanza el reloj.
- Capturas: estado inicial, con objetos en el inventario y un efecto activo, y con el panel de mensajes lleno.

**Hecho cuando:** pasan y el usuario aprueba las capturas.

### Etapa 8 — Integración final: `main.py` y partida completa

**Objetivo:** que el juego se pueda jugar de punta a punta con `python main.py`, y que `--bench` y `--replay` sigan sin pygame.

**Usa:** `UIController/LectorArgumentos.py` (`leer_argumentos`, `ErrorArgumentos`, `TEXTO_AYUDA`); `UIController/ControladorBackend.py`
(`ControladorBackend`, `ErrorOperacion`, y sus métodos `medir`, `tabla_mediciones`, `reproducir`); `ControladorPygame`.

**Archivos:** `main.py` (reemplaza el "¡Hola!"); `tests/test_main.py`.

**Comportamiento de `main.py`** (no es un rediseño: es el cableado que ya está previsto en los docstrings de los controladores)

| Modo | Qué hace | Código de salida |
|---|---|---|
| opciones inválidas | imprime el error y `TEXTO_AYUDA` | 2 |
| `--ayuda` | imprime `TEXTO_AYUDA` | 0 |
| `--bench` | `ControladorBackend(config).medir(...)` con avance por grupos y luego `tabla_mediciones(...)` | 0 (1 si hay `ErrorOperacion`) |
| `--replay ARCHIVO` | `ControladorBackend(config).reproducir(ARCHIVO, ...)`: una línea por acción reproducida y un resumen (cripta, versiones, semilla, acciones, resultado) | 0 (1 si hay `ErrorOperacion`) |
| (ninguno) | importa `ControladorPygame` y `View.VistaPygame` **dentro de una función** y ejecuta `ControladorPygame(VistaPygame(...), config).ejecutar()` | 0 |

Si falta un módulo en el modo interactivo (`ModuleNotFoundError`), imprime "No se puede abrir la interfaz gráfica: falta
el módulo '…'" (y, si es `pygame`, "Instálalo con: uv add pygame-ce") y sale con 1. Esa importación perezosa es lo que hace
que `--bench` y `--replay` no importen pygame (§6).

**Comprobaciones**
- Casos de `main.main([...])` capturando la salida: `--ayuda` (0), `--cache-size abc` (2), `--replay` inexistente (1).
- **`--replay` sin pygame:** en un intérprete limpio, `main.main([...,"--replay", log])` termina con 0 y `"pygame" in sys.modules` es `False`
  (el log se genera jugando una partida corta con servicios reales y carpetas temporales).
- `--bench` no importa pygame (comprobación equivalente; el bench tarda varios segundos).
- **Partida completa con la Vista real** (`SDL_VIDEODRIVER=dummy`) y eventos simulados: menú → criptas → nombre → mover → recoger → atacar → pausa → guardar → cargar → perder → botones del fin → salir. Sin excepciones.
- **Prueba manual del usuario** (no automatizable): `python main.py --offline` con ventana real. Pídele que compruebe que
  **los clics caen donde se ven** (por `SCALED`), que la ventana se puede redimensionar y que `Esc`/`X` cierran sin error.

**Hecho cuando:** las pruebas pasan y el usuario confirma la prueba manual.

### Etapa 9 — Animaciones (OPCIONAL: confirma con el usuario antes de empezar)

**Objetivo:** animar con los fotogramas que ya existen. Nada de esto es necesario para cumplir el enunciado.

**Mínimo:** `idle` en bucle (por tiempo, con `pygame.time.get_ticks()`; unos 6 fotogramas por segundo) para jugador y enemigos.

**Propuesta para `ataque` (a confirmar con el usuario):** la Vista no recibe eventos de combate; sí recibe `estado.mensajes`
con líneas como `"[t=150] Jugador ataca a Rata gigante #1: 7 de daño"`, y `ActorDTO.nombre` coincide con el nombre de esas
líneas. Se pueden detectar las líneas **nuevas** entre dos cuadros consecutivos y reproducir `ataque` en el actor que
ataca. Es frágil (depende del texto del mensaje): si el usuario la rechaza, déjalo en `idle`.

**No usar:** `caminar` (no hay posiciones dentro de una sala) ni `*_direccion_*`.

**Comprobaciones:** la selección de fotograma es una función pura del tiempo (`fotograma(n_fotogramas, ms)`); pruébala. Captura
dos instantes distintos y comprueba que cambian.

### Etapa 10 — Cierre

1. Regresión completa: la sección 2.3 más todas las pruebas nuevas de la Vista y `tests/test_main.py`.
2. `README.md`: ver abajo qué agregar (el README actual solo tiene un título).
3. Limpieza: sin `__pycache__`, `capturas/` ignorada, `View/prueba.txt` borrado, sin archivos de depuración.
4. Recuerda al usuario que debe **anotar en `PROMPTS_LLM.md`** los prompts de esta sesión (§10.3 del enunciado: fecha,
   herramienta, prompt textual y para qué se usó). **No lo hagas tú.**

**Qué agregar al README (§10.1 del enunciado):** versión de Python (≥ 3.14), dependencias (`requests`, `pygame-ce`),
instalación (`uv sync`), comandos (`python main.py`, `--offline`, `--cache-size N`, `--replay ARCHIVO`, `--bench`),
controles (resumen de `ControlesJuego.AYUDA_JUEGO`), y dónde se generan archivos (`cache/`, `logs/`, `saves/`).

---

## 10. Verificación

### 10.1 Qué se verifica y cómo

| Qué | Cómo |
|---|---|
| Lógica de decisión (qué sprite, qué fondo, qué zonas, qué efecto) | Funciones puras + pruebas `probar_*`. |
| Contrato con el Controlador | Vista real + `ControladorPygame` real + servicios reales + eventos simulados (`tests/ayudas_pygame.py`). |
| Aspecto visual | Capturas (10.3), revisadas por ti y aprobadas por el usuario. |
| Coordenadas del ratón con ventana real | Prueba manual del usuario (Etapa 8). |
| Capas y estructuras prohibidas | Prueba de higiene sobre el código fuente de `View/` (sin `dict`, `set`, `sorted`, `.sort(`; imports permitidos). |

### 10.2 Reglas de las pruebas

- Servicios **reales** y paquete **offline** del repositorio, con carpetas temporales (`tests/ayudas_controladores.crear_backend`
  y `tests/ayudas_pygame.crear_fabrica`). Nada se escribe en `cache/`, `logs/`, `saves/`.
- La ruta de guardado del controlador es `ControladorPygame.RUTA_GUARDADO`; las pruebas la sustituyen por una temporal.
- Las pruebas de zonas usan los **centros** de los rectángulos que la propia Vista registró, no coordenadas inventadas.
- No fijes en las pruebas datos de una cripta salvo los de `cripta-01` del paquete de pruebas, y léelos del paquete cuando puedas.

### 10.3 Capturas (para ver lo que dibujas)

Crea un script `tests/capturar_pantallas.py` (no es una prueba) que conduzca el controlador real con servicios reales y, tras
cada pantalla, guarde `pygame.image.save(superficie, "capturas/<nombre>.png")`. **Abre las imágenes y revísalas**: solapes,
texto cortado, tamaños, contraste, anclaje de los sprites, rotación de las puertas, recuadros de los fondos de fin.
`capturas/` está en `.gitignore`. Las capturas se pueden hacer con `SDL_VIDEODRIVER=dummy`.

### 10.4 Demostrar que las pruebas sirven (mutaciones)

Regla del equipo: para pruebas nuevas, **rompe piezas a propósito** y comprueba que alguna prueba falla (por ejemplo: cambiar
una regla de búsqueda, invertir la prioridad de las zonas, quitar el relleno de `sala_inicial`, cambiar el color de un efecto,
marcar todos como equipados). Hazlo sobre una **copia** del proyecto, un cambio cada vez, y restaura.

> **Trampa conocida:** Python reutiliza el código compilado de `__pycache__` si la fecha (al segundo) y el tamaño del
> archivo coinciden, y muchas mutaciones **no cambian el tamaño**. Eso produce resultados falsos. Ejecuta las pruebas
> con **`python -B`** (sin escribir bytecode) y borra los `__pycache__` de la copia antes de empezar. Comprueba además que las pruebas
> pasan **sin mutar** antes de la primera mutación.

---

## 11. Errores frecuentes

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| `pygame.error: video system not initialized` al cargar una imagen | `convert_alpha()` antes de crear la ventana | Carga y convierte **después** de `set_mode` (en `abrir`). |
| Los clics no caen donde se ven | Coordenadas en un espacio distinto al de las zonas | Dibujar y registrar zonas **en la resolución lógica**, con `pygame.SCALED`. Confirmar a mano (Etapa 8). |
| Aviso "no fast renderer available" en las pruebas | `SCALED` con el controlador de vídeo `dummy` | Inofensivo. |
| Errores de ALSA / audio al iniciar | Se usó `pygame.init()` | Usar `pygame.display.init()` + `pygame.font.init()`. |
| Los pies de los personajes "saltan" entre fotogramas | Anclaje por el borde del lienzo | Anclar por `get_bounding_rect()` (6.4). |
| Los personajes se ven borrosos | `smoothscale` en pixel art | Usar `scale`. |
| Una puerta mira hacia el lado equivocado | Sentido de `rotate` | `rotate` gira en sentido **antihorario** (6.4). |
| Se acumulan zonas de cuadros anteriores | No se limpió la lista de zonas | Limpiar al **inicio** de cada `dibujar`. |
| Un sprite que no existe rompe el juego | Falta el respaldo | Siempre terminar en la figura dibujada (6.3). |
| Texto con `?` o cuadros en lugar de tildes | Fuente sin esos glifos | La fuente por defecto sí los tiene (comprobado); si se cambia, verificarlo. |
| Mantener una tecla repite acciones | Se activó `set_repeat` | No activarlo (3.3). |
| La prueba pasa aunque el código esté roto | Bytecode antiguo en `__pycache__` | `python -B` y limpiar caché (10.4). |
| El título del menú sale duplicado | Se dibujó `pantalla.titulo` sobre `fondo_menu` | No dibujarlo en el menú (6.6). |

---

## 12. Decisiones abiertas (pregúntalas al usuario; no decidas tú)

| # | Decisión | Recomendación |
|---|---|---|
| 1 | ¿Mover `Assets/assets/` a `assets/` en la raíz? | Sí, para coincidir con el `LEEME.md` (con Git en Windows, un cambio solo de mayúsculas requiere `git mv` en dos pasos). |
| 2 | Resolución lógica y comportamiento de la ventana | `1376×768` (tamaño nativo de los fondos), `SCALED \| RESIZABLE`. |
| 3 | ¿Oscurecer con código los marcos de puerta de las direcciones **sin** salida? | Sí; sin sprites nuevos. |
| 4 | ¿Dónde y cómo mostrar `ayuda` (11 líneas) durante la partida? | Panel compacto y discreto; decidir con capturas. |
| 5 | Disposición del HUD, del inventario y de los mensajes | Decidir con capturas por etapa. |
| 6 | ¿Hacer la Etapa 9 (animaciones) y cómo disparar `ataque`? | Solo si sobra tiempo; la propuesta de los mensajes es frágil. |
| 7 | ¿Cómo mostrar un objeto del suelo: nombre siempre o solo al pasar el ratón? | **Decidido (Etapa 6):** aura permanente y nombre solo al pasar el ratón. Antes se probó una etiqueta siempre visible. |

---

## 13. Checklist final de aceptación (enunciado §10.2 y §5.1)

Cada punto debe poder hacerse **desde la interfaz**, sin consola:

| Requisito | Cómo se cumple |
|---|---|
| Seleccionar una cripta e iniciar una partida | Menú → `Comenzar juego` → cripta → nombre → `Aceptar` |
| Moverse en las cuatro direcciones | `W A S D` / flechas |
| Abrir una puerta cuando corresponda | `E` o clic sobre la puerta cerrada |
| Atacar un enemigo seleccionado | Clic sobre el enemigo, o `Espacio` (objetivo resaltado) |
| Esperar | `Z` o botón `Esperar` |
| Recoger, usar, equipar y soltar | Clic en el suelo · `U` o doble clic · `Q` o clic derecho · `G` o Mayús+clic |
| Recorrer el inventario, con vistas ordenadas | Rueda o `Tab`; `V` cambia el orden (el criterio se ve en el panel) |
| Usar un pergamino de retroceso | `Backspace` o `Ctrl+Z` |
| Guardar y cargar la partida | `Ctrl+S`/`F5` y `Ctrl+L`/`F9`, o los botones de la pausa |
| Terminar la sesión de forma controlada | `Salir` del menú, `Salir al menú` de la pausa, o cerrar la ventana |
| La vista muestra: sala actual, salidas, enemigos, objetos del suelo, vida y estadísticas, efectos y los últimos 20 mensajes | Sección 7.3 |
| Al terminar, el reporte de solicitudes, presupuesto y caché (§5.1) y la tabla de puntajes (§2.12) | Secciones 7.1 y 7.2 |
| `--replay` y `--bench` corren sin pygame (§6) | Etapa 8 |

---

## Anexo A — Primera instrucción sugerida para Claude Code

```
Lee GUIA_VISTA_PYGAME.md completa. Vamos a implementar la Vista de Pygame por etapas, sin rediseñar nada.
Empieza SOLO por la Etapa 0: verifica el estado del repositorio y del entorno, ejecuta la línea base de pruebas
y hazme las preguntas que la etapa indica. Al terminar, dame el informe de la sección 0.2 y espera mi OK
antes de pasar a la Etapa 1.
```
