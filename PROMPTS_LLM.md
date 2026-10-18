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

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Martes 13 de octubre 2026

**Herramienta:** Gemini

Quiero que, tomando como referencia la imagen adjunta, generes el resto de los sprites necesarios para mi videojuego.
Instrucciones:
- Analiza la imagen de referencia para identificar su estilo artístico, paleta de colores, iluminación, proporciones, perspectiva y nivel de detalle.
- Crea los sprites faltantes manteniendo una estética visual coherente con la imagen original.
- Conserva las dimensiones, proporciones y características visuales de los elementos para que puedan integrarse correctamente en el juego.
- Si se trata de escenarios o habitaciones, mantén la misma perspectiva, escala y estilo arquitectónico entre todas las áreas.
- Genera cada sprite con buena resolución, bordes definidos y sin deformaciones.
- Utiliza fondos transparentes cuando corresponda, especialmente para personajes, objetos y elementos individuales.
- Organiza los sprites de forma clara, preferiblemente en imágenes separadas por elemento o en una sprite sheet ordenada, según convenga.
- No modifiques ni reemplaces el diseño original de la referencia; úsalo como guía para crear contenido nuevo que combine con él.
Importante: Todos los sprites deben parecer parte del mismo videojuego. Prioriza la consistencia visual y la utilidad de los recursos dentro del juego por encima de añadir detalles que no aparecen en la referencia.
Antes de generar los sprites, identifica las características visuales que debes conservar y determina qué elementos adicionales hacen falta para completar el conjunto.

**Uso de la respuesta:** Se utilizó la respuesta para generar los sprites restantes basados en una imagen para las animaciones
de los personajes del juego

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Sábado 10 de octubre 2026

**Herramienta:** Claude

Kristel me pidió que la caché del catálogo siga bien después de usar el pergamino de retroceso. Ayúdame a resolverlo:

* ¿Qué pasa con las fichas marcadas como "en uso" cuando se revierten acciones?
* ¿Cómo vuelvo a dejar los usos iguales a lo que de verdad queda en la partida, sin liberar fichas que todavía se usan?
* Agrega las pruebas necesarias para comprobarlo

**Uso de la respuesta:** se agregaron `reiniciar_usos()` en `Data/CacheCatalogo.py` y `sincronizar_usos(ids_en_uso)` en `Data/ResolvedorCatalogo.py`, que recalculan las fichas en uso a partir de las que quedan en la partida y devuelven las que se liberaron. Se agregaron sus pruebas en `tests/TestCacheCatalogo.py` y `tests/TestResolvedorCatalogo.py`.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Sábado 10 de octubre 2026

**Herramienta:** Claude

Necesito terminar la parte de Datos que se ve al final de la partida y las banderas del programa:

* Un reporte con las solicitudes realizadas, el presupuesto de solicitudes y los aciertos y fallos de caché (§6.1)
* Leer `--offline`, `--cache-size`, `--replay` y `--bench` con `argparse`, sin que el modelo dependa de la línea de comandos
* Explícame qué combinaciones de banderas no deberían permitirse y por qué

**Uso de la respuesta:** se generaron `DTO/ReporteDatosDTO.py` y `Data/ReporteDatos.py` (junta en un DTO los contadores que ya llevan la fuente de datos, el resolvedor del catálogo y el gestor de contenido, sin hacer solicitudes), `DTO/ConfiguracionDTO.py` y `UIController/LectorArgumentos.py` (`--replay` y `--bench` son excluyentes y `--cache-size` debe ser un entero positivo), con sus pruebas `tests/TestReporteDatos.py` y `tests/TestLectorArgumentos.py`. Después del merge con la rama de Kristel se corrigieron los imports que apuntaban a `Logica` en vez de `Logic`.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Domingo 11 de octubre 2026

**Herramienta:** Claude

Sigamos con la bitácora de partida para `--replay` (§4.11). Quiero que:

* El archivo sea de texto y solo se le agreguen líneas al final, con un encabezado (cripta, versiones y semilla) y una acción por línea
* Si la última línea quedó incompleta porque el programa se cerró, se descarte sin dañar el resto
* Antes de reproducir se compruebe que las versiones sean compatibles y, si no lo son, se reporte en vez de continuar
* Si el jugador carga una partida guardada, el replay pueda seguir desde ese punto

**Uso de la respuesta:** se generaron `DTO/ReplayDTO.py` (`EncabezadoReplayDTO` y `PartidaReplayDTO`) y `Data/BitacoraReplayIO.py`: encabezado `#CRIPTA-REPLAY 1`, `anexar` que comprueba la ida y vuelta de cada acción antes de escribirla, `leer` que descarta la última línea si quedó incompleta, `comprobar_compatibilidad` que reporta las versiones incompatibles y `continuar_desde`, que copia las primeras N acciones del log anterior a un log nuevo para seguir el replay de una partida cargada. Pruebas en `tests/TestBitacoraReplayIO.py`.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Domingo 11 de octubre 2026

**Herramienta:** Claude

Vamos con el guardado de la partida en binario (§4.10). Antes de programarlo:

* Hazme una lista puntual de lo que necesito acordar con Marco y Kristel y si ocupo código de alguno de ellos
* Revisa si las recomendaciones que me diste son correctas y, si no lo son, corrígelas
* Dime si un índice de acceso directo es la mejor opción para cargar una sola sala sin leer todo el archivo

Cuando el equipo esté de acuerdo, implementa los DTOs del guardado y el formato binario.

**Uso de la respuesta:** se acordó con el equipo qué guarda la partida (todas las salas del esqueleto, solo los eventos válidos con su dueño como referencia, los efectos por su posición en la lista, el inventario por posiciones y el estado completo del azar). Se generaron `DTO/PartidaGuardadaDTO.py` (con `SalaGuardadaDTO` y los demás DTOs del guardado) y `Data/GuardadoBinario.py`: formato propio con `struct` (encabezado `CRPT`, bloque global, un bloque por sala e índice de acceso directo para cargar una sala en O(1)), escritura segura con `.tmp` + `os.replace` y `ErrorGuardado` ante cualquier archivo dañado. En la revisión se cambió el índice ordenado con búsqueda binaria por uno de acceso directo y se corrigieron dos recomendaciones que estaban mal (borrar `Jugador.arma` y cargar sala por sala). `saves/` y `logs/` se agregaron al `.gitignore`.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Domingo 11 y lunes 12 de octubre 2026

**Herramienta:** Claude

Analiza las imágenes con lo que Kristel me pidió para la capa de Servicios y dime:

* Qué archivos hay que cambiar y qué cambios lleva cada uno
* Qué es el almacén de puntajes y dónde debería guardarse
* Si en las imágenes también se habla de los aciertos de caché inflados
* Si todo lo implementado corresponde exactamente a lo que ella pidió

**Uso de la respuesta:** se agregaron `BitacoraReplayIO.ruta_libre` (siguiente nombre libre `partida_NNN.log` en una carpeta), el parámetro `contar_acierto` en `CacheCatalogo.obtener` y `ResolvedorCatalogo.ficha` (para que armar el estado de la Vista no cuente aciertos de caché) y `Data/AlmacenPuntajes.py` (agrega y lee puntajes en `saves/puntajes.jsonl`), con sus pruebas.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Lunes 12 de octubre 2026

**Herramienta:** Claude

Ahora el modo `--bench` (§5.3). Antes de empezar:

* ¿Hay algún problema en dejar la cola de eventos con un heap hecho por nosotros y no el de una librería?
* ¿Cómo se mide el guardado binario contra JSON?
* ¿Está correcto todo lo que hemos hecho desde el paso 1 hasta el paso 12?

Después propón cómo organizar las mediciones para que cada integrante tenga su propio archivo, sin tocar el código de los demás, y que todo corra sin la Vista.

**Uso de la respuesta:** se generaron `DTO/ResultadoBenchDTO.py`, `Service/Cronometro.py` (una ejecución de calentamiento y mejor y mediana de N repeticiones, ordenadas con el `Ordenador` del equipo), `Service/BenchDatos.py` (caché: búsqueda binaria contra la lineal descartada; fichas liberadas: memoria contra disco; precarga: lotes contra una solicitud por sala; guardado: binario contra JSON; bitácora: anexar y leer) y `Service/ServicioBench.py`, que junta las mediciones de los tres integrantes y las imprime como tabla. Pruebas en `tests/TestServicioBench.py`.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Martes 13 y miércoles 14 de octubre 2026

**Herramienta:** Claude

Kristel encontró que una prueba de `TestServicioBench.py` falla después de que ella y Marco agregaron sus mediciones. Analízalo y dime:

* Si lo que ella propone es correcto
* Si nuestro `Service/BenchLogica.py` lo usa alguien o se puede borrar sin problema
* Los pasos para arreglarlo sin echar a perder nada y sin tocar el código de ellos
* Si el ciclo de eventos de Marco con 500 enemigos que no cumple los 20 ms afecta mucho y si es obligatorio cambiarlo

**Uso de la respuesta:** `ServicioBench` usaba la plantilla vacía `Service/BenchLogica.py` en vez de `Logic/BenchLogica.py` (el de Marco), así que esas mediciones no se corrían aunque las pruebas pasaran. Se conectó el archivo correcto, se borró la plantilla y se quitó de `tests/TestServicioBench.py` la comprobación que exigía mediciones vacías. Con 500 enemigos el ciclo de eventos dio una mediana de 9.3 ms y un peor caso de 119 ms, y se le avisó a Marco.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Jueves 15 de octubre 2026

**Herramienta:** Claude

¿Cuántos enemigos debería tener el juego sin contar los comportamientos? Tenemos unos sprites y no sabemos si necesitamos hacer más enemigos o no.

**Uso de la respuesta:** se confirmó que el enunciado no fija la cantidad de enemigos (salen del catálogo de cada cripta) y que la cripta de la API tiene 2 tipos y 3 enemigos. Se decidió que la Vista use un sprite por tipo conocido y uno genérico para los tipos nuevos, sin escribir ids de una cripta en el código.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Domingo 18 de octubre 2026

**Herramienta:** Claude

Kristel ya trajo lo de Marco y avanzó con la Vista y el Controlador. Revisa su rama y dime:

* Si la puedo traer a mi rama sin problemas
* Qué significa el aviso de `pygame-ce` que salió después del merge y cómo se arregla
* Qué me falta a mí para terminar mi parte

**Uso de la respuesta:** se comprobó que la rama no cambiaba archivos de Datos y que pasaban las pruebas; se resolvió el aviso de `pygame-ce` sincronizando el entorno con `uv.lock`, y se armó la lista de pendientes (bitácora de LLM, README y Documento de Decisiones).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 14 de octubre 2026

**Herramienta:** Gemini

Lee detenidamente el enunciado adjunto de mi proyecto de videojuego y, basándote en sus mecánicas, crea una lista de controles de teclado y ratón que sean cómodos, intuitivos y fáciles de recordar para el jugador.
Requisitos:
- Identifica las mecánicas, acciones e interacciones que aparecen en el enunciado.
- Asigna una tecla o combinación de teclas adecuada a cada acción, priorizando la comodidad y evitando controles innecesariamente complicados.
- Utiliza el ratón para las interacciones que resulten más naturales con él. En particular, recoger objetos del suelo debe realizarse haciendo clic sobre ellos.
- Evita asignar la misma tecla a acciones diferentes cuando esto pueda causar conflictos.
- Ten en cuenta la frecuencia con la que se realiza cada acción y la facilidad para acceder a sus controles durante el juego.
- No inventes mecánicas que no estén contempladas en el enunciado.
Formato de respuesta:
Presenta una tabla con las siguientes columnas:
1. Acción o mecánica.
2. Tecla o control asignado.
3. Justificación breve de por qué es adecuado.
Al final, incluye una lista de las teclas utilizadas y verifica que no existan conflictos entre las asignaciones.
Prioriza una distribución ergonómica y coherente, siguiendo convenciones habituales de los videojuegos de PC cuando sean aplicables. Si alguna mecánica admite varias opciones, recomienda la más intuitiva y explica brevemente tu elección.

**Uso de la respuesta:** Diseño y asignación de controles para el juego

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Domingo 18 de octubre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

**Uso de la respuesta:** revisión del proyecto contra el enunciado y la rúbrica. Se probó en vivo (partida automática en cripta-04 con 8 de 52 solicitudes, `--replay`, `--bench`) y se armó la lista de pendientes por prioridad: Documento de Decisiones, efectos de §2.10 sin implementar (el veneno nunca se aplicaba y no había regeneración), versión de Python, precarga síncrona, archivos de la Vista sin subir, paquete offline y cómo correr las pruebas. La lista se fue actualizando durante la sesión.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Domingo 18 de octubre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

**Uso de la respuesta:** commit `5d43898`. Se bajó `requires-python` de 3.14 a 3.11 (lo que pide el enunciado) y se verificó con un Python 3.11 real: pruebas, `--replay` y `--bench`. Se corrigió el conteo de fallos de caché (§5.1): la precarga descargaba fichas sin contarlas, así que el reporte mostraba 0 fallos con 11 fichas descargadas. Se agregaron 3 pruebas.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Domingo 18 de octubre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

**Uso de la respuesta:** commit `e4a4c3f`. Se implementaron los efectos de §2.10 que faltaban: veneno al golpear o por trampa, regeneración cada 200 unidades y trampas con cambio de velocidad. También se cancelan los efectos de un actor al morir. Como el API todavía no publica esos campos, `DTO/EfectoFichaDTO.py` los lee de forma tolerante (varias formas y nombres, valores inválidos ignorados, tipos desconocidos conservados con un aviso). Las fichas conservan los campos que no conocen para que la caché en disco no los pierda. Es reversible con el pergamino y se guarda sin cambiar el formato binario. Se agregaron 28 pruebas y se comprobó, rompiendo el código a propósito, que detectan errores. Decisiones que van al Documento de Decisiones: un veneno nuevo reemplaza al anterior y las ralentizaciones se acumulan.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Domingo 18 de octubre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

**Uso de la respuesta:** no hizo falta reescribir la Vista. `View/Animaciones.py` y `View/EfectosEscena.py` ya estaban en `origin/kris`, en commits posteriores al que se había integrado, y se integraron con el merge `de49c3d`. En el cierre (commit `4740816`) se corrigieron dos defectos reales: con 12 enemigos y 12 objetos al centro de la sala no cabían, y una línea de la ayuda se cortaba. También se recalibraron tres pruebas que fallaban sin que la Vista estuviera mal. Además se agregó al README la sección de controles y se actualizó `GUIA_VISTA.md` con el estado final.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Domingo 18 de octubre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

**Uso de la respuesta:** se evaluó pasar la precarga (§4.2) a un hilo en segundo plano: un solo hilo para toda la red, la `Cola` propia en vez de `ThreadPoolExecutor` (§7) y la incorporación con un desfase fijo de una acción para mantener el determinismo. El equipo decidió dejarla síncrona porque funciona, y defenderla con mediciones en el Documento de Decisiones. En el commit `9a7f177` se agregaron al paquete offline cripta-02 a cripta-04, se ajustaron 3 pruebas que daban por hecho una sola cripta y se creó `tests/correr_pruebas.py`, que corre las 350 pruebas de `unittest` y los 27 scripts `probar_*`. El trabajo de la sesión se dividió en los commits `5d43898`, `e4a4c3f`, `4740816` y `9a7f177`, y se comprobó que cada uno pasa las pruebas por sí solo.

-----------------------------------------------------------------------------------------------------------------------

