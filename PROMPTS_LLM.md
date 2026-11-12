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

**Fecha:** Lunes 9 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5, spec-kit)

/speckit.specify Feature 001-terreno-cazador. Terreno con costo por salida y un nuevo enemigo "cazador".
Cada salida puede declarar un costo entero >= 1 (100 si no lo declara), igual en ambos sentidos.
Moverse por una salida cuesta su costo para todos los actores, con intervalo = max(1, costo*100 // velocidad);
atacar, esperar y demás acciones no cambian. Errantes y rastreadores conservan su comportamiento.
El cazador tiene un "rango" en unidades de costo. En su turno: si comparte sala con el jugador, ataca;
si no, calcula el costo mínimo d hasta la sala del jugador usando solo salidas abiertas en ese instante;
si no hay ruta o d > rango, espera (costo 100); si hay, avanza un paso cuyo costo es el de la salida.
Desempate: entre las vecinas v con costo(u,v) + dist(v,jugador) = d, va a la de menor id.
Conoce el esqueleto completo y el estado actual de las puertas, no lo afecta la niebla, no abre puertas.
Su decisión debe ser idéntica a calcularla desde cero en ese instante, aunque se reutilicen cálculos.
Incluir como escenarios de aceptación los 7 casos del Apéndice B "Terreno y cazador", con una tabla de trazabilidad.
Requisitos FR-101 en adelante. No nombrar estructuras de datos, clases ni módulos.

**Uso de la respuesta:** se generó `specs/001-terreno-cazador/spec.md` (FR-101 a FR-118, NFR-101 a NFR-103, SC-101 a SC-106) con los 7 casos del Apéndice B como escenarios con ejemplos numéricos y su tabla de trazabilidad, más `checklists/requirements.md`. Los puntos que el enunciado no fija quedaron como supuestos para `/speckit.clarify`.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Lunes 9 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5, spec-kit)

/speckit.clarify Convertir cada punto de "Supuestos" en una clarificación confirmada: registrar
pregunta y respuesta en "Clarificaciones" (Sesión de hoy), actualizar o crear el FR que corresponda
y quitarlo de "Supuestos". Preguntarme uno por uno antes de confirmarlo:
1) Dos salidas hacia la misma vecina: el cazador usa la más barata. ¿Qué hace el errante en ese caso?
2) Otros enemigos no bloquean el paso del cazador.
3) Un cazador que entra a la sala del jugador no ataca en ese mismo turno.
4) Una ficha de cazador sin rango es un error de datos, no recibe valor por defecto.
5) Con d == rango el cazador se mueve (la regla dice "si d > rango, espera").
6) FR-115: confirmar que la decisión del cazador no consume el generador aleatorio.
Al terminar, la sección "Supuestos" debe quedar vacía o eliminada. No nombrar estructuras de datos,
clases ni módulos.

**Uso de la respuesta:** se confirmaron las 6 preguntas con la opción recomendada y quedaron en «Clarificaciones», Sesión 2026-11-09, de `specs/001-terreno-cazador/spec.md`. Se crearon FR-119 (salida más barata hacia la misma vecina), FR-120 (otros actores no bloquean), FR-121 (no ataca en el turno en que llega), FR-122 (`rango` o costo inválido: error de datos, la partida no inicia) y FR-123 (activación según P1 §2.4). Se ajustaron FR-104, FR-106, FR-108, FR-110 y FR-118. Se eliminó la sección «Supuestos».

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Lunes 9 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

Corregir FR-115 y su clarificación (pregunta 6): la decisión del cazador de moverse o esperar
(búsqueda de ruta y desempate) no usa el generador aleatorio de la partida. Cuando el cazador
ataca, el daño se calcula con la fórmula de combate de la primera parte (P1 §2.6), que sí usa
el generador, igual que cualquier enemigo. No cambiar ningún otro requisito.

**Uso de la respuesta:** se corrigieron FR-115 y la clarificación de la pregunta 6 en `specs/001-terreno-cazador/spec.md`. Moverse o esperar no usa el azar, y el daño del ataque usa la fórmula de P1 §2.6 con el generador de la partida.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Lunes 9 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

Reescribir SC-103 así: "Misma cripta, misma semilla y mismas acciones producen la misma partida,
con o sin cazadores. Las decisiones de moverse o esperar de los cazadores no consumen el generador
aleatorio: en una partida donde ningún cazador ataca, agregar cazadores no cambia lo que eligen
los errantes." No cambiar ningún otro requisito.

**Uso de la respuesta:** se reescribió SC-103 en `specs/001-terreno-cazador/spec.md` con el texto indicado, para que no contradiga FR-115.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Lunes 9 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5, spec-kit)

/speckit.plan Seguir la constitución v1.2.0. Python 3.11, sin dependencias nuevas; solo las bibliotecas
permitidas por el Principio II. Prohibido dict, set, heapq, bisect, collections, copy (fuera de tests),
sorted()/list.sort() en ordenamientos evaluados y cualquier biblioteca de grafos o rutas.
Arquitectura: Logic no llama a Data ni a Service; los DTO son el único formato entre capas;
el paquete Estructuras no depende de ninguna capa.
Antes de diseñar, revisar las limitaciones de las estructuras existentes contra esta feature:
Logic/ColaEventos.py (montículo binario; registra en HistorialRetroceso si tiene uno),
Logic/Comportamientos.py (decidir() devuelve una sala destino, no una salida),
Logic/Mazmorra.py (salidas_abiertas() devuelve destinos sin costo),
Logic/motorJuego.py (el movimiento hoy cuesta 100 fijo).
Abierto/Cerrado: el cazador entra como clase nueva en COMPORTAMIENTOS; cada cambio a código de la
primera entrega debe justificarse con su requisito en una tabla.
Decisiones a evaluar con alternativas y complejidad: 1) cola de prioridad; 2) un cálculo por cazador
frente a uno compartido desde el jugador (el costo es simétrico); 3) cortar la búsqueda en el rango;
4) qué eventos invalidan una ruta y si conviene reutilizar o recalcular siempre; 5) la búsqueda debe
poder usarse sobre el mapa conocido del jugador para "ir a".
Toda caché que sea estado del juego se registra en HistorialRetroceso.
Código nuevo con type hints y docstring breve. Pruebas con unittest en tests/.
Incluir las mediciones planificadas para --bench según el §6.3.
Contrato de datos aún no confirmado con el integrante 2: proponer SalidaDTO.costo (int, 100 si
falta) y FichaEnemigoDTO.rango (int, sin valor por defecto), con la validación de FR-122 en la
capa Data. Marcarlo en el plan como "Propuesto — pendiente de confirmar con integrante 2" y no
planificar código de la capa Data, que le corresponde a él.

Seguimiento (durante la misma ejecución): "en FichaEnemigoDTO (int, sin default). Si una ficha de cazador no trae rango válido, o una salida trae un costo menor que 1 o no entero, es error de datos: se informa con contexto y la partida no inicia (FR-122). Esa validación va en Data, ¿te parece? FichaEnemigoDTO es mío, así que rango lo agrego yo; costo en SalidaDTO sería tuyo."

**Uso de la respuesta:** se generaron `plan.md`, `research.md`, `data-model.md`, `quickstart.md` y `contracts/` (contrato de datos y búsqueda compartida) en `specs/001-terreno-cazador/`. Decisiones: montículo propio en Estructuras, búsqueda compartida desde el jugador, reanudable y cortada en el rango, invalidación por cambio de sala del jugador o por puertas que tocan salas ya cerradas, y descarte registrado en el historial. `FichaEnemigoDTO.rango` queda como `int | None = None` porque el dataclass lo exige; Data rechaza al cazador sin rango válido. Quedó el hallazgo H-1 (salida que usa el rastreador con dos salidas hacia la misma sala), que se corrige en la spec.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Lunes 9 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

Agregar a la spec, en su propio commit: cuando dos salidas abiertas llevan a la misma vecina,
el rastreador, igual que el cazador, se mueve por la más barata y paga su costo. El errante sigue
sorteando entre salidas como en P1. Registrarlo en Clarificaciones y en el FR correspondiente. yo hago el commit no lo hagas tu ok?

**Uso de la respuesta:** se corrigió el hallazgo H-1 del plan en `specs/001-terreno-cazador/spec.md`: nueva pregunta en «Clarificaciones», Sesión 2026-11-09, y FR-104 ampliado (el rastreador usa la salida más barata hacia la vecina; el errante sortea entre salidas). Se ajustó el caso borde que ya trataba ese punto, para que no contradiga FR-104. El commit lo hace el integrante.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Lunes 9 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

listo, ya hice el commit; marca H-1 como resuelto en plan.md

**Uso de la respuesta:** en `specs/001-terreno-cazador/plan.md` se marcó H-1 como resuelto (commit `58f7310`, FR-104 y pregunta 7 de «Clarificaciones»), y el Principio IX de la tabla de la constitución pasó de ⚠️ a ✅.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Lunes 9 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5, spec-kit)

/speckit.tasks

**Uso de la respuesta:** se generó `specs/001-terreno-cazador/tasks.md` con 46 tareas en 7 fases (preparación, base, una fase por historia H1 a H4, y bench y cierre), pruebas antes del código y cada prueba con su FR. Las tareas de `SalidaDTO.costo` (integrante 2) y `ActorDTO.comportamiento` (integrante 3) quedan como coordinación, no como código del integrante 1. El cazador se implementa primero calculando desde cero (H2) y después con la búsqueda compartida (H3).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Lunes 9 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5, spec-kit)

/speckit.analyze

**Uso de la respuesta:** informe de solo lectura sobre `spec.md`, `plan.md` y `tasks.md` de la feature 001: 1 hallazgo crítico (C1, ubicación de `DECISIONES.md`), 4 altos (H1 costo declarado en un solo lado de la salida, H2 FR-122 sin tareas, H3 pruebas de interfaz de H4, H4 repetir la medición de la agenda), 6 medios y 6 bajos. Cobertura de requisitos: 30 de 32. Las correcciones se aplicaron en el prompt siguiente.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Lunes 9 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

Sí, prepará los cambios con estas decisiones:
H1: si solo un lado de la salida declara costo, ambos lados lo usan; si ninguno, 100; si declaran
valores distintos, es error de datos (FR-122). La igualación va junto a _igualar_caras, extendiendo
sin reescribir. Si eso queda en Data, marcalo como coordinación con el integrante 2.
M3: cripta sintética de 1 000 salas en grilla y 30 cazadores. SC-105: al multiplicar por 10 el
tamaño de la cripta, la decisión de un cazador con rango pequeño no tarda más del doble.
C1: DECISIONES.md en la raíz del repo.
Aplicá también H2, H3, H4, M1, M2, M4, M5, M6 y los LOW L1, L2, L3, L5 y L6.
Separá los cambios en dos commits:
1) "spec(001): costo en ambos lados de la salida y criterios medibles" (H1, M3, L3) solo con spec.md.
2) "plan(001): correcciones tras analyze" con plan, tasks, data-model, quickstart, contratos,
checklist y PROMPTS_LLM.md.

**Uso de la respuesta:** commit 1 (`spec.md`): FR-101 y FR-122 con el costo en uno o dos lados, escenario H1-8, dos clarificaciones nuevas, NFR-101, SC-104 y SC-105 medibles, y FR-119 a FR-123 reordenados. Commit 2: `SalidaDTO.costo` pasa a `int | None` (costo declarado) y Lógica iguala los dos lados con `_igualar_costos()` junto a `_igualar_caras()`; `ArmadorEstado` debe copiar el costo igualado (coordinación con el integrante 3); tareas nuevas para FR-122 (integrante 2), pruebas de interfaz de H4 (integrante 3), la agenda con costos, el cierre automático en el mismo instante y los modos sin vista; `DECISIONES.md` en la raíz; «sala resuelta» en lugar de «sala cerrada» en la búsqueda; tareas renumeradas (T001 a T051). También se ajustó `research.md` (vocabulario, R5, R6 y R7).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Lunes 9 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

En spec.md, definir "rango pequeño" como rango = 200 (dos salidas de costo por defecto) en SC-105
y en NFR-102 si también lo menciona. Registrarlo en Clarificaciones (sesión de hoy) como pregunta y
respuesta. Revisar que plan.md y la tarea del bench usen ese mismo valor; si coinciden, no tocarlos.
No hacer commit todavía: mostrame el cambio.

**Uso de la respuesta:** en `specs/001-terreno-cazador/spec.md` se definió `rango` pequeño = 200 en NFR-102 y SC-105 y se agregó la pregunta a «Clarificaciones». `plan.md` y las tareas T043 y T045 ya usaban `rango` 200, así que no se tocaron.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Lunes 9 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5, spec-kit)

/speckit.analyze

**Uso de la respuesta:** segunda pasada de análisis (solo lectura) sobre `spec.md`, `plan.md` y `tasks.md` de la feature 001: sin hallazgos críticos ni altos; 3 medios (M1 hash de commit que ya no existe en `plan.md`, M2 de dónde sale el costo del grafo de búsqueda, M3 ayudante de cuadrícula con costos para T028) y 2 bajos. Cobertura de requisitos: 32 de 32.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Lunes 9 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

Sí, prepará M1, M2 y M3; no L1.
M1: en plan.md, citar los commits por su mensaje en lugar del hash.
M2: en contracts/busqueda-rutas.md, agregar la regla de que el mapa usa el costo ya igualado por
Lógica, nunca SalidaDTO.costo directo.
M3: agregar cuadricula_con_costos(n, azar) a T003 (mismo costo en ambos lados, desde un
random.Random) y que T028 la use.
Un solo commit: "plan(001): correcciones de la segunda pasada de analyze", incluyendo PROMPTS_LLM.md.
Mostrame los cambios antes del commit.


**Uso de la respuesta:** `plan.md` cita los commits de H-1 y H-2 por su mensaje; `contracts/busqueda-rutas.md` exige el costo ya igualado por Lógica en todo grafo, incluido el del mapa conocido; T003 agrega `cuadricula_con_costos(n, azar)` y T028 la usa.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Lunes 9 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5, spec-kit)

/speckit.analyze

**Uso de la respuesta:** tercera pasada de análisis (solo lectura) sobre `spec.md`, `plan.md` y `tasks.md` de la feature 001: sin hallazgos críticos ni altos; 1 medio (M1: T043 reutilizaba `_cuadricula`, que arma salidas sin costo) y 3 bajos (L1 y L2 ya aceptados, L3 reutilizar `cuadricula_con_costos` en T048). Cobertura de requisitos: 32 de 32.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Lunes 9 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

Aplicá M1 como recomendás: en T043, helper privado _cuadricula_con_costos(lado, azar) en
Logic/BenchRutas.py que toma el resultado de _cuadricula(lado) y asigna el costo con
dataclasses.replace, igual en ambos lados, sin modificar _cuadricula. Aplicá también L3 en T048.
Un commit: "tasks(001): costos en las grillas del bench", incluyendo PROMPTS_LLM.md.

**Uso de la respuesta:** en `specs/001-terreno-cazador/tasks.md`, T043 arma las cuadrículas del bench con `_cuadricula_con_costos(lado, azar)` (nuevo, privado, en `Logic/BenchRutas.py`, sobre `_cuadricula` sin modificarlo) y T048 arma su cuadrícula con `cuadricula_con_costos` de T003.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Martes 10 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

En specs/001-terreno-cazador/tasks.md, ampliá T043 (medir_agenda_con_costos, §5.6) para que el
bench de la agenda de eventos también mida: (a) muchos eventos con el mismo tiempo y (b) muchas
cancelaciones, que son el límite conocido del montículo con invalidación perezosa. Mantené los FR
que ya cita. Agregá la medición correspondiente a la tabla de mediciones de plan.md si no está.
Mostrame el cambio y hacé un commit: "tasks(001): T043 mide mismo tiempo y cancelaciones",
incluyendo PROMPTS_LLM.md con este prompt.

**Uso de la respuesta:** en `specs/001-terreno-cazador/tasks.md`, T043 (`medir_agenda_con_costos`) mide además muchos eventos con el mismo tiempo (un solo tiempo y 10 tiempos) y muchas cancelaciones (50 % y 90 %), con 100 / 1 000 / 10 000 eventos; se mantienen sus referencias (R6, Principio VIII). En `plan.md` se agregaron las dos filas correspondientes a la tabla de mediciones de `--bench`.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Martes 10 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5, spec-kit)

/speckit.implement Implementar solo T040 y quitar el skip de T037.
T040: en Enemigo, sobrescribir a_dto() para que devuelva
dataclasses.replace(super().a_dto(), comportamiento=self.ficha.comportamiento), sin modificar
ActorBase.a_dto() (Principio III, extender sin reescribir). El Jugador sigue con comportamiento None.
Código nuevo con type hints y docstring breve.
T037: quitar el skip y verificar que la prueba pasa y cita su FR.
Corré tests/correr_pruebas.py. Un commit: "feat(001): T040 comportamiento en ActorDTO de enemigos [FR-117]",
incluyendo PROMPTS_LLM.md. No tocar ninguna otra tarea.

Respuesta a la pregunta de Claude (la prueba de T037 no existía): Opción 1, pero sin el caso del cazador:
Enemigo todavía no puede construirse con comportamiento "cazador" porque esa clase aún no existe. Escribí
T037 en tests/test_dto_terreno.py con errante → "errante", guardián o rastreador → su valor, y jugador →
None, citando FR-117. Agregá en tasks.md, en la tarea que crea la clase Cazador, una nota: "agregar el caso
cazador → 'cazador' a la prueba de T037".

**Uso de la respuesta:** `Logic/Enemigo.py` redefine `a_dto()` con `dataclasses.replace(super().a_dto(), comportamiento=self.ficha.comportamiento)`, sin tocar `ActorBase.a_dto()`. Se creó `tests/test_dto_terreno.py` con `test_h4_2_fr117_actor_dto_trae_el_comportamiento` (errante, guardián y rastreador traen su comportamiento; el jugador, `None`), sin skip. En `tasks.md` se marcaron T037 y T040 y se agregó en T024 la nota de sumar el caso del cazador a esa prueba.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Martes 10 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Opus 5.5)

En tasks.md, actualizá el texto de T037 para que describa la prueba tal como quedó: errante,
guardián y rastreador traen su comportamiento y el jugador trae None, sin skip. El caso del
cazador queda en la nota de T024. Commit: "tasks(001): actualizar descripción de T037",
incluyendo PROMPTS_LLM.md.

**Uso de la respuesta:** en `specs/001-terreno-cazador/tasks.md`, T037 describe la prueba como quedó: errante, guardián y rastreador traen su comportamiento y el jugador `None`, sin `skip`; el caso del cazador remite a la nota de T024.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Martes 10 y miércoles 11 de noviembre 2026

**Herramienta:** Claude

Le pedí a Claude revisar las ramas de Marco y Kristel junto con la constitución v1.2.0 y la spec 001, confirmar el contrato de datos (specs/001-terreno-cazador/contracts/contrato-datos.md) y hacer la tarea T001: agregar costo a SalidaDTO como último campo, de tipo int | None con None por defecto, leerlo en desde_diccionario y escribirlo en a_diccionario solo si no es None, con pruebas que citen FR-101.

**Uso de la respuesta:** se usó en `DTO/SalaDTO.py` y `tests/TestDtos.py` (T001, FR-101). Revisé el cambio y corrí las pruebas: 355 OK y 31/31.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Martes 11 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Sonnet 5.5)

/speckit-specify Línea de tiempo de Cripta II. Usa exactamente el directorio specs/004-linea-tiempo y numera los requisitos con el prefijo FR-4xx (FR-401, FR-402, ...).

Antes de escribir, lee .specify/memory/constitution.md (sobre todo los principios IX y X) y, del enunciado de la Parte II (Proyecto II parte.pdf): §3.6, §7.3 y el Apéndice B (sección «Línea de tiempo»). Escribe SOLO el QUÉ: reglas, historias de usuario, escenarios de aceptación y requisitos numerados. No nombres estructuras de datos, clases, módulos ni algoritmos; eso va en el plan.

Capacidad: consultar, sin modificar la partida, el estado de la partida en cualquier instante pasado, desde el inicio. Es independiente del pergamino de retroceso, que sigue limitado a 5 acciones.

Reglas:
- Estado en el instante t: el estado tras ejecutar todos los eventos con tiempo menor o igual que t. Si a t le corresponde una decisión del jugador, es el estado justo antes de tomarla. Estas dos frases pueden dar estados distintos cuando hay eventos con el mismo tiempo; deja UNA sola marca [NEEDS CLARIFICATION] sobre eso y no la resuelvas.
- Comandos en partida: «historia <t>» e «historia #k» (estado justo antes de la acción número k del jugador). Muestran como mínimo: reloj, sala del jugador, vida y estadísticas, inventario, efectos activos, enemigos de esa sala con su vida y el mapa conocido en ese momento. La consulta no consume tiempo virtual, no se registra como acción y no altera el estado del juego ni el historial de retroceso.
- Consultar un instante posterior al reloj actual se rechaza.
- Sin interacción: «--replay partida.log --hasta <t>» reproduce hasta t e imprime el mismo resumen, sin interfaz gráfica.
- Las acciones revertidas con un pergamino dejan de existir en la línea de tiempo.
- Se puede configurar con «--checkpoint-cada K» cada cuántas acciones del jugador se guarda una copia completa. Una consulta no puede requerir aplicar o deshacer cambios de más de K acciones del jugador. El valor por defecto de K se justificará en el plan con mediciones (no lo fijes aquí).
- Guardar y cargar la partida conserva la línea de tiempo completa. Un archivo de partida de la primera parte se reporta como incompatible (o se migra de forma explícita); nunca se carga en silencio.

Historias de usuario (con prioridad): consultar un instante en partida; consultar sin interacción con --hasta; mantener la línea correcta al usar el pergamino; conservar la línea al guardar y cargar.

Escenarios de aceptación: incluye estos seis casos del Apéndice B, cada uno en formato Dado/Cuando/Entonces y con su requisito FR-4xx:
1. historia <t> con t mayor que el reloj actual: se rechaza.
2. historia después de usar un pergamino: no muestra las acciones revertidas.
3. Varios eventos ocurren en el mismo instante t: historia <t> muestra el estado después de todos ellos (sujeto a la aclaración pendiente).
4. historia no consume tiempo virtual, no se registra en partida.log y no modifica el historial de retroceso.
5. --replay partida.log --hasta t con t posterior al final de la partida: muestra el estado final e indica que la partida terminó antes.
6. Se carga un archivo de partida de la primera parte: se reporta la incompatibilidad de formato o se migra explícitamente; nunca se carga en silencio.

Suposiciones y fuera de alcance: el cursor del inventario y los mensajes del juego no forman parte del estado consultable; «ir a» y el mapa conocido son de la spec 002 (el resumen incluye el mapa conocido cuando exista); la verificación de resolubilidad es de la spec 003.

No escribas código ni crees archivos fuera de specs/004-linea-tiempo.

**Uso de la respuesta:** se usó en `specs/004-linea-tiempo/spec.md` con los requisitos FR-401 a FR-423 y los 6 casos del Apéndice B como escenarios de aceptación

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Martes 11 de noviembre 2026

**Herramienta:** Claude (Claude Code, modelo Claude Sonnet 5.5)

Edita SOLO specs/004-linea-tiempo/spec.md (y checklists/requirements.md si algo de lo que menciona cambia). No toques la marca [NEEDS CLARIFICATION] de FR-402, no resuelvas esa aclaración y no escribas código. No nombres estructuras, clases ni módulos.

1. SC-405: reemplázalo por: «Una consulta `historia` se contesta en menos de 50 ms en una partida de al menos 5 000 acciones del jugador, con el valor de K por defecto, medido con --bench (§6.3 de la Parte II).»
2. Agrega NFR-402: la memoria total de la línea de tiempo crece con la cantidad de cambios ocurridos más una copia completa cada K acciones del jugador, y no con el producto de las acciones por el tamaño del estado (§5.5).
3. Agrega NFR-403: al usar un pergamino, la línea de tiempo se recorta sin recorrer toda la historia (§5.5).
4. Amplía NFR-401: las mediciones cubren al menos tres valores de K y la alternativa sin puntos de control, y justifican el valor por defecto (§5.5 y §6.3).
5. Historia 3, escenario 1: corrígelo para que sea coherente con FR-404, FR-409 y FR-413. Tras revertir la acción 5 solo existen 4 acciones: `historia #5` se rechaza por rango, y consultar el instante actual muestra al jugador en la sala 7, no en la 9. Mantén la referencia al Apéndice B caso 2 y agrega FR-409 a los requisitos del escenario.
6. Elimina FR-422 y el escenario 4 de la Historia 4. Amplía FR-421 para cubrir también «un archivo de una versión distinta a la actual». Actualiza todas las referencias y la tabla de trazabilidad.
7. En Suposiciones agrega: «Se asume que cada paso de «ir a» es una acción ordinaria del jugador; se confirmará en la spec 002.»
8. Al final verifica que no queden referencias a FR-422 y que ninguna cifra de rendimiento contradiga la tabla de §6.3 del enunciado. Dime qué cambiaste.

**Uso de la respuesta:** se usó en `specs/004-linea-tiempo/spec.md`para corregir la spec 004: cifra de rendimiento según §6.3, escenario de pergamino incoherente, requisitos de memoria y recorte (NFR-402/403) y se eliminó FR-422

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude

Le pedí a Claude revisar la spec 004 de Kristel (revisión cruzada: el integrante 2 revisa la del 3) contra el enunciado de la Parte II (§3.6, §5.5, §6.1 y Apéndice B «Línea de tiempo») y la constitución (principios IX y X), y redactar las observaciones. También le pedí preparar el prompt de /speckit-specify de mi spec 003 y revisar el resultado contra el enunciado, la constitución y el código de la primera parte (SalidaDTO, Mazmorra._igualar_caras y los códigos de salida de main.py) antes de cada paso.

**Uso de la respuesta:** se usó para las observaciones de la revisión cruzada de `specs/004-linea-tiempo/spec.md` y para definir el prompt, las correcciones y las respuestas de clarify de `specs/003-resolubilidad/spec.md`.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

/speckit-specify SPECIFY_FEATURE_DIRECTORY=specs/003-resolubilidad

Verificación de resolubilidad de Cripta II. Usa exactamente el directorio specs/003-resolubilidad. Numera los requisitos funcionales FR-301, FR-302, …; los de rendimiento NFR-301, …; y los criterios de éxito SC-301, …. No empieces en 001.

Antes de escribir, lee .specify/memory/constitution.md (sobre todo los principios IX y X) y, del enunciado de la Parte II (Proyecto II parte.pdf): §3.5, §4.2, §4.3, §5.4, §6.1 y el Apéndice B (sección «Resolubilidad»). Escribe SOLO el QUÉ: reglas, historias de usuario, escenarios de aceptación y requisitos numerados. No nombres estructuras de datos, clases, módulos ni algoritmos; eso va en el plan.

Reglas (§3.5):
- Antes de iniciar una partida, el programa determina si la cripta puede ganarse usando el esqueleto y la ubicación de las llaves.
- Supuestos de la verificación: el jugador puede atravesar cualquier salida abierta y cualquier salida cerrada cuya llave ya obtuvo; las llaves no se consumen; todo enemigo puede ser derrotado; una llave que suelta un enemigo se considera obtenible en la sala donde ese enemigo inicia; las trampas y los cierres automáticos no bloquean, porque una puerta puede volver a abrirse con la misma llave. El costo de las salidas no afecta la verificación.
- Resoluble: partiendo de la sala inicial y bajo esos supuestos, el jugador puede obtener llave_salida y llegar a sala_salida a través de una puerta que la requiere.
- Si es resoluble, el resultado es un orden de obtención de llaves en el que cada llave aparece después de todas las llaves necesarias para alcanzarla. Si hay varios órdenes válidos, el resultado es determinista: la misma cripta produce siempre el mismo orden.
- Si no es resoluble, el reporte incluye: las llaves que no pueden obtenerse; las puertas de la frontera bloqueada (las puertas cerradas adyacentes a la región alcanzable) con la llave que requiere cada una; dónde se encuentra cada una de esas llaves; y, si una llave está ubicada detrás de puertas que solo ella abre, directamente o mediante una cadena de llaves, el ciclo concreto. La detección del ciclo es determinista.
- Si la cripta no es resoluble, la partida no inicia y se muestra el reporte, salvo que se use --forzar.
- --verificar <cripta> ejecuta únicamente la verificación y muestra el reporte, sin instanciar la vista. Funciona también con --offline.

Datos (§4.2, §4.3):
- La ubicación de cada llave trae su id, la sala y, opcionalmente, la instancia de enemigo que la suelta; en ese caso la sala es donde ese enemigo inicia.
- La consulta de ubicación de llaves cuenta dentro de presupuesto_solicitudes. Su respuesta es válida mientras coincida la versión de la cripta y puede persistirse con el resto de los datos de la cripta. En --offline se lee del paquete local.
- Lo persistido por la primera parte se invalida con la validación de versión que ya existe, no borrando archivos a mano.

Rendimiento (§5.4, §6.1):
- La verificación tarda menos de 200 ms con la cripta publicada más grande.
- El costo total crece aproximadamente de forma lineal con salas, salidas y llaves: obtener una llave no puede implicar repetir el recorrido completo de la cripta.
- El reporte de una cripta no resoluble (frontera y dependencias entre llaves) sale del mismo recorrido, no de recorridos adicionales por cada llave.
- --bench compara contra la alternativa de repetir el recorrido por cada llave, en criptas sintéticas deterministas por semilla con muchas llaves encadenadas.

Historias de usuario (con prioridad): saber antes de jugar si la cripta es resoluble y en qué orden obtener las llaves; entender por qué una cripta no es resoluble; verificar una cripta sin jugar con --verificar; jugar de todas formas con --forzar.

Escenarios de aceptación: incluye estos cuatro casos del Apéndice B, cada uno en formato Dado/Cuando/Entonces y con su FR-3xx, y una tabla «Trazabilidad del Apéndice B «Resolubilidad»» como la de la spec 001:
1. llave_salida está detrás de la única puerta que ella misma abre: no resoluble; el reporte señala el ciclo.
2. Una llave está en el campo suelta de un enemigo errante: la verificación la ubica en la sala inicial del enemigo.
3. Existen varios órdenes válidos de obtención de llaves: dos ejecuciones producen el mismo orden.
4. Cripta no resoluble sin --forzar: la partida no inicia y se muestra el reporte.
Agrega además escenarios para: una cripta sin puertas cerradas; un ciclo formado por una cadena de dos llaves; --forzar con una cripta no resoluble; --verificar con una cripta resoluble y con una no resoluble. Cada requisito funcional debe tener al menos un escenario.

Si algo no está definido en el enunciado (por ejemplo, una ubicación de llave con una sala o un enemigo que no existen, o llave_salida ausente de la lista de llaves), márcalo con [NEEDS CLARIFICATION] en lugar de inventarlo.

Fuera de alcance: cómo se dibuja el reporte en la interfaz gráfica (integrante 3); el costo de las salidas y el cazador (spec 001); el mapa conocido y «ir a» (spec 002); la línea de tiempo (spec 004).

No escribas código ni crees archivos fuera de specs/003-resolubilidad.

**Uso de la respuesta:** se usó para crear `specs/003-resolubilidad/spec.md` y `specs/003-resolubilidad/checklists/requirements.md` (FR-301 a FR-322, NFR-301 a NFR-304, SC-301 a SC-308). Dejó 3 marcadores [NEEDS CLARIFICATION] (FR-305, FR-321 y FR-322). Claude Code borró `.specify/feature.json` por la última instrucción del prompt; lo volví a crear a mano (es local y está en el .gitignore).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

Respuestas y correcciones para specs/003-resolubilidad/spec.md. Edita SOLO ese archivo y checklists/requirements.md. No escribas código ni nombres estructuras, clases, módulos ni algoritmos. Registra las tres respuestas en una sección «Clarificaciones» → «Sesión 2026-11-11», con el formato «P: … → R: …», como en las specs 001 y 004, y quita los tres [NEEDS CLARIFICATION].

1. FR-305 (P1 → A): el orden incluye todas las llaves obtenibles de la cripta, no solo las necesarias para ganar. Ajusta el caso borde «Una llave obtenible pero innecesaria para ganar».

2. FR-321 (P2):
   - Una llave que requiere alguna puerta (incluida llave_salida) y que no aparece en la lista de ubicaciones es no obtenible: aparece en el reporte con la indicación «sin ubicación». No es un error de datos, porque el servicio publica criptas no resolubles (§4.3).
   - Una ubicación cuya sala no existe en el esqueleto es un error de datos: se informa con contexto (qué llave y qué sala), la verificación no concluye y tiene el mismo efecto que FR-320 (la partida no inicia salvo con --forzar). El programa no se cae.
   - La instancia de enemigo de una ubicación no se valida en la verificación, porque comprobarla exigiría descargar el contenido de salas (FR-301); se usa la sala que trae la ubicación.
   Ajusta el escenario H2-6 para que cubra los tres casos por separado.

3. FR-322 (P3 → A): si ninguna puerta hacia sala_salida requiere llave_salida, la cripta no es resoluble. Motivo: en la primera parte (P1 §2.12) la victoria exige entrar a sala_salida después de abrir con la llave correspondiente la puerta que da acceso a ella, así que esa cripta no se puede ganar. El reporte DEBE indicar ese motivo de forma explícita. Ajusta H1-2 (cripta sin ninguna puerta cerrada → no resoluble, con ese motivo) y el caso borde correspondiente.

4. Puertas de dos caras: agrega a FR-302 que una puerta es una sola para las dos salas que une: si solo una de sus caras declara que está cerrada o qué llave requiere, eso vale para las dos, igual que en la primera parte. Corrige el supuesto «Una salida cerrada que no declara llave…» para que diga «que no declara llave en ninguna de sus caras». Agrega en la Historia 1 un escenario donde la llave de una puerta está declarada solo en una cara.

5. FR-308: define la frontera bloqueada como las salidas cerradas que van desde una sala de la región alcanzable hacia una sala fuera de ella. Una salida sin vuelta que solo va de afuera hacia adentro no es frontera. Ajusta también la entidad «Frontera bloqueada».

6. FR-310: en lugar de «señalar al menos uno», exige que cada llave no obtenible que forma parte de un ciclo aparezca en al menos un ciclo señalado, sin repetir ciclos y en un orden determinista. Las llaves que solo dependen de un ciclo (H2-4) se listan junto con el ciclo del que dependen.

7. En Supuestos, cambia «se trata como una cripta no resoluble para efectos de iniciar la partida» por «el programa informa que la verificación no concluyó (no que la cripta sea no resoluble); para iniciar la partida, solo --forzar permite jugar (FR-320)».

8. Actualiza la tabla de cobertura y el checklist. Al final dime qué cambiaste y confirma que no queda ningún [NEEDS CLARIFICATION] ni ningún FR-0xx.

**Uso de la respuesta:** se usó en `specs/003-resolubilidad/spec.md` para responder las 3 aclaraciones (FR-305, FR-321, FR-322), agregar los escenarios H1-10, H2-7 y H2-8, y corregir FR-302 (dos caras), FR-308 (frontera), FR-309, FR-310 (ciclos) y los supuestos.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

/speckit-clarify

Respuestas a las 4 preguntas:
1. Si las dos caras de una misma puerta se contradicen (llaves distintas, o una cerrada y la otra abierta), ¿qué hace la verificación? → «A, solo llaves distintas»
2. Si la lista de ubicaciones trae la misma llave más de una vez, con salas distintas, ¿cómo se trata? → «A, una vez en orden»
3. ¿--verificar devuelve un código de salida distinto según el resultado? → «0 resoluble, 3 no, 1 error»
4. ¿La verificación se ejecuta también al cargar una partida guardada o con --replay? → «A»

**Uso de la respuesta:** se usó en `specs/003-resolubilidad/spec.md`: 4 aclaraciones nuevas en «Sesión 2026-11-11», los escenarios H1-11, H1-12, H2-9 y H4-4, y cambios en FR-301, FR-302, FR-305, FR-309, FR-314, FR-316 y SC-308.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

Ajuste final en specs/003-resolubilidad/spec.md (edita SOLO ese archivo y su checklist; sin código ni nombres de clases):

1. Mi respuesta a la pregunta de las dos caras fue «A, solo llaves distintas», y quedó registrada con más alcance. Corrige la aclaración, FR-302 y el caso borde «Las dos caras de una puerta se contradicen»: solo es error de datos cuando las dos caras declaran llaves distintas. El caso «una cara cerrada y la otra explícitamente abierta» no existe en los datos: como en la primera parte, «cerrada» ausente, null o false significan lo mismo (la cara no declara cierre). Quítalo de esos tres lugares.

2. En FR-302, reemplaza la regla de una sola cara por la de la primera parte: si una cara declara la llave que requiere y la otra no declara ninguna llave, la llave, el estado cerrado y el cierre automático de la primera valen para las dos. Si ninguna de las dos caras declara llave, cada cara se rige por lo que declara: una cara cerrada sin llave no puede atravesarse en ese sentido. Ajusta igual el caso borde «Una puerta declara cierre o llave solo en una de sus caras» y el supuesto «Una salida cerrada que no declara llave…». El escenario H1-10 no cambia.

3. En la aclaración de los códigos de salida y en FR-314, agrega que el código 2 sigue reservado para los argumentos inválidos, como en la primera parte, así que --verificar no lo usa para ningún veredicto.

4. Actualiza la tabla de cobertura si cambia algo y dime exactamente qué líneas modificaste. Confirma que no queda ningún [NEEDS CLARIFICATION] ni ningún FR-0xx.

**Uso de la respuesta:** se usó en `specs/003-resolubilidad/spec.md` para limitar el error de datos de las dos caras a llaves distintas, alinear la regla de una sola cara de FR-302 con la de la primera parte (`_igualar_caras`) y reservar el código de salida 2 para argumentos inválidos (FR-314).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

En specs/001-terreno-cazador/contracts/contrato-datos.md quitá la marca "Propuesto — pendiente de confirmar con integrante 2": Dereck lo confirmó tal como está el 11 nov. Anotalo en el plan si lo menciona. Commit: "plan(001): contrato de datos confirmado con integrante 2", con PROMPTS_LLM.md.

**Uso de la respuesta:** se usó en `specs/001-terreno-cazador/contracts/contrato-datos.md` y `specs/001-terreno-cazador/plan.md` para marcar el contrato de datos como confirmado con el integrante 2 el 11 de noviembre; la parte de `ActorDTO` y `ArmadorEstado` sigue pendiente con el integrante 3.

-----------------------------------------------------------------------------------------------------------------------
