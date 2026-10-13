# PROMPTS

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Sábado 4 de octubre 2026

**Herramienta:** Claude

Explícame de manera clara y sencilla el uso de la librería `dataclasses` de Python y el decorador `@dataclass`
Quiero que la explicación incluya:

* ¿Qué es `dataclass` y para qué sirve?
* ¿Cuándo es buena opción utilizarla y cuándo no sería necesario?
* ¿Qué ventajas tiene frente a una clase tradicional?
* ¿Qué es `field()` y para qué se utiliza?
* Explica especialmente la diferencia entre `default` y `default_factory`, con un ejemplo sencillo
* ¿Qué significa `frozen=True` y para qué sirve?
* Explica brevemente qué ocurre si un `dataclass` congelado contiene objetos mutables como listas
* Incluye un ejemplo práctico que utilice `@dataclass`, `field()` y `frozen=True`, explicando el código paso a paso

Utiliza ejemplos sencillos y un lenguaje didáctico, como si me estuvieras enseñando el tema desde cero

**Uso de la respuesta:** se utilizó para aprender sobre esta librería, que facilita la implementación de la capa de DTO del proyecto.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 7 de octubre 2026

**Herramienta:** Claude (Claude Code)

Haz tests básicos para probar lo que es la parte de lógica de este proyecto, luego de ello dame una tabla con lo que encontraste

**Uso de la respuesta:** se generó `tests/test_logica.py` (60 pruebas con `unittest`) para la capa `Logica`. Las pruebas detectaron 6 errores (campo `dano` en vez de `danio` en trampas, desempaquetado de DTOs como tuplas, turno extra con poción de velocidad, salas sin esqueleto cargado y daño negativo que curaba) e imports inconsistentes. Se corrigieron con cambios mínimos.


-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 9 de octubre 2026

**Herramienta:** Claude

Pruebas unitarias de la capa de datos (Integrante 2) para verificar todo lo implementado: ClienteHttp, Cola, DTOs, FuenteRed, FuenteOffline, DescargadorPaquete, GestorEsqueleto y GestorContenido.

**Uso de la respuesta:** se generaron 8 archivos de prueba en `tests/` (82 pruebas con `unittest`) más `tests/Utilidades.py` (datos reales del paquete de cripta-01 y una API falsa para no usar la red). Las pruebas cubren 429 y presupuesto, encabezado X-Cripta-Client-Id, lotes de 10, paquete offline, validaciones del esqueleto y orden determinista de la precarga. Durante el proceso se corrigió una prueba de fallo a mitad de descarga (la solicitud que fallaba era la del catálogo reutilizado) y se ajustaron las pruebas a los nombres de campo finales de los DTOs.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 9 de octubre 2026

**Herramienta:** Claude

Caché del catálogo en memoria (§4.4) usando solo arrays y la ListaDoble compartida: tope configurable, desalojo justificado y fichas en uso que no se pueden liberar.

**Uso de la respuesta:** se generó `Data/CacheCatalogo.py`: array ordenado por id con búsqueda binaria O(log n) para consultar, y la `ListaDoble` de Kristel (sin modificarla) para el desalojo LRU en O(1) con solo las fichas que no están en uso. Contadores de usos para `marcar_en_uso`/`liberar_uso` y de aciertos/fallos para el reporte. Se agregó `tests/TestCacheCatalogo.py` (16 pruebas, incluida una comparación contra un modelo simple con operaciones al azar).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 9 de octubre 2026

**Herramienta:** Claude

Caché del catálogo en disco (§4.4): persistir cada ficha, validarla con la versión del catálogo y recuperarla con una lectura de disco en vez de una solicitud de red.

**Uso de la respuesta:** se generó `Data/AlmacenCatalogo.py` (un archivo JSON por ficha dentro de una carpeta por versión de catálogo; descarta versiones viejas, escritura segura con .tmp, archivos dañados se borran sin detener el juego). En `Security/ValidadorAcceso.py` se agregaron `validar_version` y `es_nombre_seguro`. `FuenteJson.ficha_desde_diccionario` pasó a ser pública para reutilizar la traducción. Se agregó `.gitignore` y 14 pruebas (`tests/TestAlmacenCatalogo.py` y 2 en `tests/TestClienteHttp.py`).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Sábado 10 de octubre 2026

**Herramienta:** Claude

Resolución de referencias del catálogo (§4.3): resolver cada id de tipo antes de mostrar o simular, en lotes de hasta 10, sin pedir dos veces lo que ya está en memoria o en disco.

**Uso de la respuesta:** se generó `Data/ResolvedorCatalogo.py` (memoria -> disco -> red, ids repetidos eliminados, lotes de 10 con la Cola compartida, resolución de lo que sueltan los enemigos, `ficha(id)` que nunca devuelve None para `Mazmorra.cargar_contenido`, y `marcar_en_uso`/`liberar_uso`). `GestorContenido` recibe el resolvedor como parámetro opcional y resuelve el catálogo de cada lote de contenido apenas llega. Se agregó `tests/TestResolvedorCatalogo.py` (20 pruebas, incluida la cripta real completa en 6 solicitudes con presupuesto 9).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Lunes 12 de octubre 2026

**Herramienta:** Claude (Claude Code)

**Uso de la respuesta:** 

Compatibilidad del guardado:
* Con `Data/GuardadoBinario.py`: lo que devuelve `guardar` es exactamente lo que recibe `GuardadoBinario.guardar(ruta, partida, salas)`, y lo que entregan `GuardadoBinario.cargar` y `cargar_salas` es lo que recibe `cargar`. Se probó la ida y vuelta por el archivo binario.
* Con los acuerdos del equipo del 10 y 11 de octubre: solo se guardan los eventos válidos y su dueño va como referencia (actor; posición del efecto; sala + trampa; sala + dirección). El equipo se guarda por posición en el inventario (dos dagas iguales funcionan) y `Jugador.arma`/`armadura` se llenan desde el inventario al cargar. El historial de retroceso no se guarda: la partida cargada empieza sin acciones para deshacer, pero el retroceso funciona desde la primera acción.
* Determinismo: se restauran el estado del azar y la secuencia de cada evento, y los eventos se guardan en el orden en que saldrían de la cola, así que la partida cargada continúa exactamente igual que la original.
* Con Servicios (Integrante 3): `ServicioGuardado` (todavía vacío) arma el `ContextoPartida` con `motor.jugador`, `motor.mazmorra` y `motor.inventario`.
* Cambio en `Logic/Inventario.py` (Integrante 3): se agregaron `posiciones_equipadas()` y `restaurar(...)`, porque el inventario recuerda el equipo por nodo (privado) y no había forma pública de guardarlo y restaurarlo por posición. No se cambió ningún método existente.
* `PartidaGuardada` reutiliza dos métodos privados en vez de copiarlos: `Motor._registrar_azar()` y `Mazmorra._salida_inversa()`.

Se agregó `tests/test_partida_guardada.py` (8 pruebas): guardar → cargar → guardar da lo mismo (en memoria y por el archivo binario); la partida cargada y la original, con las mismas 12 acciones, dan los mismos mensajes y el mismo estado final; y el retroceso funciona después de cargar. Para comprobar que las pruebas detectan errores, se rompieron a propósito seis líneas clave de la carga, una a la vez, y cada cambio hizo fallar al menos una prueba.

Pruebas del proyecto completo:
* Actualizador de las pruebas: `discover` solo encontraba los archivos que empiezan con `test` en minúscula y se saltaba los 17 `Test*.py` (235 pruebas). El comando en los encabezados de `tests/test_logica.py` y `tests/test_partida_guardada.py` pasó a ser `python3 -m unittest discover -s tests -p "*.py" -v` (usar `.venv/bin/python`): ahora corre 303 pruebas, todas OK, sin renombrar archivos.
* Los 4 archivos de estilo script (`test_servicios`, `test_servicio_replay`, `test_servicio_puntajes`, `test_retroceso_completo`) no usan unittest y se corren aparte con `.venv/bin/python -m tests.<nombre>`; los 4 pasan.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Martes 13 de octubre 2026

**Herramienta:** Gemini

Necesito que reescales las imágenes que te voy a proporcionar para utilizarlas como fondos de las habitaciones de un videojuego que estoy desarrollando.

Requisitos:

Todas las imágenes deben tener exactamente las mismas dimensiones, con una resolución grande y buena calidad.
Utiliza un tamaño uniforme de 1920 × 1080 píxeles (Full HD) para todas las imágenes.
Mantén la apariencia, los colores, los detalles y el estilo artístico original de cada imagen.
Si alguna imagen tiene una resolución menor, aumenta su tamaño procurando conservar la nitidez y evitar pixelación.
Ajusta las imágenes para que encajen en las dimensiones indicadas sin deformar los elementos ni alterar su composición original.
No agregues, elimines ni modifiques elementos de las imágenes.
Devuelve cada imagen por separado, conservando su identidad y asegurándote de que todas tengan exactamente el mismo tamaño.

Estas imágenes se utilizarán como fondos de diferentes habitaciones del mismo videojuego, por lo que es fundamental que 
sus dimensiones sean consistentes para evitar cambios de tamaño o problemas de visualización al cambiar de habitación.

**Uso de la respuesta:** Se reescalaron las imágenes proporcionadas a un tamaño uniforme de 1920 × 1080 píxeles (Full HD) manteniendo la apariencia, colores, detalles y estilo artístico original de cada imagen. 
Se ajustaron las imágenes para que encajaran en las dimensiones indicadas sin deformar los elementos ni alterar su composición original. Todas las imágenes fueron devueltas por separado, conservando su identidad y asegurando que todas tengan exactamente el mismo tamaño, listas para ser utilizadas como fondos de las habitaciones del videojuego