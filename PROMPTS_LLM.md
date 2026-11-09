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
**Fecha:** Domingo 8 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5), comando de spec-kit `/speckit-constitution`

/speckit-constitution Escribe la constitución, en español, del proyecto Cripta II (Estructuras de Datos II, UNA, II ciclo 2026): un juego de exploración por eventos en Python, con reloj virtual, que obtiene criptas de un servicio web o de un paquete local (--offline). Esta es la segunda entrega y continúa el código funcional de la primera. Usa estos principios casi textualmente, con redacción MUST/MUST NOT. No agregues principios, tecnologías ni capas que no estén aquí.

I. Arquitectura MVC en n-capas, estricta
- El proyecto MUST seguir MVC con arquitectura en n-capas. No se admite ningún otro estilo de organización.
- Las capas son: Data (red y disco), Logic (reglas del juego y estructuras de datos), Service (casos de uso), UIController + View (interfaz) y DTO (transversal). Security (validación de acceso y de versión/integridad) acompaña a la interfaz y a los datos. Se mantienen los nombres de carpetas que ya existen en el repositorio.
- El flujo de llamadas es UIController -> Service -> Logic -> Data. Cada capa MUST llamar solo a la capa inmediatamente adyacente. La interfaz MUST NOT llamar a Data, y Data MUST NOT conocer reglas del juego.
- El paquete Estructuras es un paquete de apoyo sin dependencias hacia ninguna otra capa; cualquier capa puede importarlo.
- Logic (el modelo) MUST NOT conocer HTTP, archivos ni la interfaz concreta. El acceso a red y a disco se hace detrás de una interfaz común (FuenteDatos) para que --offline sustituya la fuente sin if dispersos.
- Los DTO son clases simples de datos, sin reglas de negocio, y son el único formato en que fluye información entre capas.
- Cada capa valida lo suyo: Data solo conexión y formato; Logic reglas de negocio; Service no valida; la interfaz valida la estructura de lo que el usuario ingresa.

II. Lenguaje, bibliotecas y estructuras de datos
- El proyecto MUST escribirse únicamente en Python 3.11 o superior.
- Siguen vigentes todas las restricciones del enunciado de la primera parte (Primer Proyecto, §7) y se suman las de Cripta - Parte II (§6.2). La única excepción es cuando Cripta - Parte II mencione expresamente un cambio a alguna de ellas.
- Restricciones de la primera parte: las estructuras de datos de los problemas evaluados MUST implementarse a mano y MUST NOT sustituirse por equivalentes de bibliotecas; dict MUST NOT usarse como índice, caché, tabla de búsqueda o estructura propia (los dict que entrega respuesta.json() solo se leen); list MAY usarse solo como almacenamiento contiguo de bajo nivel; list.sort() y sorted() MUST NOT usarse en los ordenamientos evaluados (se usa el Ordenador del equipo).
- Restricciones que suma la segunda parte: MUST NOT usarse heapq, bisect, collections (deque, OrderedDict, defaultdict, Counter), networkx ni ninguna biblioteca de grafos o de búsqueda de rutas; set queda prohibido en las mismas condiciones que dict.
- Bibliotecas permitidas: requests (con tiempo de espera explícito) y pygame-ce, que ya están establecidas en el proyecto; json, struct, uuid y random.Random; y las de la biblioteca estándar os, pathlib, argparse, time, subprocess y unittest, ya consultadas con el profesor para la primera entrega. Agregar cualquier otra dependencia MUST requerir acuerdo de los tres integrantes y quedar registrada en requirements.txt y pyproject.toml.
- Se MUST mantener las bibliotecas y las estructuras de datos que ya están implementadas en el proyecto. Antes de comenzar cualquier implementación, el grupo MUST revisar las limitaciones de cada estructura ya implementada contra lo que solicita Cripta - Parte II, y dejar el resultado de esa revisión en el plan.md correspondiente.
- spec-kit y el agente de programación son solo herramientas de proceso: MUST NOT introducir dependencias ni estructuras prohibidas. Las dependencias que proponga un plan generado se revisan antes de aceptarlo.

III. Simplicidad: KISS, YAGNI, responsabilidad única y Abierto/Cerrado
- KISS: se elige la solución más simple que cumpla la especificación. El código lo deben poder leer y defender los tres integrantes, incluso los que son principiantes en Python.
- YAGNI: MUST NOT implementarse clases, capas, parámetros ni opciones que ningún requisito numerado pida.
- Responsabilidad única: cada clase y cada módulo hace una sola cosa; las funciones son cortas; los nombres son claros, con type hints y un docstring breve.
- Abierto/Cerrado: el código de la primera entrega que ya funciona está cerrado a modificación y abierto a extensión. Las capacidades nuevas MUST agregarse con clases o módulos nuevos, o extendiendo lo existente, sin reescribir implementaciones funcionales. Solo se modifica código existente cuando es indispensable para cumplir un requisito de la segunda parte o para corregir un defecto; en ese caso el cambio MUST justificarse en plan.md y, si cambia una decisión de la primera parte, mostrarse el antes y el después en DECISIONES.md.

IV. Determinismo
- Misma cripta, misma semilla y mismas acciones MUST producir la misma partida.
- El tiempo real de red MUST NOT avanzar el reloj virtual. Las respuestas pendientes o concurrentes se incorporan en un orden determinista.

V. Modos sin interfaz
- --replay y --bench MUST ejecutarse sin instanciar la vista. Si el modelo necesita una ventana o el teclado para funcionar, la separación de capas está mal.

VI. Sin datos de una cripta concreta en el código
- MUST NOT escribirse en el código números de salas, ids de entidades, páginas, presupuestos ni estadísticas de una cripta específica. El programa debe funcionar con una cripta que el grupo no haya visto.

VII. Red y presupuesto de solicitudes
- El programa MUST respetar presupuesto_solicitudes. Un reintento cuenta dentro del presupuesto.
- El X-Cripta-Client-Id se genera una sola vez por ejecución y se envía en todas las solicitudes.
- Un HTTP 429 o un error de red MUST manejarse con un mensaje con contexto, sin que el programa se caiga.

VIII. Rendimiento con evidencia
- Toda afirmación de rendimiento MUST respaldarse con mediciones propias de --bench. Las mediciones de la primera parte se repiten con la carga nueva.
- Cada decisión de estructura de datos se documenta en DECISIONES.md con: problema, alternativas consideradas, decisión, complejidad, evidencia empírica y límites conocidos, enlazando a la spec y al plan de donde proviene e indicando si la decisión final coincide con la del plan.md original. Las criptas sintéticas de --bench son deterministas por semilla.

IX. Especificación antes del código
- Una especificación MUST confirmarse (commit) antes que cualquier código que la implemente. Si la especificación estaba mal, se corrige primero la especificación y luego el código, en commits separados.
- spec.md contiene reglas del juego, historias de usuario, escenarios de aceptación y requisitos numerados, y MUST NOT nombrar estructuras de datos, clases ni módulos. plan.md contiene las estructuras elegidas, alternativas, complejidad y mediciones previstas. tasks.md contiene tareas pequeñas y verificables, cada una con el requisito que atiende.
- Specs: 001-terreno-cazador, 002-niebla-ir-a, 003-resolubilidad y 004-linea-tiempo. Los requisitos usan el prefijo FR-1xx, FR-2xx, FR-3xx y FR-4xx respectivamente, para que los identificadores no choquen.

X. Trazabilidad y pruebas
- Cada requisito tiene un identificador estable. Cada escenario de aceptación MUST tener al menos una prueba automatizada (con las herramientas que ya usa el repo: unittest y tests/correr_pruebas.py) o un partida.log de reproducción, y la prueba cita el identificador del requisito.

XI. Bitácora de uso de LLM
- Cada prompt enviado a un LLM, incluidos los comandos de spec-kit con texto propio, MUST registrarse en PROMPTS_LLM.md con fecha, herramienta, prompt textual y para qué se usó la respuesta. No se incluyen credenciales ni datos personales.
- El código generado con ayuda de un LLM es responsabilidad del grupo, y cada integrante MUST poder explicarlo y modificarlo.

Gobernanza: esta constitución solo se cambia con acuerdo de los tres integrantes, en un commit propio. Si un plan o una tarea contradice la constitución, el plan o la tarea se corrige.

**Uso de la respuesta:** se generó `.specify/memory/constitution.md` (versión 1.0.0, ratificada el 2026-11-08) a partir de la plantilla de spec-kit, con los principios I a XI y la gobernanza casi textuales. Se quitaron las dos secciones genéricas de la plantilla que no tenían contenido. Quedan pendientes algunos ajustes de la constitución que se revisarán con el equipo.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Domingo 8 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

estos son los ajustes que el equipo vio luego de hacer la version 1.0.1 que es la actual asi que nesesitaremos analizar algunas partes del flujo del codigo y añadir algunas partes que se dejaron por fuera, estas serian las recomendaciones:

Ajustes recomendados
Falta dataclasses en las bibliotecas permitidas. Todos los DTOs usan @dataclass, y la regla dice que cualquier otra dependencia requiere acuerdo. Pasa lo mismo con typing, si la usan para los type hints. Y si piensan hacer los puntos de control de la línea de tiempo con copy.deepcopy, también hay que agregar copy, o decidir desde ya que la copia se hace a mano.
El flujo de capas puede contradecir el código actual. El principio I dice que cada capa solo llama a la adyacente (UIController → Service → Logic → Data). Pero en la primera parte, cuando el motor devuelve "pendiente", quien pide el contenido a la capa de Datos es Servicios, no Lógica, porque Lógica no conoce la red. Revisen cómo está hoy el repo y ajusten la frase. Si no, /speckit.analyze va a marcar como violación algo que ya funciona.
El principio V debería incluir --verificar y --replay … --hasta. El §3.5 y el §3.6 exigen que esas dos banderas también corran sin instanciar la vista.
El principio X podría pedir el Apéndice B explícitamente. El §2.5 exige que cada caso del Apéndice B aparezca como escenario de aceptación en alguna spec. Con una línea en la constitución, el agente lo va a revisar en cada fase.

y luego de eso esta esta recomendacion: Un detalle a tener en cuenta: el principio III pide type hints y docstrings, y el código de Lógica de la primera parte no los tiene. Como el mismo principio dice que no se reescribe lo que ya funciona, lo razonable es aplicarlo solo al código nuevo. Conviene que eso quede claro para que nadie lo tome como una tarea de refactor.

Seguimiento: "sigamos con lo que recomiendas en los puntos 2 al 4 y dime que seria mas conveniente para el codigo nuevo en relacion a copy y deepcopy"

**Uso de la respuesta:** se revisaron las importaciones del repo. Service importa de Data en 8 archivos, Logic no importa de Data y solo 38 de 207 funciones de Logic tienen type hints. Con eso se pasó la constitución a la versión 1.1.0: flujo UIController -> Service -> (Logic y Data) en el principio I, type hints y docstrings solo para el código nuevo en el III, `--replay … --hasta` y `--verificar` en el V y Apéndice B en el X. Quedan pendientes la lista de bibliotecas permitidas y la decisión sobre `copy`.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Domingo 8 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

**Uso de la respuesta:** la constitución pasó a la versión 1.2.0. En el principio II se agregaron a las bibliotecas permitidas `dataclasses`, `typing`, `abc`, `urllib.parse`, `shutil`, `sys` y `math`, que ya usaba la primera entrega. `tempfile`, `contextlib`, `io`, `re`, `types` y `copy` quedan permitidos solo en `tests/`. `copy` no se usa en el código del juego, así que las copias de estado (como los puntos de control de la línea de tiempo) se hacen a mano.

-----------------------------------------------------------------------------------------------------------------------

