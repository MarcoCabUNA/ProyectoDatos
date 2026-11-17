# Crypta

**Integrantes:**
- Kristel Peraza Sánchez
- Derek García Herra
- Marco Cabrera Mora

Juego de exploración por eventos para el Primer Proyecto de Estructuras de Datos (UNA, II ciclo 2026).
El cliente obtiene la cripta desde el servicio web (o desde un paquete local con `--offline`), simula la partida
con un reloj virtual y guarda partidas, puntajes y bitácoras de replay en disco.

## Requisitos

- **Python 3.11 o superior** (lo exige `pyproject.toml`; probado con 3.11 y 3.14).
- Dependencias:
  - `requests`: acceso al servicio web (`Data/ClienteHttp.py`).
  - `pygame-ce`: interfaz gráfica (solo para jugar; `--replay` y `--bench` no lo necesitan).
  - Ambas están en `requirements.txt` (y en `pyproject.toml`).
- **No hace falta `uv`**: es opcional. Solo se necesita Python y `pip`, que vienen con Python.

## Instalación

Desde la raíz del proyecto (la carpeta donde está `main.py`). Se crea un entorno virtual `.venv` y se instalan las dos
dependencias. **No hace falta activar el entorno**: los comandos de este README llaman directamente al Python del entorno
(así tampoco molesta la política de scripts de PowerShell).

**Windows (PowerShell)**

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**Linux / macOS**

```
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Para comprobar que quedó bien (debe mostrar las opciones y no dar error):

| Windows (PowerShell) | Linux / macOS |
|---|---|
| `.venv\Scripts\python.exe main.py --ayuda` | `.venv/bin/python main.py --ayuda` |

**Alternativa con uv** (opcional; instala las mismas versiones de `uv.lock`): `uv sync`, y después cada comando de abajo
se escribe como `uv run python main.py ...`.

### Si algo falla

- *`python` no se reconoce* (Windows): prueba `py -m venv .venv`, o instala Python 3.11 o superior desde python.org
  marcando "Add python.exe to PATH".
- *`uv` no se reconoce*: no se necesita. Usa los comandos de Windows o de Linux / macOS de este README.
- *PowerShell no deja activar el entorno*: no hace falta activarlo; usa `.venv\Scripts\python.exe`.
- Si ya activaste el entorno (`.venv\Scripts\Activate.ps1` o `source .venv/bin/activate`), basta con escribir
  `python main.py ...` en lugar de la ruta completa.

## Cómo ejecutar

| Qué hace | Windows (PowerShell) | Linux / macOS |
|---|---|---|
| Abre el juego conectado al servicio web. | `.venv\Scripts\python.exe main.py` | `.venv/bin/python main.py` |
| Abre el juego con el paquete local de `paquete/`, sin usar la red. | `.venv\Scripts\python.exe main.py --offline` | `.venv/bin/python main.py --offline` |
| Cambia el tope de fichas del catálogo en memoria (entero mayor o igual a 1; por defecto 25). Se puede combinar con los demás modos. | `.venv\Scripts\python.exe main.py --cache-size 10` | `.venv/bin/python main.py --cache-size 10` |
| Reproduce una partida desde su bitácora, sin abrir la ventana, y muestra cada acción y el resultado final. | `.venv\Scripts\python.exe main.py --replay logs/partida_001.log --offline` | `.venv/bin/python main.py --replay logs/partida_001.log --offline` |
| Reproduce la partida solo hasta el instante `T` (entero mayor o igual a 0) y muestra el resumen del estado en ese instante, sin abrir la ventana. Solo se acepta junto con `--replay`. | `.venv\Scripts\python.exe main.py --replay logs/partida_001.log --hasta 300 --offline` | `.venv/bin/python main.py --replay logs/partida_001.log --hasta 300 --offline` |
| Cambia cada cuántas acciones del jugador la línea de tiempo toma un punto de control (entero mayor o igual a 1; por defecto 20). Se puede combinar con los demás modos. | `.venv\Scripts\python.exe main.py --checkpoint-cada 50` | `.venv/bin/python main.py --checkpoint-cada 50` |
| Corre las mediciones de rendimiento con cargas sintéticas, sin abrir la ventana, y muestra una tabla por subsistema. | `.venv\Scripts\python.exe main.py --bench` | `.venv/bin/python main.py --bench` |
| Muestra las opciones. | `.venv\Scripts\python.exe main.py --ayuda` | `.venv/bin/python main.py --ayuda` |

`--replay` y `--bench` no se pueden usar juntos. Con uv, cada comando se escribe `uv run python main.py ...`.

**Sobre `--replay`:** `logs/` está vacía en una copia nueva del repositorio (se llena al jugar). Para probarlo sin jugar
antes, el repositorio incluye una partida de muestra hecha con el paquete local:
`... main.py --replay ejemplos/partida_ejemplo.log --offline`. Sin `--offline`, el replay pide la cripta al servicio web
(y cuenta como solicitudes de red); con `--offline` la lee de `paquete/`.

**Nota sobre `--bench`:** la tabla es larga. La terminal integrada de PyCharm puede no mostrarla completa; en una terminal
normal sale entera. Para guardarla en un archivo:

| Windows (PowerShell) | Linux / macOS |
|---|---|
| `.venv\Scripts\python.exe main.py --bench \| Out-File -Encoding utf8 bench.txt` | `.venv/bin/python main.py --bench > bench.txt` |

### Controles

En los menús: flechas o ratón para elegir, `Enter` o clic para aceptar, `Esc` para volver.

Durante la partida (el inventario está siempre visible; la ventana muestra este resumen abajo a la derecha):

| Acción | Teclado | Ratón |
|---|---|---|
| Moverse | `W A S D` o flechas | |
| Atacar | `Espacio` (ataca al enemigo resaltado) | clic sobre el enemigo |
| Recoger | | clic sobre el objeto del suelo |
| Abrir una puerta | `E` | clic sobre la puerta cerrada |
| Esperar | `Z` | botón `Esperar` |
| Recorrer el inventario | `Tab` (`Mayús + Tab` hacia atrás) | rueda, o clic en una casilla |
| Usar | `U` | doble clic sobre la casilla |
| Equipar | `Q` | clic derecho sobre la casilla |
| Soltar | `G` | `Mayús` + clic sobre la casilla |
| Cambiar la vista del inventario | `V` (real, peso, valor, nombre; el orden real no cambia) | |
| Pergamino de retroceso | `Retroceso` o `Ctrl + Z` | |
| Abrir la línea de comandos (`historia`, `mapa`, `ir a`) | `Enter` (acepta con `Enter`, se cierra con `Esc`) | |
| Guardar / Cargar | `Ctrl + S` o `F5` / `Ctrl + L` o `F9` | botones de la pausa |
| Pausa | `Esc` (Continuar, Guardar, Cargar, Salir al menú) | |

Para salir: `Salir` en el menú principal, `Salir al menú` en la pausa, o cerrar la ventana.

### Línea de comandos: `historia`, `mapa` e `ir a`

`Enter` abre la línea de comandos (un campo de texto abajo en la ventana), `Enter` ejecuta lo escrito y `Esc` la cierra
sin pausar el juego. Mientras está abierta, las teclas del juego se escriben en la línea y no actúan.

| Comando | Qué hace |
|---|---|
| `historia <t>` | Muestra el estado en el instante `t` (entero mayor o igual a 0, hasta el reloj actual). |
| `historia #k` | Muestra el estado justo antes de la acción `k` del jugador (entero mayor o igual a 1, hasta las acciones hechas). |
| `mapa` | Abre o cierra el mapa de lo que el jugador conoce. |
| `ir a <sala>` | Lleva al jugador a una sala que ya exploró, paso a paso. |

Un comando que no se entiende deja un aviso de uso y no hace nada. Ejemplos: `historia 300`, `historia #4`, `mapa`,
`ir a Pasillo de las urnas`.

**`historia`.** El resultado aparece en un panel de solo lectura con el reloj, la sala, la vida y las estadísticas del
jugador, el inventario (con el arma y la armadura equipadas), los efectos activos y los enemigos de la sala. `Esc` cierra el
panel y el juego sigue tal cual estaba. Una consulta no consume tiempo, no cuenta como acción y no se escribe en la
bitácora. Si el número está fuera de rango, la línea muestra un aviso con el rango válido. Sin abrir la ventana, el mismo
resumen sale de `--replay ARCHIVO --hasta T` (ver «Modo `--replay`»).

La línea de tiempo toma un punto de control cada 20 acciones (se cambia con `--checkpoint-cada N`, entero mayor o igual a
1; por ejemplo `main.py --checkpoint-cada 50`): una consulta nunca re-simula más de `N` acciones. El valor por defecto
salió de `--bench` (con 5 000 acciones, `historia` tarda menos de 1 ms; ver `DECISIONES.md`).

**`mapa`.** Dibuja un panel con las salas exploradas (con su nombre y el costo de cada salida cuando hay espacio), cada salida hacia una
sala avistada como un hueco «sin explorar» (sin nombre ni número), la sala donde estás en dorado y cada puerta con el
estado en que la viste por última vez: verde abierta, roja cerrada, gris sin observar. Una puerta que se cerró sola
mientras estabas lejos sigue figurando abierta hasta que vuelvas a verla. Si el mapa no cabe, se recorta alrededor de tu
sala y el panel lo avisa. Se cierra con `mapa` otra vez, con `Esc` o al hacer cualquier acción. No consume tiempo, no
cuenta como acción y no se escribe en la bitácora. Con la partida terminada no está disponible (igual que `historia`).

**`ir a <sala>`.** El destino debe ser una sala ya explorada; mayúsculas y espacios sobrantes no importan, pero las tildes
sí (`sotano` no encuentra `Sótano`). El viaje elige la ruta de menor costo usando solo lo que el mapa recuerda (salas
exploradas y puertas recordadas abiertas), no abre puertas aunque tengas la llave, y da un paso cada 350 ms para que se
vea cómo cambias de sala. Cada paso es un movimiento normal: gasta su tiempo, deja pasar los eventos y cuenta como acción.

- *Cuándo para.* Cuando llegas, cuando entras a una sala con enemigos (activos o dormidos), cuando recibes daño de cualquier
  origen, o cuando ya no hay una ruta conocida (por ejemplo, vuelves a ver una puerta de tu ruta cerrada y no hay otra).
  El motivo, o todos si coinciden varios, aparece en el panel de mensajes («Llegaste a ...», «Viaje detenido: hay
  enemigos.», «...recibiste daño.», «...sin ruta conocida a ...»).
- *Cómo se corta.* Pulsando cualquier tecla o haciendo clic: el viaje se corta («Viaje interrumpido.») y la orden se
  ejecuta (por ejemplo `Z` espera). `Esc` solo corta el viaje y no abre la pausa. Un pergamino de retroceso revierte únicamente
  el último paso y el viaje no continúa.
- *Si se rechaza.* Una sala no explorada, desconocida o que no existe da el mismo aviso (no revela si existe); un nombre que
  designa varias salas exploradas, o la sala donde ya estás, tienen su propio aviso. No gastan tiempo ni quedan en la bitácora.
- *En la bitácora.* Cada paso se escribe como un movimiento más, y la orden como un comentario (`# ir a Pasillo de las
  urnas`) justo después del primer paso. `--replay` repite los pasos y llega a la misma partida; el comentario no cambia nada.

### Modo `--offline`

Lee las criptas desde la carpeta `paquete/`, que viene en el repositorio con las cuatro publicadas al 18 de octubre
(`cripta-01` a `cripta-04`, de 6 a 50 salas). Las lecturas locales no cuentan como solicitudes de red, así que el
reporte final muestra 0 solicitudes.

Para agregar o actualizar una cripta en el paquete (esto sí usa la red; el catálogo se comparte entre criptas y se
completa con las fichas nuevas):

```
.venv\Scripts\python.exe -m Data.DescargadorPaquete <id-de-la-cripta>        (Windows)
.venv/bin/python -m Data.DescargadorPaquete <id-de-la-cripta>             (Linux / macOS)
```

### Modo `--replay`

Cada partida escribe su bitácora en `logs/` mientras se juega: un encabezado (cripta, versión de la cripta,
versión del catálogo y semilla) y una línea por cada acción del jugador. `--replay` vuelve a ejecutar esas acciones
con la misma semilla y llega al mismo resultado. Si la versión de la cripta o del catálogo no coincide con la
disponible, se informa la incompatibilidad y no se reproduce. Si la última línea quedó a medio escribir (por
ejemplo, porque el programa se cerró), se ignora y se avisa.

Con `--hasta T` el replay no recorre la partida mostrando cada acción: la reproduce hasta el instante `T` y
imprime el resumen de ese estado (el mismo que muestra `historia T` durante la partida). Si `T` es posterior al final de
la partida, muestra el estado final y avisa que la partida terminó antes. Sin `--hasta`, `--replay` reproduce la partida
completa. Códigos de salida de `--replay ... --hasta`:

| Código | Cuándo |
|---|---|
| 0 | Imprimió el resumen. |
| 1 | No se pudo reproducir: el log no existe o no se puede leer, o la versión de la cripta o del catálogo no coincide. El mensaje dice por qué. |
| 2 | Error en las opciones: `--hasta` sin valor, negativo o que no es un entero, o usado sin `--replay`. |

Al cargar una partida guardada, la bitácora continúa en un archivo nuevo que incluye las acciones anteriores,
así que ese log también se puede reproducir completo.

## Archivos que genera el programa

Ninguna de estas carpetas se sube al repositorio (están en `.gitignore`). Se crean solas al usarse.

| Ubicación | Contenido |
|---|---|
| `cache/catalogo/` | Caché del catálogo en disco: una ficha por archivo, dentro de una carpeta por versión del catálogo. Cuando el catálogo cambia de versión, la anterior se borra. |
| `saves/partida.sav` | La partida guardada (formato binario propio). |
| `saves/puntajes.jsonl` | Los puntajes: una línea por partida terminada. |
| `logs/partida_NNN.log` | Bitácora de cada partida para `--replay` (`partida_001.log`, `partida_002.log`, ...). |
| `saves/bench_tmp/` | Archivos temporales de `--bench`; se borran al terminar. |

## Pruebas

Para correr todas de una vez (no abre ventanas; termina con código 0 si todo pasa):

```
uv run python tests/correr_pruebas.py
```

En Windows hay que pedirle a Python que escriba en UTF-8; si no, el script se cae al imprimir un carácter que la
consola no puede mostrar (no es una prueba que falle):

```
PYTHONIOENCODING=utf-8 uv run python tests/correr_pruebas.py                (Git Bash)
$env:PYTHONIOENCODING = "utf-8"; uv run python tests/correr_pruebas.py      (PowerShell)
```

Sin uv, con el entorno virtual ya creado:

```
.venv\Scripts\python.exe tests/correr_pruebas.py        (Windows)
.venv/bin/python tests/correr_pruebas.py             (Linux / macOS)
```

Hay dos tipos de pruebas, y el script corre los dos:

- **De `unittest`** (`tests/Test*.py` y algunos `tests/test_*.py`):
  `.venv\Scripts\python.exe -m unittest discover -s tests -p "[Tt]est*.py"` (en Linux / macOS, `.venv/bin/python ...`).
- **Scripts `probar_*`** (el resto de `tests/test_*.py`: Servicios, controladores, Vista...). `unittest discover` no los
  encuentra; cada uno se corre por separado y termina con una línea `OK: ...`, por ejemplo
  `.venv\Scripts\python.exe tests/test_servicios.py`.

Las pruebas de la Vista necesitan `pygame-ce`. Los scripts `tests/capturar_*.py` no son pruebas: guardan capturas de
pantalla en `capturas/` para revisarlas a ojo.

## Documentación

- `PROMPTS_LLM.md`: bitácora de uso de modelos de lenguaje.
- `docs/Documento_Decisiones.pdf`: Documento de Decisiones de Diseño (§8).