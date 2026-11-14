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
**Fecha:** Martes 10 de noviembre 2026

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
**Fecha:** Martes 10 de noviembre 2026

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
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

En spec.md, ampliá FR-122: los costos inválidos o distintos entre las dos caras se detectan con el
esqueleto, antes de iniciar, y la partida no inicia. Una ficha de cazador con rango ausente o
inválido puede llegar durante la partida con la precarga: si llega antes de iniciar, la partida no
inicia; si llega durante la partida, la partida se detiene con un error de datos que indica la ficha
y el campo, sin que el programa se caiga. Registralo en Clarificaciones (pregunta de Dereck, 11 nov).
Agregá el escenario de aceptación correspondiente. Commit solo de spec.md:
"spec(001): FR-122 para fichas inválidas que llegan durante la partida".

**Uso de la respuesta:** commit `f0640c4`. Se amplió FR-122 en `specs/001-terreno-cazador/spec.md` (detección de costos con el esqueleto y fichas de la precarga), se agregó la sesión 2026-11-11 de Clarificaciones con la pregunta de Dereck, el escenario H2-9 y se ajustó el caso borde «Datos inválidos».

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

/speckit-analyze

**Uso de la respuesta:** análisis de solo lectura de `spec.md`, `plan.md` y `tasks.md` de la feature 001. Encontró que H2-9 no tenía prueba (Principio X), que nadie se encargaba de detener la partida ante una ficha inválida de la precarga (hoy `precargar_alrededor` atrapa `ErrorRed` y sigue), que T002, T050, el contrato y el plan seguían diciendo «la partida no inicia» en todos los casos, dos ambigüedades (qué significa «se detiene» y en qué momento) y marcas de estado desactualizadas (T001, T039, «Propuesto»).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

/speckit.clarify Resolver A1 y A2 de FR-122 con esta regla:
Si una ficha de cazador con rango ausente o inválido llega con la precarga, Data la rechaza como
error de formato (distinto del error de red) y esa sala queda sin contenido cargado. La partida se
detiene en el momento determinista en que el jugador intenta entrar a esa sala: el movimiento no se
ejecuta, no consume tiempo, no se registra en partida.log, y la partida termina con un error de
datos que indica la ficha y el campo, sin puntaje y sin que el programa se caiga. --replay termina
en ese mismo punto con un código de salida distinto de 0; --verificar no se ve afectado.
Mientras el jugador no entre a esa sala, la partida sigue: el cazador no se activa (FR-123).
Actualizá FR-122, H2-9 y el caso borde. Agregá "(ampliada en la sesión 2026-11-11)" a la respuesta
de la pregunta 4 de la sesión 11-09 (I5).
Commit solo de spec.md: "spec(001): FR-122 determinista para fichas inválidas de la precarga".
Mostrame el cambio antes del commit.

Respuesta a la pregunta de Claude (el movimiento fallido no se registra, así que --replay no llegaría al error): «Marca de cierre en el log».

**Uso de la respuesta:** commit `f60ec7a`. En `specs/001-terreno-cazador/spec.md` se agregó la aclaración del momento determinista y de `--replay` / `--verificar`, y se actualizaron FR-122, H2-9 y el caso borde. Para que `--replay` llegue al error sin registrar el movimiento como acción, `partida.log` termina con una marca de cierre con el movimiento intentado.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

Aplicá los hallazgos del último analyze, sin tocar spec.md:
- I1: separar en T002, T050, contrato-datos.md (Validación) y plan.md los dos efectos de FR-122:
  esqueleto → la partida no inicia; ficha de la precarga → se detiene al intentar entrar a esa sala.
- C1: agregar la tarea de prueba test_h2_9_fr122_ficha_invalida_detiene_al_entrar, a mi cargo, usando
  una fuente de prueba que devuelva un error de formato para esa sala.
- E1: agregar tareas de coordinación: integrante 2 (Data distingue error de formato de error de red)
  e integrante 3 (Service termina la partida ante ese error). Anotarlo en la tabla de dependencias.
- I2: agregar H2-9 a la tabla de pruebas del plan.
- I3: quitar "Propuesto" en data-model.md y research.md.
- I4: marcar T001 y T039; actualizar la fila de ActorDTO (solo queda T038 pendiente).
- I6: agregar "campo (rango)" al contexto mínimo del mensaje. I7: quitar la fecha límite vieja.
- E2: en T014, indicar que equipar, recoger, soltar y abrir quedan cubiertos por las pruebas de P1.
Commit: "plan(001): FR-122 en plan, contrato y tareas tras analyze", incluyendo PROMPTS_LLM.md.

**Uso de la respuesta:** se usó en `tasks.md` (T002, T014 y T050 corregidas; T001 y T039 marcadas; tareas nuevas T052 y T053 de coordinación con los integrantes 2 y 3, y T054 con la prueba de H2-9), `plan.md` (dos efectos de FR-122, tabla de pruebas con H2-9, dependencias y estado de `ActorDTO`), `contracts/contrato-datos.md` (efectos de FR-122, campo `rango` en el mensaje y sin la fecha límite vieja), `data-model.md` y `research.md` (contrato confirmado).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

/speckit-analyze

**Uso de la respuesta:** segunda pasada de análisis de la feature 001. Los hallazgos anteriores quedaron resueltos; encontró que T052 y T053 modificaban código de P1 (Data y Service) sin justificarlo en la tabla de cambios del plan (Principio III), que cambiaban decisiones de P1 sin antes y después en `DECISIONES.md`, y que T052 no definía qué pasa con las otras salas del lote ni cómo se recuerda el rechazo. Llevó a simplificar FR-122.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

/speckit.clarify Simplificar FR-122 para fichas de la precarga (Principio III, KISS): si una ficha de
cazador con rango ausente o inválido llega con la precarga, Data la rechaza con un error de datos que
indica la ficha y el campo, y no la vuelve a pedir. Esa sala queda como contenido no disponible: si
el jugador intenta entrar, el movimiento se rechaza con ese mensaje, sin consumir tiempo ni
registrarse en partida.log, y la partida sigue. Esto reemplaza la regla de detener la partida y la
marca de cierre en el log. Los costos inválidos del esqueleto siguen impidiendo iniciar.
Actualizá FR-122, H2-9, el caso borde y Clarificaciones (motivo: evitar cambiar el formato del log y
el replay de P1). Commit solo de spec.md: "spec(001): FR-122 simplificado para fichas de la precarga".
Mostrame el cambio antes del commit.

Respuesta a la pregunta de Claude sobre la ficha que llega antes de iniciar: Limitalo: "si la ficha inválida es de un cazador de la sala inicial, la partida no inicia; para
cualquier otra sala, esa sala queda como contenido no disponible", llegue antes o durante la partida.
Después hacé el commit solo de spec.md: "spec(001): FR-122 simplificado para fichas de la precarga".

**Uso de la respuesta:** commit `31f8719`. En `specs/001-terreno-cazador/spec.md` se reemplazó la regla de detener la partida y la marca de cierre por la de «contenido no disponible»: entrar a esa sala se rechaza con el error de datos y la partida sigue; solo una ficha inválida de la sala inicial impide iniciar. Se actualizaron FR-122, H2-9, el caso borde y Clarificaciones (las dos respuestas anteriores quedaron marcadas como reemplazadas).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

Alinear plan, contrato y tareas con el FR-122 simplificado: quitar la marca de cierre y todo cambio
a partida.log, ServicioReplay y main.py. Reducir T052 a "Data rechaza la ficha con error de datos
con contexto (ficha, campo), distinguible del error de red, recuerda el rechazo por sala sin gastar
otra solicitud, y solo esa sala queda sin contenido". Reducir T053 a "Service muestra ese error de
datos al rechazar el movimiento, en lugar del mensaje de red". Ajustar T054 a "intentar entrar a esa
sala se rechaza con el mensaje y la partida sigue". En la tabla de cambios a código P1, una fila
para Data (T052, integrante 2) y una para Service (T053, integrante 3), ambas con FR-122.
Ajustar quickstart.md. Commit: "plan(001): FR-122 simplificado en plan, contrato y tareas",
con PROMPTS_LLM.md.

**Uso de la respuesta:** se usó en `tasks.md` (T002, T050, T052, T053 y T054 con la regla simplificada; la prueba pasa a llamarse `test_h2_9_fr122_ficha_invalida_rechaza_entrar`), `plan.md` (efectos de FR-122, filas de Data y Service en la tabla de cambios a P1, «No se tocan» con `partida.log`, `ServicioReplay` y `main.py`, dependencias), `contracts/contrato-datos.md` (efectos de FR-122) y `quickstart.md` (paso de datos inválidos).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

/speckit.implement Implementar T003 y la fase 2 (hasta su punto de control), en el orden de tasks.md.
Saltar T002, que es del integrante 2. Pruebas antes del código cuando la tarea lo indique.
Un commit por tarea: "feat(001): T0xx descripción [FR-…]", incluyendo PROMPTS_LLM.md en el primero.
Después de cada tarea, correr tests/correr_pruebas.py; si algo queda en rojo, detenerse y mostrarme
el error. En el punto de control de la fase 2, detenerse y mostrarme un resumen. No hacer push.

**Uso de la respuesta:** se implementaron T003 (`tests/ayudas_terreno.py`) y la fase 2 de `specs/001-terreno-cazador/tasks.md`: la prueba `tests/test_mazmorra_costos.py` (T004) y el costo por salida en `Logic/Mazmorra.py` (T005 a T007), un commit por tarea.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

/speckit.implement Implementar la fase 3 (Historia 1, T008 a T014), en el orden de tasks.md.
Pruebas antes del código. El rojo esperado de TDD está bien; detenete solo si falla una prueba que
ya existía antes de esta fase. Un commit por tarea: "feat(001): T0xx descripción [FR-…]".
Cada cambio a código de la primera entrega debe coincidir con su fila en la tabla de cambios a P1
del plan; si necesitás tocar algo que no está en esa tabla, detenete y avisame antes.
Al terminar la fase, correr tests/correr_pruebas.py y mostrarme un resumen. No hacer push.

**Uso de la respuesta:** commits `554cbf7` a `8bb7c08`. Pruebas de los escenarios H1-1 a H1-8 y de errante, rastreador y guardián con costos (T008, T009) en `tests/test_terreno_cazador.py`; `mover_jugador` paga el costo de la salida (T010); `Comportamiento.decidir_paso` y `Errante.decidir_paso` con el mismo sorteo de P1 (T011, T012); `turno_enemigo` programa con el costo de la salida (T013); verificación sin regresiones de P1 (T014).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

/speckit.implement Fase 4 de specs/001-terreno-cazador/tasks.md (T015–T026 y T054).

Orden dentro de la fase, si las dependencias de tasks.md lo permiten:
1. Primero T021 (FichaEnemigoDTO.rango: int | None = None, último campo).
2. Después la cola de prioridad y la búsqueda de ruta según contracts/busqueda-rutas.md
   (recibe el grafo como parámetro, solo salidas abiertas, costo ya igualado,
   desempate por menor id).
3. Al final la clase Cazador en COMPORTAMIENTOS, y agregá el caso del cazador
   a test_h4_2_fr117_actor_dto_trae_el_comportamiento (nota de T024).
4. T054 queda con skipTest hasta que exista T052 (integrante 2); dejá el motivo en el skip.

Reglas:
- Constitución v1.2.0: sin dict, set, heapq, bisect, collections ni copy en código del juego;
  sin sorted()/list.sort() en ordenamientos evaluados. Type hints y docstring breve.
- No toques código de la primera entrega fuera de lo que justifica la tabla
  "Cambios a código de la primera entrega" de plan.md. Si hace falta algo más, pará y avisame.
- Un commit por tarea o grupo pequeño, con el ID y los FR en el mensaje.
- tests/correr_pruebas.py en verde antes de cada commit; las 383 pruebas actuales no se modifican.
- No hagas push.
- Al terminar: lista de commits, total de pruebas y cualquier desvío del plan.

**Uso de la respuesta:** commits `6e147e8` a `f000aa2`. `FichaEnemigoDTO.rango` como último campo (T016, T021); `Estructuras/MonticuloMinimo.py` (T015, T020); `Logic/GrafoEsqueleto.py` y `Logic/BusquedaCostoMinimo.py` con `paso_desde_cero` (T017, T022, T023); la clase `Cazador`, `self.grafo` en `Motor.__init__` y el caso del cazador en `test_h4_2` (T018, T019, T024, T025); la prueba de H2-9 con `skipTest` hasta T052 y T053 (T054); verificación (T026). Quedaron 431 pruebas en verde y 1 omitida.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

/speckit-analyze

**Uso de la respuesta:** tercera pasada de análisis de la feature 001, después de implementar las fases 1 a 4. Encontró que faltaban estas tres entradas en `PROMPTS_LLM.md` (Principio XI), que T021 no coincide con la posición real de `rango`, que la tabla de cambios a P1 no menciona dos importaciones nuevas, y detalles sin documentar de la búsqueda (`_asegurar_tamano`, casos que devuelven `None` o lanzan `ValueError`, uso de `Mazmorra._existe`).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Miércoles 11 de noviembre 2026

**Herramienta:** Claude Code

que recomeindas para corregirlos

Respuesta tras la propuesta de Claude: Sí, aplicalo así en un solo commit, con U3 como lo propusiste (sin existe_sala() público).
Agregá la entrada en PROMPTS_LLM.md. Corré tests/correr_pruebas.py antes del commit. No hagas push.

**Uso de la respuesta:** se corrigieron los hallazgos menores del tercer `/speckit-analyze` sin tocar código: T021 dice que `rango` es el último campo (I1); `data-model.md` y una nota en T032 explican que los arrays de la búsqueda solo crecen (U1); la tabla de cambios a P1 del plan menciona las importaciones nuevas (I2); la tabla de pruebas incluye `GrafoEsqueleto` (I3); el contrato y `data-model.md` documentan los casos que devuelven `None` o lanzan `ValueError` (U2); T022 justifica el uso de `mazmorra._existe()` (U3).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Jueves 12 de noviembre 2026

**Herramienta:** Claude

Le pedí a Claude revisar las ramas de Marco y Kristel (pruebas, cambios y si las podía jalar), el Estado_001 de Marco y el plan y el contrato de la línea de tiempo de Kristel, y redactar las respuestas para cada uno. También le pedí preparar el prompt de /speckit-specify de mi parte de la spec 002 (mapa conocido y antorcha) y revisar el resultado contra el enunciado (§3.3, §5.3, §6.1 y Apéndice B), la constitución y el código de la primera parte (puertas de dos caras en Mazmorra) antes de cada paso.

**Uso de la respuesta:** se usó para jalar las ramas de Marco y Kristel a derek, para los mensajes de coordinación (contrato de datos, T052, contrato de la línea de tiempo y reparto de FR-2xx) y para definir el prompt, las correcciones y la respuesta de clarify de `specs/002-niebla-ir-a/spec.md`.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Jueves 12 de noviembre 2026

**Herramienta:** Claude Code

/speckit-specify SPECIFY_FEATURE_DIRECTORY=specs/002-niebla-ir-a

Niebla de guerra y mapa conocido de Cripta II (parte del integrante 2). Usa exactamente el directorio specs/002-niebla-ir-a. Puedes crear o actualizar .specify/feature.json (es local y está en el .gitignore); fuera de eso, no crees archivos fuera de specs/002-niebla-ir-a ni escribas código.

Numeración: esta spec la comparten dos integrantes. Esta parte (mapa conocido y antorcha) usa FR-201 a FR-249, NFR-201 a NFR-249 y SC-201 a SC-249. El rango FR-250 a FR-299 (y NFR/SC 250 a 299) queda reservado para «ir a», que escribe el integrante 3 en otro commit: deja una sección «Viaje automático «ir a» (§3.4) — FR-250 a FR-299: pendiente, la escribe el integrante 3» sin inventar requisitos. No empieces en 001.

Antes de escribir, lee .specify/memory/constitution.md (sobre todo los principios IX y X), specs/004-linea-tiempo/spec.md (FR-405 y FR-420, que usan el mapa conocido) y, del enunciado de la Parte II (Proyecto II parte.pdf): §3.3, §5.3, §6.1, §6.3 y el Apéndice B (sección «Niebla de guerra e «ir a»»). Escribe SOLO el QUÉ: reglas, historias de usuario, escenarios de aceptación y requisitos numerados. No nombres estructuras de datos, clases, módulos ni algoritmos.

Reglas (§3.3):
- Para el jugador, cada sala está en uno de tres estados. Explorada: el jugador entró a ella al menos una vez; la sala inicial está explorada desde el instante 0; el jugador conoce su nombre, sus salidas, el costo de cada salida y el estado de sus puertas según la última observación. Avistada: no está explorada, pero es destino de una salida de una sala explorada; el jugador solo sabe que existe una sala detrás de esa salida. Desconocida: ninguna de las anteriores; el jugador no sabe nada.
- Memoria de puertas: el jugador observa una puerta cuando está en cualquiera de las dos salas que conecta. El mapa recuerda el estado de cada puerta tal como estaba en su última observación, aunque haya cambiado después (por ejemplo, una puerta con cierre automático puede figurar abierta en el mapa y estar cerrada en realidad). Al volver a observarla, el mapa se actualiza.
- Antorcha (P1 §2.7): mientras esté encendida, al entrar a una sala también quedan exploradas todas sus vecinas, a través de cualquier salida, abierta o cerrada. Explorar una vecina de esta forma revela su nombre y sus salidas, no su contenido, y no activa sus enemigos ni sus trampas.
- Separación entre mapa y conocimiento: el programa sigue descargando el esqueleto completo, y la precarga y el cazador pueden usarlo (es infraestructura). Todo lo que la vista muestra y todo lo que usa «ir a» se deriva exclusivamente del conocimiento del jugador.
- El conocimiento del jugador es estado del juego: se guarda en el archivo de partida (al cargar, el mapa es idéntico al guardado), se revierte con el pergamino de retroceso (incluidas las salas exploradas por la antorcha y las puertas observadas en la acción revertida) y forma parte de la línea de tiempo (el resumen de historia de la spec 004 muestra el mapa conocido de ese instante).
- La interfaz ofrece un comando para ver el mapa conocido: salas exploradas (con sus salidas, costos y el estado recordado de sus puertas) y salas avistadas. Nunca muestra salas desconocidas ni información que el jugador no conoce.
- La misma partida (misma cripta, semilla y acciones) produce el mismo mapa conocido, también con --replay.

Rendimiento (§5.3, §6.1, §6.3):
- Consultar si una sala está explorada, avistada o desconocida, y consultar el estado recordado de una puerta, son operaciones frecuentes (en cada vista, en cada paso de «ir a» y en cada actualización por antorcha): su costo no debe depender del tamaño del mapa conocido ni de la cripta.
- Explorar nuevas salas cuesta proporcionalmente a las salas reveladas, no al tamaño del mapa conocido.
- Registrar e invertir un cambio del mapa (para el pergamino y la línea de tiempo) cuesta proporcionalmente a lo que cambió.
- --bench mide las consultas al mapa conocido y la exploración con antorcha, en criptas sintéticas deterministas por semilla de al menos tres tamaños (Principio VIII).

Historias de usuario (con prioridad): el jugador solo ve lo que ha explorado; recuerda las puertas como las vio por última vez; la antorcha explora las vecinas; el mapa se guarda, se revierte y se consulta en la línea de tiempo; el jugador consulta su mapa con un comando.

Escenarios de aceptación: incluye, en formato Dado/Cuando/Entonces y con su FR-2xx, estos casos del Apéndice B:
1. Con la antorcha encendida, entrar a una sala explora sus vecinas sin activar sus enemigos ni sus trampas.
2. Un pergamino revierte una entrada con la antorcha encendida: las salas exploradas por la antorcha vuelven a su estado anterior.
3. El mapa recuerda abierta una puerta que en realidad está cerrada: al observarla, el mapa se actualiza (la parte de «la ruta se recalcula y el viaje se detiene» es de «ir a», FR-25x).
Agrega además escenarios para: la sala inicial explorada en el instante 0 y sus vecinas avistadas; una puerta con cierre automático que figura abierta en el mapa y está cerrada en realidad; la antorcha apagada no explora vecinas; la antorcha explora a través de una salida cerrada; guardar y cargar conserva el mapa; el pergamino revierte la observación de una puerta; el comando de ver el mapa no muestra salas desconocidas; --replay produce el mismo mapa. Cada requisito funcional debe tener al menos un escenario.

Incluye una tabla «Trazabilidad del Apéndice B «Niebla de guerra e «ir a»»» con los 6 casos: los 2 de la antorcha y el pergamino (con sus escenarios), el de la puerta recordada abierta (la parte del mapa aquí; la de la ruta, «pendiente FR-25x, integrante 3») y los otros 3 («ir a» a una sala no explorada, «ir a» que entra a una sala con enemigos dormidos, un pergamino durante un viaje) marcados «pendiente FR-25x, integrante 3».

Si algo no está definido en el enunciado, márcalo con [NEEDS CLARIFICATION] en lugar de inventarlo. En particular: (a) al explorar una vecina con la antorcha, ¿el jugador conoce el estado de las puertas de esa vecina, si nunca estuvo en ella?; (b) encender la antorcha estando ya en una sala, ¿explora las vecinas de esa sala o solo al entrar a la siguiente?; (c) una sala que solo es destino de una salida sin vuelta, ¿queda avistada?

Fuera de alcance: «ir a» (FR-250 a FR-299, integrante 3); cómo se dibuja el mapa en la interfaz (integrante 3); el costo de las salidas y el cazador (spec 001); la línea de tiempo en sí (spec 004).

**Uso de la respuesta:** se usó para crear `specs/002-niebla-ir-a/spec.md` y `specs/002-niebla-ir-a/checklists/requirements.md` con mi parte (FR-201 a FR-224, NFR-201 a NFR-205, SC-201 a SC-206) y la sección de «ir a» reservada para el integrante 3. Dejó 3 marcadores [NEEDS CLARIFICATION] (FR-204, FR-212 y FR-215).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Jueves 12 de noviembre 2026

**Herramienta:** Claude Code

Respuestas y correcciones para specs/002-niebla-ir-a/spec.md. Edita SOLO ese archivo y su checklist; sin código ni nombres de estructuras, clases o módulos. Registra las respuestas en una sección «Clarificaciones» → «Sesión 2026-11-12», con el formato «P: … → R: …», como en las specs 001, 003 y 004, y quita los tres [NEEDS CLARIFICATION]. Todo lo que escribas en la spec, en español.

1. FR-212 (Q1 → A): las puertas de una vecina explorada con la antorcha que el jugador nunca observó figuran «sin observar» (estado desconocido) hasta que esté en una sala que tenga una cara de esa puerta; la puerta de la salida por la que es vecina sí se observa, porque el jugador está en la otra sala (FR-207). Una puerta «sin observar» no es una puerta recordada abierta (dato que usará «ir a», FR-25x). Ajusta FR-205 (el estado de cada puerta según la última observación, o «sin observar» si nunca se observó), FR-219 (el comando muestra las puertas sin observar como tales) y el escenario H3-6.

2. FR-215 (Q2 → A): la antorcha solo tiene efecto al entrar a una sala (§3.3: «al entrar a una sala»); encenderla estando ya en una sala no cambia el mapa conocido. Ajusta H3-7.

3. FR-204 (Q3 → C): X sigue desconocida. En la primera parte, una puerta con vuelta tiene una cara en cada una de las dos salas que conecta y es la misma puerta; una salida sin vuelta solo existe como salida de la sala de la que sale. Regla: el jugador observa las puertas que tienen una cara en la sala donde está; así, una puerta con vuelta se observa desde cualquiera de sus dos salas (§3.3) y una salida sin vuelta solo desde la sala de la que sale. Si se observara desde la otra sala, el jugador sabría que existe una sala desconocida (contradice FR-206). Ajusta FR-204, FR-207, el escenario H2-4 (la puerta de la salida sin vuelta de A hacia F se observa desde A, no desde F) y el caso borde «Puerta en una salida sin vuelta».

4. En «Convenciones de los ejemplos», cambia «Puede tener puerta o no» por: «Toda salida tiene una puerta, abierta o cerrada (P1); en una salida con vuelta, las dos caras son la misma puerta».

5. FR-220: confírmalo como requisito y regístralo en Clarificaciones (P: ¿ver el mapa conocido consume tiempo o cuenta como acción? → R: No; es una consulta, como historia en la feature 004: no consume tiempo, no es acción, no se registra en partida.log y no modifica el historial de retroceso). Quita esa suposición de «Suposiciones».

6. SC-206: la cripta de referencia todavía no está publicada (§6.1). Cámbialo a «medido con --bench en una cripta sintética determinista con decenas de enemigos activos y la antorcha encendida». NFR-205 se mantiene.

7. Actualiza la tabla de cobertura, las tablas de trazabilidad y el checklist. Al final dime exactamente qué cambiaste y confirma que no queda ningún [NEEDS CLARIFICATION], que no hay ningún FR-0xx y que todos los FR, del FR-201 al FR-224, tienen al menos un escenario.

**Uso de la respuesta:** se usó en `specs/002-niebla-ir-a/spec.md` para responder las 3 aclaraciones (puertas «sin observar» de una vecina explorada con la antorcha, la antorcha solo al entrar y la regla de las caras para las salidas sin vuelta), confirmar FR-220 y corregir las convenciones y SC-206.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Jueves 12 de noviembre 2026

**Herramienta:** Claude Code

/speckit-clarify

Respuesta a la única pregunta:
1. Si dos salidas de salas exploradas llevan a la misma sala avistada, ¿sabe el jugador que es la misma sala? → «A» (no: cada salida hacia una sala avistada se muestra por separado, sin identificador, hasta que se explora).

**Uso de la respuesta:** se usó en `specs/002-niebla-ir-a/spec.md`: una aclaración nueva en «Sesión 2026-11-12», cambios en FR-204 y FR-219, el escenario nuevo H5-5 y un caso borde.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Jueves 12 de noviembre 2026

**Herramienta:** Claude Code

Revisión cruzada de la spec 001 hecha por la integrante 3. Aplicá las correcciones en dos commits:

Commit 1, spec(001): correcciones tras revisión cruzada
- Escenarios nuevos para FR-119, FR-120, FR-121, FR-123, FR-122 (costo inválido o distinto entre caras;
  ficha inválida en la sala inicial), FR-118 (--verificar y --bench), FR-104 (rastreador y guardián),
  FR-108 (puertas con llave y cierre automático), FR-103 (todas las acciones que no son mover) y FR-115.
  Cada uno en la tabla de trazabilidad.
- FR-117 observable: junto al nombre de cada enemigo se muestra su comportamiento en texto, y el cazador
  lleva un marcador visual propio. FR-116: el costo se muestra junto a cada salida, también si está cerrada.
- Fuera de alcance: FR-118 depende de la spec 004 (--replay --hasta) y de la 003 (--verificar); la 002
  reutiliza la búsqueda de rutas.
- Quitar las respuestas "Reemplazada" de Clarificaciones.
- FR-114: mencionar que el pergamino de retroceso puede deshacer movimientos o puertas.
- Marcar como "decisión del grupo": igualar el costo de las dos caras, rango pequeño 200, SC-105,
  1000 salas y 30 cazadores, y la regla del rastreador con salidas repetidas.
- FR-108: escribir qué pasa si una puerta se cierra en el mismo instante que el turno del cazador,
  según el orden que el motor YA aplica (revisá el código; no inventes la regla).
- Formato: línea 194 "escenario 2.1" pasa a H2-1; caso 6 cita FR-102; frase cortada en "Datos inválidos";
  orden FR-116..FR-123; citar P1 §2.6 en Fuente; desmarcar el checklist hasta que esté cubierto.

Commit 2, test(001): pruebas de los escenarios nuevos
- Para cada escenario nuevo: si ya existe una prueba que lo cubre, solo agregá el ID del escenario al
  docstring. Escribí pruebas nuevas solo para las que falten.
- FR-118 --verificar/--bench: dejalas con skipTest y el motivo (spec 003 / fase 7).
- También T036 (test_h4_1_fr116...) sin skip, porque T038 ya está integrada; marcá T038 en tasks.md.

Antes de cada commit, suite en verde. Entrada en PROMPTS_LLM.md. No hagas push.
Al final: tabla escenario → prueba y la lista de lo que quedó con skip.

Respuesta a la pregunta de Claude (T038 no estaba en la rama Marco, solo en origin/kris y origin/derek):
Cherry-pick solo 888d763.

**Uso de la respuesta:** se trajo T038 con un cherry-pick de `888d763` (commit de Kris, `89efa22` en Marco). Commit `fa52f5a` (spec): escenarios H1-9 a H1-11, H2-10 a H2-19, H3-7 y H3-8 con su tabla de trazabilidad; FR-116 y FR-117 observables; regla de FR-108 tomada del motor (dos eventos con el mismo tiempo se atienden en el orden en que se programaron, por la secuencia de `ColaEventos`); fuera de alcance, decisiones del grupo, FR-114 con el pergamino y correcciones de formato; checklist desmarcado donde falta cobertura. Commit de pruebas: docstrings con el escenario en las pruebas que ya cubrían H1-10, H1-11, H2-10 a H2-14 y H2-16; pruebas nuevas para H1-9, H2-14 (ataque), H2-15 y T036; H2-17 a H2-19 con `skip` hasta T002, y H3-7 y H3-8 con `skip` hasta la spec 003 y la fase 7.
-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Jueves 12 de noviembre 2026

**Herramienta:** Claude Code

Revisión cruzada, SOLO LECTURA (no modifiques nada, no hagas commit): specs 002 y 003 del integrante 2,
en origin/derek (git fetch; leelas con git show origin/derek:specs/<carpeta>/spec.md).
Revisá contra la constitución v1.2.0 y el enunciado: Principio IX; Principio X (FR sin escenario y
Apéndice B); requisitos no verificables; clarificaciones contradictorias o reemplazadas; fuera de alcance
y dependencias con 001, 004 y entre 002 y 003; coherencia con la 001 (grafo de busqueda-rutas.md y
FR-122); cifras que son decisión del grupo; formato. Salida por spec con prioridad ALTA/MEDIA/BAJA,
archivo y línea, y una propuesta concreta por punto.

Corregí H3-7 de la 001 según tu propuesta, en dos commits:
1. spec(001): H3-7 alineado con 003 FR-302: --verificar no depende de costos ni cazadores;
   los errores de FR-122 hacen que no concluya (código 1). Actualizá la trazabilidad.
2. test(001): renombrá test_h3_7_fr118_verificar_aplica_las_mismas_reglas según el nuevo escenario
   (sigue con skip mientras no exista la 003).
Suite en verde con uv run, entrada en PROMPTS_LLM.md, no hagas push.

**Uso de la respuesta:** la revisión de las specs 002 y 003 (sin cambios en esas specs) encontró, entre otros puntos, que H3-7 de la 001 contradecía 003 FR-302. Commit `99bb5ff` (spec): H3-7, FR-118 y «Fuera de alcance» dicen que `--verificar` no depende de los costos ni de los cazadores y que los errores de FR-122 hacen que no concluya, con código 1; la trazabilidad de H3-7 cita FR-118 y FR-122. Commit de pruebas: la prueba pasa a llamarse `test_h3_7_fr118_fr122_verificar_no_depende_de_costos_ni_cazadores` y sigue con `skip` hasta que exista la 003.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Jueves 12 de noviembre 2026

**Herramienta:** Claude

Le pedí a Claude que me guiara con T002 y T052 de specs/001-terreno-cazador/tasks.md (FR-122 en Data, según contracts/contrato-datos.md): validar con el esqueleto completo los costos de las salidas (entero >= 1, sin aceptar bool, y los dos lados con el mismo costo si los dos lo declaran); rechazar la ficha de un cazador con rango ausente, null, no entero o negativo con un error de datos que se distinga del error de red; recordar el rechazo por sala sin gastar otra solicitud; y que solo esa sala quede sin contenido. Con pruebas que citen FR-122 y los casos de T050, sin tocar archivos de Marco ni de Kristel. Después le pedí analizar la rama de Marco (escenarios H2-17 a H2-19 con skip y su revisión de las specs 002 y 003) y decirme qué hacer primero.

**Uso de la respuesta:** se usó en `Data/ValidacionDatos.py` (nuevo: `ErrorDatos`, subclase de `ErrorRed`, y las reglas de FR-122), `Data/GestorEsqueleto.py` (`_validar_costos`: la partida no inicia), `Data/ResolvedorCatalogo.py` (una ficha inválida no se guarda ni se vuelve a pedir; `rechazo(id)`), `Data/GestorContenido.py` (estado `RECHAZADA` por sala: `asegurar_sala` vuelve a lanzar el mismo error sin otra solicitud y las demás salas del lote se cargan) y `tests/TestValidacionDatos.py` (20 pruebas). Revisé el cambio y corrí las pruebas: 460 OK (skipped=6) y 31/31 con la rama de Marco ya jalada; el replay de ejemplo sigue terminando en victoria con reloj 3625. También se usó para jalar la rama de Marco a derek (con PROMPTS_LLM.md resuelto a mano), para proponerle el cuerpo de las pruebas H2-17 a H2-19 y para las respuestas a su revisión.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Jueves 12 de noviembre 2026

**Herramienta:** Claude (Claude Code)

Lee .specify/memory/constitution.md y, en specs/001-terreno-cazador/tasks.md, T052 y T053. Implementa SOLO T053. En Service/ServicioAccionJugador.py, método ejecutar: agrega from Data.ValidacionDatos import ErrorDatos y, ANTES del except ErrorRed, agrega except ErrorDatos as error: que devuelva self._armador.armar_estado(contexto, str(error)) (ErrorDatos es subclase de ErrorRed, por eso va antes). El mensaje es el del propio error, sin el prefijo «Sin conexión con el servicio:». No cambies nada más de ese archivo. Justificación (Principio III): cambio indispensable para FR-122, escenario H2-9. Agrega una prueba corta en tests/test_servicios.py, siguiendo el estilo del archivo: con un contenido de prueba cuyo asegurar_sala lanza ErrorDatos, mover hacia esa sala devuelve un estado cuyo mensaje contiene el texto del error y no dice «Sin conexión», el jugador sigue en su sala, el reloj no avanza y la acción no queda en partida.log. Cita FR-122 y H2-9. NO toques tests/test_terreno_cazador.py ni quites el skip de T054 (la escribe el integrante 1), y no modifiques tasks.md. Corre python tests/correr_pruebas.py y reporta. Un solo commit: «feat(service): ServicioAccionJugador muestra el error de datos (T053, FR-122)».

**Uso de la respuesta:** ServicioAccionJugador muestra el error de datos (T053, FR-122) con su prueba.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Jueves 12 de noviembre 2026

**Herramienta:** Claude (Claude Code)

Edita SOLO specs/004-linea-tiempo/spec.md y su checklist si aplica. Sin estructuras, clases ni módulos.

1. P1 §2.11 dice que la reversión del pergamino no deshace los pergaminos recogidos o soltados durante el intervalo revertido. Agrégalo como requisito FR-424: «Los pergaminos de retroceso recogidos o soltados dentro de acciones revertidas conservan ese cambio: la línea de tiempo refleja la cantidad de pergaminos igual que la partida viva (P1 §2.11).» Agrega el escenario H3-5 (el jugador recoge un pergamino en la acción 4 y usa otro pergamino para revertirla; al consultar el instante actual, el inventario conserva el pergamino recogido y no tiene el consumido), con su fila de trazabilidad, citando FR-413, FR-419 y FR-424.
2. Si en FR-419 o Suposiciones hay alguna nota que trate ese caso como excepción o límite, elimínala.
3. Anota que FR-417 se integró en NFR-402 y que FR-422 se eliminó.
4. Verifica que no queden referencias rotas y dime qué cambiaste.

**Uso de la respuesta:** Se agregó FR-424 y el escenario H3-5 (pergaminos recogidos o soltados en acciones revertidas, P1 §2.11).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Jueves 12 de noviembre 2026

**Herramienta:** Claude (Claude Code)

Edita SOLO specs/004-linea-tiempo/plan.md, research.md, data-model.md, contracts/contrato-linea-tiempo.md y tasks.md. No escribas código ni cambies spec.md. Plan y modelo:

1. H-2 ya no es una decisión pendiente: es regla de P1 §2.11 (FR-424). El marcador de pergamino se generaliza: posición + quitados (ids de pergaminos que salen del inventario) + agregados (pergaminos que quedan en el inventario aunque la acción que los trajo se revirtió). El descuento del pergamino usado es un «quitado». Actualiza data-model.md, el contrato (MarcadorPergaminoDTO, con su validación al leer) y R-.. de research.md.
2. D1: la validación de rango (t entero ≥ 0 y no posterior al reloj; 1 ≤ k ≤ acciones del jugador) es regla de negocio: va en Logic/LineaTiempo, con métodos que lanzan ValueError con el motivo y el rango válido. ServicioLineaTiempo solo propaga (la constitución dice que Service no valida).
3. I1: en «Cambios a código de la primera entrega», el dueño de ConfiguracionDTO.py y LectorArgumentos.py es «Integrante 3 (con visto bueno del integrante 2)».
4. C2: agrega la fila de Service/BenchInventario.py (T061): cambio indispensable para exponer el bench nuevo sin tocar ServicioBench (del integrante 2); NFR-401.
5. Nota: la 004 no toca Service/ServicioAccionJugador.py; el único cambio es T053 de la feature 001 (un except ErrorDatos, FR-122), que no afecta a la línea. Logic/PartidaGuardada.py y DTO/PartidaGuardadaDTO.py los extiende Derek para el mapa conocido (spec 002, FR-223); la 004 solo agrega linea.
6. Los grabadores (resolvedor y contenido envueltos) delegan TODO lo que no es ficha() o asegurar_sala() al objeto original, incluidos rechazo() y resolver_contenido() (los usa GestorContenido, FR-122); un ErrorDatos propaga sin registrar nada.
7. El mapa conocido (spec 002) será un campo de PartidaGuardadaDTO que actualiza el motor, así los puntos de control y la re-simulación lo reproducen. La línea no lo invierte: NFR-203 de la 002 habla de invertirlo; aclara en el plan que la 004 reconstruye hacia adelante. Tareas:
8. I2: agrega T069 en la Fase 2, justo después de T010: crear CHECKPOINT_POR_DEFECTO = 20 y el campo checkpoint_cada en DTO/ConfiguracionDTO.py, con su prueba. T018 depende de T069; T050 queda con la bandera y el cableado.
9. I3: T021 aplica los registros de carga básicos; T032 solo agrega la regla del prefijo por ordinal.
10. H-2: T033 se escribe SIN skip (H3-5, FR-413, FR-424, FR-419). T034 pasa a ser tarea de implementación del marcador con quitados/agregados; ajusta T028, T030 y T031. Quita las menciones de «decisión pendiente» o de límite conocido en DECISIONES.
11. D1: T007 y T008 incluyen la validación de rango en LineaTiempo; T025 solo propaga el error.
12. C3: agrega «(FR-xxx)» a las tareas de 004 que no lo tienen (T001, T014, T018, T019, T021, T023, T028, T044, T053, T054, T056...). Ojo: el T053 de la 004 es de la interfaz, distinto del T053 de la 001.
13. P1: T066 se hace en un commit spec(004) aparte.
14. T004: la spec 002 ya existe; ajusta T004 a «coordinar con FR-223: el mapa conocido es campo de PartidaGuardadaDTO y se copia con PartidaGuardada.guardar, sin copy». Muestra los cambios.

**Uso de la respuesta:** Se ajustaron el plan, el modelo y las tareas de la 004 tras el analyze (validación en Lógica, T069, dueños de archivos).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Jueves 12 de noviembre 2026

**Herramienta:** Claude (Claude Code)

Edita SOLO specs/002-niebla-ir-a/spec.md, en la sección reservada para «ir a» (FR-250 a FR-299, NFR-250 a NFR-299, SC-250 a SC-299). No modifiques los FR-201 a FR-249 de Derek. Lee antes la constitución, la spec completa, y de Proyecto II parte.pdf §3.4, §6.1, §7.3 y el Apéndice B «Niebla de guerra e ir a». Solo el QUÉ: sin estructuras, clases, módulos ni algoritmos. Reglas (§3.4): «ir a <sala>» lleva al jugador a una sala explorada mediante movimientos ordinarios. La ruta usa solo salas exploradas y solo salidas que el mapa recuerda abiertas (una puerta «sin observar» no cuenta como recordada abierta); minimiza la suma de costos y desempata igual que el cazador (primer paso hacia la vecina de menor id). Cada paso es una acción completa del jugador que consume tiempo según §3.1, y entre pasos ocurren los eventos del reloj. La ruta se recalcula antes de cada paso con el conocimiento vigente. El viaje se detiene si llega al destino, entra a una sala con enemigos (activos o dormidos), recibe daño o deja de haber ruta conocida; la interfaz muestra el motivo. No abre puertas aunque el jugador tenga la llave. Un destino no explorado se rechaza sin consumir tiempo. En partida.log cada paso es un movimiento y la orden se registra además como comentario. El pergamino revierte solo el último paso y el viaje no continúa. Cada paso cuenta como acción del jugador en la línea de tiempo (spec 004). Rendimiento: el cálculo de un paso tarda menos de 5 ms con el mapa conocido completo (§6.1). Escenarios: los casos del Apéndice B de «ir a»: (1) destino no explorado, (2) puerta recordada abierta que en realidad está cerrada: la ruta se recalcula y, si no queda ruta, el viaje se detiene sin consumir tiempo adicional (la parte de que el mapa se actualiza ya es de la historia 1 de Derek), (3) enemigos dormidos: se activan según P1 §2.4 y el viaje se detiene, (4) pergamino durante un viaje. Usa historias H5 y H6. Cada escenario con su FR en la tabla de trazabilidad. Reemplaza únicamente los marcadores «pendiente FR-25x» por los FR concretos. Verifica que no queden referencias rotas y dime qué cambiaste.

**Uso de la respuesta:** Se escribieron FR-250 a FR-264 y las historias 6 y 7 de «ir a» en la spec 002, con los casos del Apéndice B.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Jueves 12 de noviembre 2026

**Herramienta:** Claude (Claude Code)

/speckit-analyze Enfócate en: (1) que cada FR y NFR tenga al menos una tarea; (2) que cada escenario de aceptación y cada caso del Apéndice B tenga una prueba que cite su FR; (3) que ninguna tarea ni el plan contradiga la constitución; (4) que ninguna tarea modifique código de otros integrantes sin marcarlo como «Coordinar»; (5) inconsistencias entre spec, plan y tasks.

**Uso de la respuesta:** Segundo informe, sin hallazgos críticos; dejó ajustes de texto y la mejora del diseño del pergamino.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

Correcciones a specs/003-resolubilidad/spec.md tras la revisión cruzada de Marco (integrante 1). Editá SOLO specs/003-resolubilidad/spec.md y su checklists/requirements.md; sin código y sin nombrar estructuras de datos, clases ni módulos. Todo en español. Antes de editar, leé .specify/memory/constitution.md (principios IX y X), specs/001-terreno-cazador/spec.md (FR-101, FR-122, el escenario H3-7 y «Fuera de alcance») y, solo para entender la regla de las caras de la primera parte, Logic/Mazmorra.py (_igualar_caras y abrir_puerta).

1. Llaves distintas en las dos caras de una puerta (FR-302, escenario H2-9, casos borde y Clarificaciones):
   - Ya NO es un error de datos. Regla nueva, igual que en la primera parte: si las dos caras declaran llave, cada cara se rige por lo que declara (su llave, su estado cerrado y su cierre automático); para atravesar la puerta desde una sala hace falta la llave que declara la cara de esa sala. Una cara cerrada sin llave sigue sin poder atravesarse en ese sentido.
   - Por qué (escribilo en la aclaración): en la primera parte, una cara que declara su propia llave no se iguala con la otra, así que el juego ya permite esa puerta, y el enunciado no dice que sea inválida. Los costos distintos entre caras sí son error (001 FR-122) porque §3.1 dice que el costo es el mismo en ambos sentidos; para las llaves no existe esa regla.
   - Clarificaciones: quitá la pregunta de la Sesión 2026-11-11 sobre llaves distintas y agregá una sección «Sesión 2026-11-12» con la pregunta y la respuesta nuevas, indicando que surge de la revisión cruzada del integrante 1. No dejes respuestas marcadas como «Reemplazada» (es la convención de la spec 001).
   - Reescribí el escenario H2-9 para la regla nueva con la puerta 2–6: la cara de la sala 2 requiere A y la de la sala 6 requiere B; con la sala 2 alcanzable, A obtenible y B no, la sala 6 es alcanzable entrando por la cara de la sala 2, la verificación concluye y no se informa ningún error de datos. Si en cambio A no es obtenible, la puerta 2–6 aparece en la frontera bloqueada con la llave A (la de la cara de la sala alcanzable).
   - Actualizá el caso borde «Las dos caras de una puerta declaran llaves distintas» y cualquier otra mención (requisitos, supuestos, tablas).

2. Errores de datos del esqueleto definidos en 001 FR-122 (un costo no entero o menor que 1, o costos distintos entre las dos caras de una salida). Agregá un requisito nuevo, FR-323: con un esqueleto que tenga uno de esos errores, la verificación NO DEBE concluir; --verificar DEBE terminar con el código de salida 1 (FR-314), mostrar el error con contexto y no caerse; y la partida NO DEBE iniciar, ni siquiera con --forzar, porque la feature 001 exige que con esos datos la partida no inicie y el juego supone datos válidos (a diferencia de FR-320, donde --forzar sí permite jugar). El costo sigue sin afectar el veredicto (FR-302). Agregá un escenario en la Historia 3 (--verificar con una salida de costo 0 → código 1 y ningún veredicto) y otro en la Historia 4 (iniciar con --forzar una cripta cuya salida declara costos distintos en sus dos caras → la partida no inicia). Agregá el caso borde y una aclaración en «Sesión 2026-11-12». Citá 001 FR-122 e indicá que concuerda con el escenario H3-7 de la 001.

3. Actualizá la tabla «Cobertura de requisitos funcionales», la trazabilidad y el checklist. No cambies la numeración de los FR que ya existen ni la tabla del Apéndice B.

Al final decime exactamente qué cambiaste y confirmá: que no queda ninguna mención de las llaves distintas como error de datos; que FR-323 tiene al menos un escenario; que todos los FR del FR-301 al FR-323 tienen escenario; y que no hay ningún [NEEDS CLARIFICATION]. No hagas commit.

**Uso de la respuesta:** se usó en `specs/003-resolubilidad/spec.md` y `specs/003-resolubilidad/checklists/requirements.md`, a partir de la revisión cruzada del integrante 1. Las llaves distintas en las dos caras de una puerta dejan de ser error de datos (cada cara se rige por lo que declara, como `Mazmorra._igualar_caras` de la primera parte): FR-302, FR-308, escenario H2-9 reescrito y aclaración en la Sesión 2026-11-12. Nuevo FR-323: un error de datos de 001 FR-122 en el esqueleto hace que la verificación no concluya (`--verificar` con código 1) y la partida no inicia ni con `--forzar` (escenarios H3-8 y H4-5); se ajustaron FR-312, FR-314, casos borde, supuestos, la tabla de cobertura y el checklist. Revisé con Claude el cambio contra el enunciado y el código de la primera parte antes del commit.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

Correcciones a specs/002-niebla-ir-a/spec.md, solo en la parte del integrante 2 (mapa conocido y antorcha: FR-201 a FR-249, NFR-201 a NFR-249, SC-201 a SC-249, historias 1 a 5), tras la revisión cruzada del integrante 1 y lo acordado con el integrante 3. NO modifiques la sección «Viaje automático «ir a»» (FR-250 a FR-299), ni las historias 6 y 7, ni sus filas de las tablas: son del integrante 3. Editá SOLO specs/002-niebla-ir-a/spec.md y su checklists/requirements.md; sin código y sin nombrar estructuras de datos, clases, métodos ni módulos. Todo en español. Antes de editar, leé .specify/memory/constitution.md (principios IX y X), specs/001-terreno-cazador/spec.md (FR-101), specs/003-resolubilidad/spec.md (FR-313) y specs/004-linea-tiempo/spec.md (cómo se reconstruye un instante), y la sección «ir a» de esta misma spec (FR-252 y FR-253).

1. FR-225 (nuevo): el mapa conocido DEBE ofrecer a «ir a» exactamente lo que necesitan FR-252 y FR-253: para cada sala explorada, sus salidas hacia otras salas exploradas cuya puerta el mapa recuerda abierta (una puerta «sin observar» no cuenta, FR-212; una salida hacia una sala avistada o desconocida tampoco), cada una con su costo igualado según 001 FR-101; y cada sala identificada por su identificador real, para que el desempate por menor identificador de FR-253 dé el mismo resultado que la búsqueda del cazador aplicada a ese mismo conjunto de salas y salidas. No nombres operaciones ni estructuras: eso va en el plan. Agregá un escenario en la Historia 1 o la 2 que lo pruebe: salas exploradas A, B y C, con la puerta A–B recordada abierta y costo declarado 150 solo en la cara de B, la puerta A–C «sin observar» y una salida de A hacia una sala avistada D; el mapa ofrece A→B con costo 150 y no ofrece A→C ni A→D.

2. FR-205 y FR-219: el costo de cada salida que se conoce y se muestra DEBE ser el costo igualado según 001 FR-101 (el mismo en los dos sentidos aunque solo una cara lo declare, y 100 si ninguna lo declara), no el declarado por una sola cara. Ajustá los escenarios que muestran costos si hace falta.

3. FR-217: agregá una excepción explícita. El reporte de resolubilidad (spec 003, FR-313) DEBE mostrarse completo al iniciar la partida, como exige §7.3, aunque mencione salas, puertas o ubicaciones de llaves que el jugador no conoce; no es parte del mapa conocido, NO DEBE modificarlo (no explora ni avista ninguna sala ni cambia el estado recordado de ninguna puerta) y «ir a» no lo usa. Motivo: §3.3 dice que la vista solo muestra el conocimiento del jugador, pero §7.3 exige ver el reporte al iniciar, y el reporte de §3.5 nombra salas y llaves; el choque solo aparece cuando la cripta no es resoluble y se inicia con --forzar. Acordado con el integrante 3, dueña de la interfaz. Agregá un escenario en la Historia 5: con una cripta no resoluble iniciada con --forzar, el reporte nombra salas desconocidas y, después de mostrarlo, el mapa conocido sigue teniendo solo la sala inicial explorada y sus vecinas avistadas.

4. NFR-203: las inversas son solo para el pergamino. Registrar un cambio del mapa conocido e invertirlo con el pergamino DEBE costar proporcionalmente a lo que cambió, no al tamaño del mapa conocido (§5.3). Para la línea de tiempo (feature 004), el mapa conocido NO necesita inversas: se reconstruye hacia adelante, porque forma parte del estado de la partida que se copia en cada punto de control y que la re-simulación reproduce (FR-221, FR-223, FR-224); esa copia cuesta proporcionalmente al tamaño del mapa conocido y se hace una vez por punto de control. Acordado con el integrante 3. Revisá que FR-222 y FR-223 sigan siendo coherentes con esto.

5. Agregá una sección «Sesión 2026-11-13» en Clarificaciones con una pregunta y respuesta por cada uno de los puntos 1 a 4, indicando de dónde salen (revisión cruzada del integrante 1 o acuerdo con el integrante 3). No marques nada como «Reemplazada».

6. Actualizá la tabla de trazabilidad y cobertura (solo tus filas y las filas nuevas), los casos borde si corresponde y el checklist. No cambies la numeración de los FR que ya existen ni la tabla del Apéndice B.

Al final decime exactamente qué cambiaste y confirmá: que no tocaste nada de FR-250 a FR-299 ni de las historias 6 y 7; que FR-225 tiene al menos un escenario; que todos los FR del FR-201 al FR-225 tienen escenario; y que no hay ningún [NEEDS CLARIFICATION]. No hagas commit.

Seguimiento en la misma conversación:

Ajustes finales de texto en specs/002-niebla-ir-a/spec.md y specs/002-niebla-ir-a/checklists/requirements.md, sin cambiar ningún requisito ni escenario:
1. En el encabezado, «Estado» ya no debe decir que la parte de «ir a» está pendiente: la escribió el integrante 3 (FR-250 a FR-264, historias 6 y 7).
2. En «Reparto de la numeración», cambiá «que escribe el integrante 3 en otro commit» por «que escribió el integrante 3 en su propio commit».
3. En «Fuera de alcance», quitá «el comando «ir a» (FR-250 a FR-299, integrante 3);» porque ahora es parte de esta spec. Lo demás de esa línea queda igual.
4. En el checklist, cambiá la línea «La sección «ir a» (FR-250 a FR-299) queda pendiente a propósito: la escribe el integrante 3.» por una que diga que la sección «ir a» la escribió el integrante 3 en su propio commit.
5. Sí, reacomodá la línea larga de FR-219 al mismo ancho que las demás, sin cambiar el texto.
No toques nada más y mostrame exactamente qué líneas cambiaste. No hagas commit.

Seguimiento en la misma conversación (puntos MEDIA y BAJA de la revisión cruzada del integrante 1):

Segunda tanda de correcciones en specs/002-niebla-ir-a/spec.md y su checklist, con los puntos MEDIA y BAJA de la revisión cruzada del integrante 1 (los de prioridad ALTA ya están hechos). Mismas reglas: solo la parte del integrante 2; no toques FR-250 a FR-299, ni las historias 6 y 7, ni sus filas de las tablas; sin nombrar estructuras de datos, clases ni módulos; no renumeres FR ni escenarios existentes (los escenarios nuevos van al final de cada historia). Antes leé, solo para entender la primera parte, Logic/Mazmorra.py (_igualar_caras y abrir_puerta) y Logic/EventoPorg.py (__lt__), y specs/001-terreno-cazador/spec.md (FR-108, NFR-101 y SC-104).

1. Caras con estados distintos (punto 4 de la 003 en la revisión). En la primera parte, las dos caras de una puerta pueden tener estados reales distintos: si ninguna declara llave y solo una está cerrada, o si las dos declaran llaves distintas, cada cara se rige por lo suyo (la 003 ya lo dice en FR-302). Hoy la 002 dice que las dos caras «son la misma puerta» con un solo estado. Corregilo así: en Convenciones, la puerta de una salida con vuelta tiene dos caras que normalmente tienen el mismo estado, pero pueden diferir según la primera parte; el estado recordado se guarda por cara; al observar una puerta (FR-207) el mapa registra el estado real de cada una de sus caras; y una salida cuenta como recordada abierta solo si se recuerda abierta la cara de la sala de la que sale (esto es lo que usa FR-225). Ajustá FR-207, FR-208, FR-225 y la entidad «Estado recordado de una puerta». Agregá un escenario al final de la Historia 2: la puerta A–B con la cara de A cerrada sin llave y la cara de B abierta; al observarla, el mapa recuerda A→B cerrada y B→A abierta, y a «ir a» solo se le ofrece B→A. Agregá la pregunta y la respuesta en la «Sesión 2026-11-13» que ya existe, indicando que surge de la revisión del integrante 1 y que es la regla de la primera parte.

2. Punto 4: marcá «(decisión del grupo)» en la aclaración y en FR-207 sobre la observación de las salidas sin vuelta solo desde la sala de la que salen, citando que evita contradecir FR-206.

3. Punto 5: agregá SC-207: «Con `--bench`, registrar e invertir con el pergamino la misma cantidad de cambios del mapa conocido varía menos de un factor 2 entre un mapa conocido pequeño y uno al menos 10 veces mayor *(decisión del grupo)*.»

4. Punto 6: reescribí SC-202 para que sea comprobable: en cada acción de una partida de prueba de al menos 200 acciones *(decisión del grupo)*, con y sin antorcha, lo que la interfaz recibe para dibujar el mapa (vista, comando de ver el mapa y resumen de `historia`) no contiene el identificador, el nombre, las salidas ni el contenido de ninguna sala desconocida, ni más que la existencia de las avistadas; se comprueba automáticamente. Mantené la excepción del reporte de resolubilidad (FR-217).

5. Punto 7: SC-206 debe usar la misma cripta de referencia que la 001 (NFR-101 y SC-104: una cripta sintética de 1 000 salas en cuadrícula con 30 cazadores activos), con la antorcha encendida *(decisión del grupo)*.

6. Punto 8: reemplazá el caso borde «La antorcha se apaga en el mismo instante en que el jugador entra» por la regla concreta: los eventos con el mismo tiempo se atienden en el orden en que se programaron (la misma regla de 001 FR-108); si el fin de la antorcha se programó antes que la acción del jugador, la entrada ocurre con la antorcha apagada y no explora las vecinas; si se programó después, las explora. Agregalo también como escenario al final de la Historia 3.

7. Punto 9: agregá un escenario para la parte del cazador de FR-218: un cazador que se mueve por salas desconocidas no cambia el estado de ninguna sala para el jugador ni el estado recordado de ninguna puerta.

8. Punto 10: en «Fuera de alcance», agregá que la verificación de resolubilidad (003-resolubilidad) usa el esqueleto completo y no el mapa conocido, y que su reporte se muestra según la excepción de FR-217.

9. Punto 11: marcá «(decisión del grupo)» en SC-203 y SC-204 (factor 2 y al menos 10 veces mayor), en NFR-204 (al menos tres tamaños) y en la aclaración sobre la sala avistada sin identificador.

10. Punto 12: en NFR-205, la cita queda «P1 §5.2 y §6.1 de la Parte II».

11. Punto 13: en «Fuente» agregá §3.4, §3.5, §3.6 y §7.3 de la Parte II, P1 §5.2 y la feature 001 (FR-101, FR-108 y FR-122).

12. Punto 14: reacomodá las líneas cortadas de FR-204 y FR-214 al mismo ancho que las demás, sin cambiar el texto.

13. Punto 15: en la tabla del Apéndice B el «#» 2 está repetido: cambialo por «2a» y «2b» (solo la etiqueta; no cambies el contenido de ninguna fila). La segunda tabla ya dice que sus escenarios no provienen del Apéndice B: dejala como está.

14. Punto 17: en H1-6, unificá la cita en «(FR-203, FR-222)».

Actualizá la tabla de trazabilidad (filas nuevas al final) y el checklist con una nota de esta tanda. Al final decime exactamente qué cambiaste y confirmá: que no tocaste FR-250 a FR-299, las historias 6 y 7 ni sus filas (salvo la etiqueta «2a/2b»); que todos los FR del FR-201 al FR-225 siguen teniendo escenario; y que no hay ningún [NEEDS CLARIFICATION]. No hagas commit.

**Uso de la respuesta:** se usó en `specs/002-niebla-ir-a/spec.md` y `specs/002-niebla-ir-a/checklists/requirements.md` (solo la parte del integrante 2), a partir de la revisión cruzada del integrante 1 y de lo acordado con el integrante 3: nuevo FR-225 (lo que el mapa conocido ofrece a «ir a»: salidas entre salas exploradas con la cara recordada abierta, costo igualado e identificador real); FR-205 y FR-219 con el costo igualado de 001 FR-101; excepción explícita en FR-217 para el reporte de resolubilidad de 003 FR-313 y SC-202 reescrito; NFR-203 con inversas solo para el pergamino y FR-223 con la reconstrucción hacia adelante; estado recordado por cara (regla de caras de la primera parte); SC-207 nuevo; SC-206 con la cripta de referencia de la 001; la regla de eventos simultáneos para la antorcha; escenario del cazador para FR-218; decisiones del grupo marcadas; encabezado, fuente y formato al día. No se tocó la sección «ir a» del integrante 3. Revisé con Claude el cambio antes del commit.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

Segunda tanda de correcciones a specs/003-resolubilidad/spec.md y su checklist, con los puntos MEDIA y BAJA de la revisión cruzada del integrante 1. Los puntos ALTA ya están hechos; su punto 1 ALTA (tratar las llaves distintas como error) quedó descartado: cada cara se rige por su llave, como en la primera parte. Editá SOLO esos dos archivos; sin código y sin nombrar estructuras de datos, clases ni módulos; no renumeres FR ni escenarios existentes (los escenarios nuevos van al final de cada historia). Antes leé specs/002-niebla-ir-a/spec.md (FR-217 y su excepción) y specs/001-terreno-cazador/spec.md (FR-122 y NFR-101).
 
1. Punto 2 (lo que falta): agregá en los supuestos que los errores de `rango` de 001 FR-122 no afectan la verificación, porque la verificación no descarga el contenido de las salas (FR-301); un cazador inválido en la sala inicial impide iniciar la partida por 001 FR-122, no por la verificación.

2. Punto 3: en FR-313, decí que mostrar el reporte completo al iniciar es la excepción de 002 FR-217: el reporte no forma parte del mapa conocido ni lo modifica.

3. Punto 4: agregá un escenario al final de la Historia 2 para una puerta cuyas caras tienen estados distintos sin llave: la puerta 3–7 con la cara de la sala 3 cerrada sin llave y la cara de la sala 7 abierta, la sala 3 alcanzable y la 7 sin otro acceso; la sala 7 no es alcanzable. Y si la sala 7 fuera alcanzable por otro camino, desde ella sí se llega a la 3 (FR-302).

4. Punto 5: un escenario para cada uno: FR-308, una salida sin vuelta que va de una sala de afuera hacia la región alcanzable no aparece en la frontera bloqueada; FR-310, dos ciclos independientes aparecen los dos, cada uno con sus llaves dependientes, en un orden determinista; FR-314, `--verificar` junto con `--forzar` da el mismo resultado y el mismo código de salida que sin `--forzar`.

5. Punto 6: reescribí SC-305: «En todas las criptas no resolubles de prueba, el reporte contiene, para cada llave no obtenible, su id y todas sus ubicaciones o «sin ubicación»; para cada puerta de la frontera, sus dos salas y su llave; y, si hay ciclo, la secuencia completa hasta volver a la primera llave. Se comprueba automáticamente.»

6. Punto 7: en SC-307, cambiá «crece de forma claramente mayor» por un umbral concreto: el tiempo de la alternativa de repetir el recorrido por cada llave crece al menos el doble de lo que crece el de la verificación *(decisión del grupo)*. Actualizá el supuesto que explica SC-307.

7. Punto 8: en NFR-301 y SC-306, «la cripta publicada más grande» pasa a «la cripta publicada más grande o, mientras no esté publicada, una cripta sintética determinista de 1 000 salas en cuadrícula con 100 llaves encadenadas *(decisión del grupo)*».

8. Punto 9: FR-313 debe ser observable: el resultado se muestra antes de la primera acción del jugador.

9. Punto 10: en H4-1, cambiá «ni se crea estado de partida» por «no se crea `partida.log` ni archivo de guardado y el reloj no avanza».

10. Punto 11: en FR-310, «junto con el ciclo» pasa a «inmediatamente después del ciclo, indicando la llave del ciclo de la que dependen».

11. Punto 12: marcá «(decisión del grupo)» en: los códigos de salida 0, 3 y 1 (aclaración y FR-314), el orden con todas las llaves obtenibles (FR-305), que «sin ubicación» no es error de datos (FR-321), las copias múltiples de una llave (FR-316), SC-303, SC-307 y NFR-304.

12. Punto 13: en «Fuera de alcance», agregá que la verificación tampoco corre con `--replay … --hasta` de la feature 004 (FR-301).

13. Punto 14: en H2-1, aclará que en ese escenario `sala_salida` es la 5 y la puerta 4–5 es la puerta de salida (así coincide con el caso del Apéndice B: «llave_salida está detrás de la única puerta que ella misma abre»), y no la puerta 8–9 de las Convenciones.

14. Punto 16: cambiá el encabezado «Supuestos» por «Suposiciones», como en las specs 002 y 004.

Actualizá la tabla de cobertura y el checklist. Al final decime exactamente qué cambiaste y confirmá: que todos los FR del FR-301 al FR-323 siguen teniendo escenario; y que no hay ningún [NEEDS CLARIFICATION]. No hagas commit.

Seguimiento en la misma conversación:

Dos ajustes más en specs/003-resolubilidad/spec.md (y en el checklist si corresponde), sin renumerar nada:
1. En H4-5, cambiá «no se consume tiempo virtual ni se crea estado de partida» por la misma redacción de H4-1: «no se crea `partida.log` ni archivo de guardado y el reloj no avanza».
2. FR-308: una salida cerrada sin llave que va de una sala de la región alcanzable hacia una sala fuera de ella también es parte de la frontera bloqueada, y en el reporte DEBE indicarse «sin llave: no se puede abrir» en lugar de una llave. Agregalo a FR-308 y completá H2-10: en el primer caso, la frontera bloqueada lista la puerta 3–7 con esa indicación. Actualizá el caso borde que corresponda y la tabla de cobertura (FR-308 suma H2-10).
Decime exactamente qué líneas cambiaste. No hagas commit.

Seguimiento en la misma conversación:

Sí, en SC-305 cambiá «para cada puerta de la frontera, sus dos salas y su llave» por «para cada puerta de la frontera, sus dos salas y su llave o «sin llave: no se puede abrir»». No toques nada más y decime la línea que cambiaste. No hagas commit.

**Uso de la respuesta:** se usó en `specs/003-resolubilidad/spec.md` y `specs/003-resolubilidad/checklists/requirements.md`, con los puntos MEDIA y BAJA de la revisión cruzada del integrante 1: suposición sobre los errores de `rango` de 001 FR-122; FR-313 observable y como excepción de 002 FR-217; escenarios nuevos H2-10 (caras con estados distintos sin llave), H2-11 (salida sin vuelta hacia adentro), H2-12 (dos ciclos independientes) y H3-9 (`--verificar` con `--forzar`); FR-308 y SC-305 con las puertas cerradas sin llave en la frontera («sin llave: no se puede abrir»); FR-310 más preciso; SC-305 y SC-307 medibles; cripta sintética de referencia en NFR-301 y SC-306; H4-1 y H4-5 observables; H2-1 con `sala_salida` 5 como en el Apéndice B; marcas «(decisión del grupo)»; «Suposiciones». El punto 1 ALTA (llaves distintas como error) quedó descartado. Revisé con Claude el cambio antes del commit.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

Correcciones de la segunda revisión del integrante 1 en specs/003-resolubilidad/spec.md y specs/002-niebla-ir-a/spec.md (y sus checklists). Mismas reglas de siempre: sin código y sin nombrar clases ni módulos; no renumeres FR ni escenarios; los escenarios nuevos van al final de su historia; en la 002 no toques el contenido de FR-250 a FR-299 ni de las historias 6 y 7. Antes leé, solo para entender la primera parte, Logic/Mazmorra.py (abrir_puerta, _igualar_caras y CierrePuerta) y Logic/motorJuego.py (dónde se declara la victoria), y §3.5 de «Proyecto II parte.pdf».

Spec 003:
1. FR-304: mantené la definición de §3.5, que es literal del enunciado, y precisá que la puerta por la que se llega a sala_salida debe estar cerrada y que llave_salida la pide la cara de la sala desde la que se entra a sala_salida (en la primera parte, la llave que vale al abrir es la de la cara desde la que se abre). Ajustá FR-322 de la misma forma.
2. Agregá una «Sesión 2026-11-13» en Clarificaciones (revisión del integrante 1): el motor de la primera parte declara la victoria al entrar a sala_salida después de abrir cualquier puerta que pida llave_salida, aunque esa puerta no lleve a sala_salida; en cambio §3.5 y P1 §2.12 exigen llegar a sala_salida a través de una puerta que la requiere. La verificación sigue el enunciado (FR-304). La diferencia solo aparece en una cripta donde sala_salida se alcanza sin pasar por una puerta que pida llave_salida: ahí la verificación dice «no resoluble», con el motivo de FR-322, aunque el motor permitiría ganar. Queda como coordinación con el integrante 1 (alinear el motor con P1 §2.12 es decisión suya). Agregá el caso borde.
3. FR-302, cierres automáticos: en la primera parte, abrir una puerta abre sus dos caras, y el cierre automático que se programa es el de la cara desde la que se abrió, y cierra las dos caras. Corregí FR-302 y la aclaración de la Sesión 2026-11-12 donde dice que cada cara se rige por «su cierre automático»: cada cara se rige por su llave y su estado cerrado; el cierre automático es el de la cara que se abre y afecta a las dos.
4. El supuesto de §3.5 «los cierres automáticos no bloquean, porque una puerta puede volver a abrirse con la misma llave» se mantiene porque es del enunciado. Agregá un caso borde marcado *(decisión del grupo)*: con llaves distintas por cara, después de un cierre automático volver por esa puerta puede exigir la llave de la otra cara; la verificación igual aplica el supuesto de §3.5 y no lo considera un bloqueo.
5. FR-321: agregá al escenario H2-7 que, con --verificar, el código de salida es 1.
6. FR-313: quitá «DEBE quedar disponible para que la interfaz lo muestre» y dejá que el resultado DEBE mostrarse antes de la primera acción del jugador. Agregá qué pasa sin vista: el único modo sin vista que verifica es --verificar, que escribe el resultado en la salida estándar (FR-314); --replay y --bench no verifican (FR-301).

Spec 002:
7. En Convenciones («Puerta») y en la aclaración de la Sesión 2026-11-13 sobre las caras: las caras también pueden diferir si las dos declaran llave (la misma o distintas) con distinto estado cerrado, porque la primera parte no iguala dos caras que declaran llave. Dejalo así: «si ninguna declara llave y solo una está cerrada, o si las dos declaran llave (la misma o distintas) con distinto estado», alineado con 003 FR-302.
8. FR-225: reacomodá la línea cortada («desconocida. Cada sala»), sin cambiar el texto.
9. La segunda tabla de trazabilidad (escenarios adicionales) usa números que parecen casos del Apéndice B: cambiá su columna «#» por «Adicional» y numerá sus filas A1, A2… en el mismo orden. Incluye las filas del integrante 3: solo cambia la etiqueta, no el contenido.
10. En el caso borde del reporte de resolubilidad con --forzar, la referencia «(003, escenario de --forzar)» pasa a «(003 H4-4)».

Actualizá las tablas de cobertura y los checklists. Al final decime exactamente qué cambiaste en cada spec y confirmá: que no renumeraste FR ni escenarios; que no tocaste el contenido de FR-250 a FR-299 ni de las historias 6 y 7; y que no hay ningún [NEEDS CLARIFICATION]. No hagas commit.

Seguimiento en la misma conversación:

Ajuste en la aclaración de la Sesión 2026-11-13 de specs/003-resolubilidad/spec.md sobre el motor de la primera parte (y en su caso borde): el integrante 1 decidió mantener el motor como está, porque cambiarlo sería tocar la primera parte sin un FR que lo pida, y la diferencia va hacia el lado seguro: la verificación puede rechazar una cripta que el motor dejaría ganar (para eso está --forzar), pero nunca aprueba una que el motor no deje ganar. Queda registrado en DECISIONES.md como diferencia conocida entre la verificación y el motor. Reemplazá la frase de que alinear el motor es decisión del integrante 1 por esto. No toques nada más y decime qué líneas cambiaste. No hagas commit.

**Uso de la respuesta:** se usó en `specs/003-resolubilidad/spec.md`, `specs/002-niebla-ir-a/spec.md` y sus checklists, con la segunda revisión cruzada del integrante 1. En la 003: FR-304 y FR-322 precisan que la puerta hacia `sala_salida` está cerrada y que `llave_salida` la pide la cara de la sala desde la que se entra; aclaración y caso borde sobre la diferencia con el motor de la primera parte (el integrante 1 decidió mantenerlo; va hacia el lado seguro); FR-302 corregido (el cierre automático es el de la cara que se abre y cierra las dos) y caso borde del supuesto de §3.5 con llaves distintas por cara; código 1 en H2-7; FR-313 observable y sin vista; FR-301 y FR-314 ajustados. En la 002: las caras también difieren con la misma llave y distinto estado; FR-225 reacomodado; tabla de escenarios adicionales con etiquetas A1 a A43; referencia «003 H4-4». No se tocó la sección «ir a» del integrante 3 salvo las etiquetas. Revisé con Claude el cambio antes del commit.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

/speckit-plan Plan de la feature 003-resolubilidad (integrante 2). Antes de planificar, leé: .specify/memory/constitution.md; specs/003-resolubilidad/spec.md completa; «Proyecto II parte.pdf» §3.5, §4.2, §4.3, §5.4, §6.1, §6.3 y §7.3; el plan y los contracts de specs/001-terreno-cazador y de specs/004-linea-tiempo, solo como modelo de formato; y el código real que vas a usar o tocar: Data/FuenteDatos.py, FuenteJson.py, FuenteRed.py, FuenteOffline.py, DescargadorPaquete.py, GestorEsqueleto.py, ValidacionDatos.py, AlmacenCatalogo.py y ClienteHttp.py; DTO/SalaDTO.py y DTO/CriptaDTO.py; Service/ServicioPartida.py, ServicioReplay.py y ServicioGuardado.py (para ver dónde NO se verifica); UIController/LectorArgumentos.py, DTO/ConfiguracionDTO.py y main.py (códigos de salida 0, 1 y 2); Estructuras/ (lo que ya existe); y la carpeta paquete/ (qué trae hoy cada cripta).

El plan tiene que tomar y justificar estas decisiones (en research.md, cada una con la alternativa descartada y su complejidad):

1. Contrato de datos de las llaves (entrega atrasada, era para el 9/11): el DTO de una ubicación de llave (id, sala, enemigo opcional, §4.2) y cómo se entrega la lista; el método nuevo de FuenteDatos para GET /criptas/{id}/llaves (cuenta en el presupuesto, FR-317); la validación de formato en FuenteJson; FuenteOffline leyendo las llaves del paquete y DescargadorPaquete descargándolas (FR-318), revisando si el paquete también tiene que traer costos y cazadores; la persistencia de la respuesta por versión de cripta con la validación de versión que ya existe (FR-317, FR-319); y la validación de FR-321 (sala inexistente) en Data con el esqueleto, usando ErrorDatos de Data/ValidacionDatos.py. Los errores de FR-323 ya los lanza GestorEsqueleto al cargar el esqueleto (T002 de la 001).

2. El DTO del reporte de resolubilidad para el integrante 3 (vence hoy, 13/11): sus campos exactos, para que la interfaz lo muestre sin calcular nada: veredicto (resoluble, no resoluble o no concluyó), orden de llaves, llaves no obtenibles con sus ubicaciones o «sin ubicación», frontera bloqueada (dos salas y la llave o «sin llave: no se puede abrir»), ciclos y sus llaves dependientes, el motivo de FR-322 y el mensaje si no concluyó. Solo transporta datos; campos nuevos al final con valor por defecto. Escribilo en specs/003-resolubilidad/contracts/contrato-reporte-resolubilidad.md, y el contrato de las llaves en specs/003-resolubilidad/contracts/contrato-llaves.md.

3. Dónde vive cada parte según la arquitectura de la constitución: el recorrido y el armado del reporte en Logic (no importa Data; recibe DTOs del esqueleto y de las ubicaciones); Data entrega y valida los datos; Service orquesta la verificación antes de crear partida.log solo al iniciar una partida nueva (cargar una partida y --replay no verifican, FR-301); UIController y main.py: --verificar <cripta> y --forzar, con los códigos 0, 3 y 1 (el 2 sigue siendo de argumentos). Coordinación con el integrante 3: ella agrega primero --hasta y --checkpoint-cada en ConfiguracionDTO y LectorArgumentos; los campos verificar y forzar van después de los suyos, y --verificar en el mismo grupo excluyente que --replay y --bench.

4. El recorrido incremental (§5.4, NFR-302, NFR-303): cómo guardar la frontera bloqueada agrupada por llave sin dict ni set (por ejemplo, listas por llave en un array con un índice propio de llave), de modo que al obtener una llave se reabran solo las puertas que la esperaban; cada cara por separado (FR-302); el costo no afecta; la cola del recorrido es la de Estructuras/. Con la complejidad temporal y espacial.

5. El orden determinista (FR-305, FR-306): la regla concreta de orden y desempate, y cómo ordenar sin sorted ni list.sort (con el Ordenador del equipo, si hace falta).

6. Los ciclos (FR-310): cómo detectar de forma determinista los ciclos de dependencia entre llaves no obtenibles (llave → puerta que la encierra → llave que pide esa puerta), sin repetir ciclos, y cómo ubicar las llaves dependientes inmediatamente después de su ciclo.

7. --bench (NFR-304, SC-306, SC-307): dónde va la medición y cómo se conecta con Service/ServicioBench.py; criptas sintéticas deterministas por semilla con llaves encadenadas en al menos tres tamaños, incluida la de 1 000 salas en cuadrícula con 100 llaves; la alternativa de repetir el recorrido por cada llave.

8. Historial y línea de tiempo: la verificación no cambia el estado del juego, así que no registra nada en el historial de retroceso ni en la línea de tiempo. Dejalo escrito (es el riesgo principal del plan de trabajo).

9. Pruebas: qué archivos de prueba en tests/ y que cada prueba cite su FR (Principio X).

Restricciones: constitución v1.2.0 (sin dict ni set como índice o caché; sin heapq, bisect, collections, queue ni bibliotecas de grafos; sin sorted ni list.sort en lo evaluado; copy solo en tests). No escribas código: solo plan.md, research.md, data-model.md, contracts/ y quickstart.md dentro de specs/003-resolubilidad/. No modifiques archivos de otras features ni de otros integrantes; si algo de su código tiene que cambiar, listalo en el plan como coordinación. Si el script de setup modifica algún archivo fuera de specs/003-resolubilidad (por ejemplo, un archivo de contexto del agente), decime cuál. Todo en español. Al final resumí las decisiones, qué hay que coordinar con los integrantes 1 y 3, y si quedó algún NEEDS CLARIFICATION. No hagas commit.

Seguimiento en la misma conversación (después del commit 45e959e de la spec):

La spec de la 003 cambió después de generar el plan (segunda revisión del integrante 1): FR-302 (el cierre automático es el de la cara desde la que se abre y cierra las dos caras; cada cara se rige por su llave y su estado cerrado), FR-304 y FR-322 (la puerta hacia sala_salida debe estar cerrada y llave_salida la pide la cara de la sala desde la que se entra; una puerta que pide llave_salida pero no lleva a sala_salida no cuenta), FR-313 (se muestra antes de la primera acción; sin vista solo verifica --verificar, que escribe en la salida estándar), FR-301 (--bench no verifica como paso previo a una partida) y FR-314, más la aclaración de la Sesión 2026-11-13: el integrante 1 decidió mantener el motor de la primera parte como está y registrar la diferencia en DECISIONES.md. Leé de nuevo specs/003-resolubilidad/spec.md y alineá plan.md, research.md, data-model.md, quickstart.md y los dos contratos con esos cambios. En particular: cómo decide el recorrido si se llegó a sala_salida por una cara que pide llave_salida, el texto del motivo de FR-322, el hallazgo H-1 (ya no es solo informativo: quedó decidido y lo registra el integrante 1 en DECISIONES.md) y cualquier mención del cierre automático por cara. No toques la spec ni ningún archivo fuera de specs/003-resolubilidad. Al final decime exactamente qué cambiaste en cada archivo. No hagas commit.

**Uso de la respuesta:** se usó para crear `specs/003-resolubilidad/plan.md`, `research.md`, `data-model.md`, `quickstart.md`, `contracts/contrato-llaves.md` (UbicacionLlaveDTO, `FuenteDatos.obtener_llaves`, `AlmacenLlaves`, `GestorLlaves`, validación de FR-321 y `llaves.json` en el paquete) y `contracts/contrato-reporte-resolubilidad.md` (ReporteResolubilidadDTO para el integrante 3). Decisiones: recorrido incremental por oleadas con la frontera agrupada por llave en arreglos (sin `dict`), índice propio de llaves con el `Ordenador`, caras combinadas con la regla de `Mazmorra`, puerta de salida por la cara desde la que se entra, ciclos en O(K), `--bench` en `Service/BenchResolubilidad.py` y ningún registro en el historial ni en la línea de tiempo. El seguimiento alineó el plan con la segunda revisión de la spec. Revisé con Claude el plan antes del commit.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

1. git fetch. Mostrame git log --oneline Marco..origin/derek y después hacé git merge origin/derek
   (commit de merge normal). Si hay conflictos en archivos de la feature 001, pará y mostrámelos.
2. test(001): H2-17, H2-18 y H2-19 sin skip, usando la propuesta del integrante 2
   (te paso el archivo Propuesta_pruebas_FR-122_para_Marco.md). Borrá PENDIENTE_T002.
   Agregá "Co-Authored-By: Derek" en el commit.
3. test(001): T054 (H2-9) con el cuerpo completo y sin skip, con la fuente FuenteConFichaInvalida
   de la misma propuesta (la fuente devuelve la ficha sin rango, no lanza el error).
   Cubrí los 5 puntos de T054 en tasks.md, incluido que el segundo intento no hace una solicitud nueva
   (len(fuente.lotes) y len(fuente.catalogos)) y que el mensaje ya no empieza con "Sin conexión".
4. tasks(001): marcá T002, T052 y T053 (y T038 si sigue sin marcar) en tasks.md.
Suite en verde con uv run antes de cada commit; entrada en PROMPTS_LLM.md; no hagas push.
Al final: total de pruebas, qué sigue con skip y por qué.

**Uso de la respuesta:** el merge de `origin/derek` (con T002 y T052 de Derek y T053 de Kris) entró como fast-forward, sin conflictos. Commit `7c9dfc4` (test): H2-17, H2-18 y H2-19 con el cuerpo de la propuesta de Derek (`_no_inicia` y los helpers de `tests/TestValidacionDatos.py`), sin `PENDIENTE_T002`. Commit `0c1259b` (test): `FuenteConFichaInvalida` en `tests/ayudas_terreno.py` y T054 (`test_h2_9_fr122_ficha_invalida_rechaza_entrar`) con los 5 puntos, incluido el segundo intento sin solicitudes nuevas y el mensaje sin «Sin conexión». Commit tasks(001): T002, T052 y T053 marcadas (T038 ya lo estaba). Suite: 460 OK (skipped=2) y 31/31 scripts; quedan con `skip` H3-7 (spec 003) y H3-8 (fase 7).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

1. git commit --amend en 0c1259b (es el último commit de T054? si no, usá un rebase sin -i no es posible:
   en ese caso dejalo como está y avisame) para agregar "Co-Authored-By: Derek García Herra <...>".
2. tasks(001): marcá T054. T050 todavía no (espera la confirmación del integrante 2).
3. docs: en el README, cómo correr la suite: uv run python tests/correr_pruebas.py, y en Windows
   (Git Bash o PowerShell) con PYTHONIOENCODING=utf-8. En su propio commit.
Suite en verde con uv run; no hagas push.

Después: agregá la entrada en PROMPTS_LLM.md en un commit aparte, cubriendo el amend que no se hizo,
T054 en tasks.md y el README.

**Uso de la respuesta:** el amend no se hizo: `0c1259b` ya no era el último commit (después venía `2a85717`), así que el commit de T054 quedó sin el co-autor de Derek, aunque `FuenteConFichaInvalida` sale de su propuesta. Commit `35862c8` (tasks): T054 marcada en `specs/001-terreno-cazador/tasks.md`; T050 sigue sin marcar hasta que confirme el integrante 2. Commit `2706b39` (docs): la sección «Pruebas» del `README.md` usa `uv run python tests/correr_pruebas.py` y explica que en Windows hace falta `PYTHONIOENCODING=utf-8` (Git Bash y PowerShell, las dos probadas), porque sin eso el script se cae al imprimir un carácter que la consola no puede mostrar. Suite: 460 OK (skipped=2) y 31/31 scripts antes de cada commit.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

tasks(001): marcá T050 (revisión de las pruebas de FR-122 confirmada por el integrante 2 el 13 nov:
cubre costo 0/"250"/true, caras 100 vs 250, rango ausente/null/-1/true, no inicia en esqueleto y sala
inicial, y otra sala con T052/T054). Puede ir en el mismo commit que la entrada de PROMPTS_LLM.md.
Suite en verde con uv run; no hagas push.

**Uso de la respuesta:** antes de marcar se comprobó que los casos de T050 están en `tests/TestValidacionDatos.py` (costo 0, "250" y true; caras con 100 y 250; rango ausente, null, -1 y true) y en `tests/test_terreno_cazador.py` (H2-17 a H2-19: no inicia con un error en el esqueleto ni en la sala inicial; H2-9 / T054: otra sala). T050 marcada en `specs/001-terreno-cazador/tasks.md`, en el mismo commit que esta entrada. Suite: 460 OK (skipped=2) y 31/31 scripts.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

Revisión de seguimiento, SOLO LECTURA (no modifiques nada, no hagas commit). git fetch.
Specs 002 y 003 en origin/derek, comparadas con la revisión anterior (commit ede62b8):
git diff ede62b8 origin/derek -- specs/002-niebla-ir-a specs/003-resolubilidad

1. Para cada punto de tu revisión anterior (ALTA, MEDIA, BAJA): ¿quedó resuelto, parcial o pendiente?
   Una tabla corta.
2. FR-225 de la 002: confirmá que dice "por cara" (la salida u→v se ofrece si la cara del lado de u
   se recuerda abierta), costo igualado y todas las salas contadas.
3. FR-308 nuevo de la 003 (puertas cerradas sin llave en la frontera): revisá en el código de P1
   (Logic/Mazmorra.py, motorJuego.py, _igualar_caras) y en el enunciado si una cara cerrada sin llave
   se puede abrir o no. Decime si FR-308 es correcto o si declararía no resolubles criptas que sí lo son.
4. Cualquier contradicción nueva con la 001 o entre la 002 y la 003 que hayan introducido los cambios.
Registralo en PROMPTS_LLM.md (puede ir en el próximo commit).
Salida: solo lo que falta o está mal, con archivo y línea.

**Uso de la respuesta:** revisión de solo lectura de `e1a216c` (002) y `a4782fe` (003) contra la revisión anterior. En la 002 quedaron resueltos los tres puntos ALTA y casi todos los demás; FR-225 cumple «por cara» y el costo igualado, pero no dice que todas las salas cuentan (eso va en el contrato `busqueda-rutas.md` de la 001, que todavía dice «puerta recordada abierta»). En la 003 se resolvieron las caras con llaves distintas y FR-323, pero siguen pendientes casi todos los puntos MEDIA y BAJA (SC-305, SC-307, NFR-301, FR-313, H4-1, FR-310, marcas de «decisión del grupo»). En P1 una cara cerrada sin llave nunca se abre (`motorJuego.abrir_puerta` devuelve `nada_que_abrir` y `_igualar_caras` solo le copia llave si la otra cara declara una), así que FR-302/FR-308 no declaran no resoluble una cripta resoluble; falta decir cómo se lista esa puerta en la frontera. Contradicción nueva: con llaves distintas por cara y cierre automático, el supuesto «una puerta puede volver a abrirse con la misma llave» (FR-302) deja de valer.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

OK con 4b. Corregí specs/001-terreno-cazador/contracts/busqueda-rutas.md: "con la cara de la sala de
origen recordada abierta; ids del esqueleto completo (cantidad_salas() de la cripta)". Commit plan(001)
(el contrato es del plan), junto con la entrada pendiente de PROMPTS_LLM.md. Suite en verde, no hagas push.
Después seguí con la fase 5.

**Uso de la respuesta:** commit `7d9ed8f` (plan): la fila «Grafo del mapa conocido» del contrato `busqueda-rutas.md` dice «con la cara de la sala de origen recordada abierta; ids del esqueleto completo (`cantidad_salas()` de la cripta)», junto con la entrada de la revisión de seguimiento. Fase 5 con `/speckit.implement` (T027 a T035; los commits están en la entrada siguiente): `Logic/RutasHaciaJugador.py` (nuevo: búsqueda compartida por todos los cazadores; se rehace si cambia la sala del jugador o si se descartó; `puerta_cambio` la descarta solo si toca una sala resuelta; registra «descartar» en el historial al crearla o extenderla y en cada aviso de puerta), `Logic/Mazmorra.py` (`observador_puertas`; `abrir_puerta` y `CierrePuerta.activar` avisan con los destinos de las caras), `Logic/motorJuego.py` (`self.rutas`) y `Logic/Comportamientos.py` (`Cazador.decidir_paso` usa `motor.rutas.decidir`). Pruebas: `tests/test_rutas_equivalencia.py` (H3-1 a H3-5; 12 partidas aleatorias con puertas, cierres automáticos, muertes, velocidades y pergaminos, unas 11 000 decisiones comparadas con `paso_desde_cero`, sin diferencias; historial, con una prueba extra para abrir una puerta sin moverse y deshacer con el pergamino) y `TestDeterminismo` en `tests/test_terreno_cazador.py` (H3-6 y SC-103). Se comprobó con mutaciones que las pruebas detectan quitar el aviso de puertas o el registro en el historial. Suite: 472 OK (skipped=2) y 31/31 scripts.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

Antes de commitear, respondé:
1. ¿Qué queda registrado en HistorialRetroceso? Método, cuándo se registra y qué ve la línea de
   tiempo de la integrante 3. El acuerdo era un aviso de "descartar caché", sin copiar nada.
   Si hoy el descarte depende solo de un gancho del pergamino y no de un registro en el historial,
   decímelo antes de cambiar nada.
2. ¿observador_puertas y los avisos en abrir_puerta y CierrePuerta.activar están en la tabla
   "Cambios a código de la primera entrega" de plan.md? Si no, agregalos con su FR en un commit plan(001)
   antes del código.
3. ¿_asegurar_tamano()/reiniciar se usa ahora? Si no, quitalo.
Después commiteá agrupando por tarea (no todo en uno): suite en verde antes de cada commit,
la entrada de PROMPTS_LLM.md en el último. No hagas push.

**Uso de la respuesta:** (1) En el historial se registra solo `registrar_cambio(RutasHaciaJugador.descartar)`, que pone `valida = False` y no copia nada: al crear o extender la búsqueda en `decidir` y en cada `puerta_cambio`. El descarte no depende de un gancho del pergamino: lo hace `HistorialRetroceso.deshacer` al ejecutar esos registros. La línea de tiempo (004, research R9) re-simula con un motor aparte que tiene su propio historial vacío y no usa esos registros. (2) Las filas ya estaban en la tabla de `plan.md`; a la de `observador_puertas` le faltaba FR-114. (3) `reiniciar` sí se usa, pero el crecimiento de los arrays (`_asegurar_tamano`) nunca ocurría: `Motor` se crea siempre después de `cargar_esqueleto`. Commits: `d284475` (plan: FR-114 en la tabla; `data-model.md` y T032 sin el crecimiento), `c838ff3` (refactor: los arrays se reservan una sola vez en el constructor), `2bc38fa` (T031), `515c785` (T032), `31641c0` (T033), `1efe941` (T034), `d4b25a5` (pruebas T027 a T029) y el último con T030, T035 y estas entradas. La suite se corrió sobre lo que entraba en cada commit (lo demás guardado con `git stash`): 460 OK hasta T034, 470 con T027 a T029 y 472 al final, siempre con skipped=2 y 31/31 scripts.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

En tasks.md, en T046, agregá dos notas para DECISIONES.md:
1. Diferencia conocida entre la verificación (003 FR-304, literal de §3.5 y P1 §2.12) y el motor de P1:
   abrir_puerta activa salida_abierta con cualquier puerta que pida llave_salida. No se cambia el motor
   (no hay FR que lo pida); la diferencia va hacia el lado seguro (--forzar). Acordado con el integrante 2
   el 13 nov; la 003 lo cita.
2. Evidencia de FR-113 para research.md (D4): 12 partidas aleatorias, ~11 000 decisiones iguales a
   paso_desde_cero, reutilización > 90 %, y las pruebas de mutación (sin avisos de puerta fallan 6-7
   de 12; sin descarte por pergamino, solo la prueba fija lo detecta).
Commit tasks(001) con su entrada en PROMPTS_LLM.md. No hagas push.

**Uso de la respuesta:** se agregaron las dos notas debajo de T046 en `specs/001-terreno-cazador/tasks.md`. En la segunda, Claude señaló que la evidencia es de FR-114 (decidir igual que un cálculo desde cero), no de FR-113 (no abrir puertas), y que en `research.md` la decisión es R4 (no hay D4); la nota quedó con FR-114 y R4. En la primera se aclaró que, al 13 nov, la 003 de `origin/derek` (`f9ecaec`) todavía no cita la diferencia. Suite: 472 OK (skipped=2) y 31/31 scripts.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

Creá DECISIONES.md en la raíz (T046, adelantado), en un commit docs(001) aparte:
- Encabezado: qué es el archivo y cómo se cita el "antes" (docs/Documento_Decisiones.pdf de la primera entrega).
- Una sección por integrante y spec: "Integrante 1 — 001 terreno y cazador (§5.1, §5.2, §5.6)",
  "Integrante 2 — 002 y 003", "Integrante 3 — 004". Las de los integrantes 2 y 3 vacías, con "(pendiente)".
- En la sección del integrante 1, ya escrita, la entrada "Diferencia conocida entre la verificación y el
  motor de P1": 003 FR-304 sigue §3.5 y P1 §2.12; abrir_puerta activa salida_abierta con cualquier puerta
  que pida llave_salida; el motor no se cambia (ningún FR lo pide); la diferencia va hacia el lado seguro
  (--forzar). Acordado con el integrante 2 el 13 nov.
- Lo demás de §5.1, §5.2 y §5.6 queda como "(se completa en T046 con las mediciones de --bench)".
La nota 2 (evidencia de FR-113 para D4) sí va en tasks.md, en T046, como te pedí.
Entrada en PROMPTS_LLM.md. Suite en verde. No hagas push.

**Uso de la respuesta:** se creó `DECISIONES.md` en la raíz: encabezado con lo que pide el Principio VIII y cómo se cita el «antes» (`docs/Documento_Decisiones.pdf`); sección del integrante 1 con §5.1 «La ruta más barata del cazador», §5.2 «Rutas que dejan de ser válidas» y §5.6 «Revisión de decisiones de la primera parte» (títulos del enunciado) como «(se completa en T046 con las mediciones de --bench)», y la entrada «Diferencia conocida entre la verificación y el motor de P1». En esa entrada se acotó «lado seguro» a esta regla: si la verificación dice resoluble, el motor también deja ganar; lo contrario no, y para eso está `--forzar`. Las secciones de los integrantes 2 y 3 quedaron «(pendiente)». La nota 2 ya estaba en T046 de `tasks.md` (commit `c7bd816`), escrita con FR-114 y R4. Suite: 472 OK (skipped=2) y 31/31 scripts.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code (consulta por el puente, solo lectura)

Prueba del puente (solo lectura). Lee specs/001-terreno-cazador/tasks.md y decime en 3 lineas: que tareas de la fase 5 quedan sin marcar y si existe el commit de ajustes plan(001) de las fases 1 a 4 (buscalo en PROMPTS_LLM.md, no tenes git).

**Uso de la respuesta:** consulta `1a1d60173f0` (11:43), respuesta en `.claude-bridge/outbox/1a1d60173f0.txt`. Confirmó que en ese momento faltaban las 9 tareas de la fase 5 (T027 a T035). No pudo confirmar desde `PROMPTS_LLM.md` el commit `plan(001)` de ajustes de las fases 1 a 4, porque la entrada correspondiente no da título ni hash y la consulta no tenía `git`. Sirvió para probar el puente y para decidir seguir con la fase 5. No modificó nada.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code (consulta por el puente, solo lectura)

Revision de seguimiento, SOLO LECTURA (no modifiques nada). Hace git fetch.
Specs 002 y 003 en origin/derek comparadas con la revision anterior (commit ede62b8):
git diff ede62b8 origin/derek -- specs/002-niebla-ir-a specs/003-resolubilidad

1. Para cada punto de la revision anterior (ALTA, MEDIA, BAJA): resuelto, parcial o pendiente. Tabla corta.
2. FR-225 de la 002: confirma que dice por cara (la salida u->v se ofrece si la cara del lado de u se recuerda abierta), costo igualado y todas las salas contadas.
3. FR-308 nuevo de la 003 (puertas cerradas sin llave en la frontera): revisa en el codigo de P1 (Logic/Mazmorra.py, Logic/motorJuego.py, _igualar_caras) y en el enunciado si una cara cerrada sin llave se puede abrir o no. Decime si FR-308 es correcto o si declararia no resolubles criptas que si lo son.
4. Contradicciones nuevas con la 001 o entre la 002 y la 003 introducidas por los cambios.
Salida: solo lo que falta o esta mal, con archivo y linea.

**Uso de la respuesta:** consulta `1a1d6061b41` (11:51), respuesta en `.claude-bridge/outbox/1a1d6061b41.txt`. Revisó la 003 en `f9ecaec`, más nueva que la de la revisión hecha en esta sesión. Casi todos los puntos de la revisión anterior quedaron resueltos. En la 002 siguen parciales NFR-251 sin «decisión del grupo», una línea cortada en FR-225 y la numeración de la tabla de escenarios adicionales. En la 003 siguen parciales el código 1 de FR-321 sin escenario y FR-313. FR-225 dice «por cara» y costo igualado; «todas las salas» es del contrato de la 001 (ya corregido en `7d9ed8f`). FR-308 es correcto: en P1 una cara cerrada sin llave nunca se abre. Señaló que FR-304 y FR-322 pueden declarar no resoluble una cripta que P1 deja ganar, porque `abrir_puerta` activa `salida_abierta` con cualquier puerta que pida `llave_salida`. Eso llevó a la nota de T046 (`c7bd816`) y a la entrada de `DECISIONES.md` (`ded35aa`). Contradicciones nuevas: el motivo de que el cierre automático no bloquee y el «cierre automático por cara» de FR-302, la 002 corta frente a la 003 en caras con la misma llave, la referencia «003 H4-4» y el «5 ms» de NFR-250. Se le pasan al integrante 2. No modificó nada (3 acciones bloqueadas por permisos).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code (consulta por el puente, solo lectura)

Revision cruzada del PLAN de la spec 003 (integrante 2), SOLO LECTURA. Hace git fetch y lee con git show origin/derek:specs/003-resolubilidad/<archivo> (plan.md, research.md, data-model.md, contracts/, tasks.md si existe).
Revisa contra la constitucion v1.2.0 (.specify/memory/constitution.md) y la spec 003:
1. Principio I (capas): en que capa queda la verificacion y quien la llama. Data nunca llama a Logic, Logic nunca llama a Data ni a Service. El plan dice que combina las caras con una Mazmorra aparte para usar _igualar_caras: confirma desde que capa se construye esa Mazmorra y si eso respeta las capas.
2. Usar _igualar_caras (metodo privado de Mazmorra) desde otro modulo: se hace por la API publica (cargar_esqueleto) o llamando al privado? Si cambia codigo de P1, debe estar en la tabla de cambios a P1 con su FR.
3. Principio II: estructuras prohibidas (dict, set, heapq, bisect, collections, copy, sorted/list.sort en ordenamientos evaluados). Si usa un recorrido o cola, que sea propia o reutilice Estructuras/ de la 001.
4. Regla de la salida por cara: una cara cuenta si lleva a sala_salida, esta cerrada y su llave es llave_salida. Coherencia con FR-304 y FR-322 de la spec y con Logic/Mazmorra.py (abrir_puerta, salida_abierta).
5. Coherencia con la 001: errores de FR-122 al cargar el esqueleto antes de verificar; no usa costos ni cazadores (003 FR-302, 001 H3-7); determinismo.
6. Mediciones de --bench planificadas para cada decision (Principio VIII) y cripta sintetica de 1000 salas y 100 llaves.
7. Que cada FR de la spec tenga cobertura en el plan; reglas nuevas que el plan agregue y no esten en la spec (Principio IX).
Salida: ALTA/MEDIA/BAJA con archivo y linea, y al principio que esta bien.

**Uso de la respuesta:** consulta `1a1d642ea8b` (12:58), respuesta en `.claude-bridge/outbox/1a1d642ea8b.txt`. Sin hallazgos ALTA. Lo que está bien: capas (la `Mazmorra` aparte se crea en Logic), `_igualar_caras` usado por la API pública (`cargar_esqueleto`) sin tocar `Logic/Mazmorra.py`, estructuras permitidas, regla de la salida por cara coherente con FR-304, FR-322 y el motor (la diferencia ya está en `DECISIONES.md`), coherencia con 001 FR-122, mediciones B1 a B4 y cobertura de FR-301 a FR-323. MEDIA: M1, la elección de una sola puerta por llave puede dejar fuera de los ciclos señalados una llave que sí está en un ciclo (FR-310); M2, la variante no resoluble del generador del bench produce K/2 ciclos de una llave en vez de un ciclo con una cadena de dependientes; M3, un segundo `if config.offline` en `ServicioResolubilidad`. Además, 8 puntos BAJA (cita de la constitución, la alternativa ingenua en Service, mediciones de R3 y R4, reglas que no están en la spec, `ErrorPartidaNoIniciada` en dos lugares, FR-319, recursión y duración de B2). Se le pasan al integrante 2. No modificó nada (4 acciones bloqueadas por permisos).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

Registrá en PROMPTS_LLM.md las tres consultas hechas por el puente (solo lectura):
1a1d60173f0 (estado de la fase 5), 1a1d6061b41 (seguimiento de las specs 002/003) y
1a1d642ea8b (revisión del plan de la 003). Las respuestas están en C:\Users\Eli\.claude-bridge\outbox\.
Commit docs con la entrada; no hagas push.

**Uso de la respuesta:** se agregaron las tres entradas anteriores. El texto de cada consulta se tomó del primer mensaje de su sesión (`.claude-bridge/sessions/<id>` da el id de la sesión de Claude Code) y el resumen, de su respuesta en `outbox`. Commit docs.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude (Claude Code)

Edita SOLO specs/004-linea-tiempo/spec.md y su checklist si aplica. Sin estructuras, clases ni módulos. Agrega el escenario H3-6 (FR-413, FR-419, FR-424): el jugador suelta un pergamino de retroceso en la acción 4, usa otro pergamino para revertir esa acción, y después recoge el pergamino que sigue en el suelo de la sala; cuando consulta el instante actual y los instantes posteriores, el resumen coincide con el de la partida viva (el pergamino soltado quedó fuera de la reversión, tanto en el inventario como en el suelo). Agrégalo a la tabla de trazabilidad. Verifica referencias y dime qué cambiaste.

**Uso de la respuesta:** Se agregó el escenario H3-6 (pergamino soltado y vuelto a recoger tras revertir).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude (Claude Code)

Edita SOLO specs/004-linea-tiempo/plan.md, research.md, data-model.md, quickstart.md, contracts/contrato-linea-tiempo.md y tasks.md. No cambies spec.md ni escribas código.

1.Cambia el diseño del pergamino (hallazgos C1 y E1 del analyze). Se elimina el marcador de pergamino (quitados/agregados). En su lugar, después de usar un pergamino, la línea quita la última acción, quita los puntos de control con más de c acciones, y toma un punto de control NUEVO en la posición c copiando el estado vivo con PartidaGuardada.guardar, reemplazando el que hubiera en c. Esa copia ya incluye inventario, suelo de las salas, azar y todo lo demás tal como quedó (en el motor, recoger y soltar un pergamino no se registran en el historial ni en el inventario ni en el suelo). Explica en research.md (R4) por qué es más simple y exacta que los marcadores, y que las consultas de instantes anteriores a c usan los puntos anteriores, que reflejan lo vivido en ese momento.
2. Quita MarcadorPergamino y MarcadorPergaminoDTO del modelo y del contrato (también del bloque binario). La línea guardada lleva k, acciones, puntos, cargas y fichas. Mantén el campo linea y la versión 2. El contrato lo lee el integrante 2 (Derek): déjalo completo y claro.
3. Tareas: T028 pasa a retroceder_una(estado_guardado) (quita la última acción y los puntos posteriores, y agrega o reemplaza el punto en c); T030 toma el estado con PartidaGuardada.guardar tras detectar −1 y llama a retroceder_una; T031 desaparece (el reconstructor no aplica marcadores); T034 pasa a ser «reemplazar el punto en c y verificar H3-5 y H3-6»; T010 quita el DTO de marcador. T033 incluye H3-5 y H3-6 sin skip. T007: la regla pasa a «nunca hay más de K acciones entre dos puntos consecutivos» (los puntos tras un pergamino pueden estar más cerca).
4. E1: M6 y T060 miden el recorte más la copia del punto tras el pergamino, con historias de 100 a 5 000 acciones.
5. Ajustes de texto: E2 (todo camino que ejecute acciones —comando manual, «ir a» de la spec 002, replay— usa ServicioLineaTiempo.ejecutar: anótalo en H-4 y en T053 de la 004); E3 (T023: si el estado trae el mapa conocido, el resumen lo copia); Q1 (quickstart §3 incluye H3-5 y H3-6); T1 (agrega FR a T037, T041, T046, T047, T050, T063 y T064 según tu tabla de cobertura); O1 (ya no aplica si T030/T034 cambian: revisa); I1 (en el plan, el dueño de motorJuego.py es «Integrante 3 (revisa Marco)»).
6. Agrega una tarea con prueba: un escenario con un cazador comprueba que el estado reconstruido por la línea coincide con el de la partida viva (FR-419, FR-114); la búsqueda compartida del Motor aparte arranca vacía y decide igual que desde cero.
7. DECISIONES.md ya existe (lo creó el integrante 1) con una sección «Integrante 3 — 004» vacía: T063 y T064 la completan; ajusta T063 para decir «completar» y no «crear».
8. ConfiguracionDTO: el orden de campos es checkpoint_cada y después hasta; los de la 003 (verificar y forzar, del integrante 2) van detrás.
9. ContextoPartida y ControladorBackend: la 004 agrega un campo y métodos al final con valor por defecto; la 003 también (resolubilidad, verificar). Anota que quien sube primero, el otro hace merge antes. --replay y --replay … --hasta no verifican la resolubilidad (FR-301 de la 003).
10. «ir a» registra la orden como comentario «# ir a <sala>» en partida.log (formato acordado con el integrante 2). Anota que BitacoraReplayIO.leer debe ignorar esas líneas (tarea del integrante 2, spec 002) y que --replay … --hasta depende de ello. Muestra las líneas cambiadas y dime si algo de lo anterior no se pudo aplicar.

**Uso de la respuesta:** Se cambió el diseño del pergamino a un punto de control nuevo tras cada uso y se ajustaron el contrato y las tareas.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude (Claude Code)

Edita SOLO tu sección de «ir a» en specs/002-niebla-ir-a/spec.md (FR-250 a FR-299). No modifiques los FR-201 a FR-249.

1. FR-252 y donde corresponda: cambia «puerta recordada abierta» por «salida recordada abierta», el término de Convenciones (el mapa recuerda cada cara por separado: una salida cuenta como recordada abierta solo si se recuerda abierta la cara de la sala de la que sale; FR-208, FR-225, escenario H2-6).
2. NFR-251: márcalo como decisión del grupo.
3. NFR-250 y SC-252: cita que el «5 ms» sale de la tabla de §6.1 del enunciado.
4. Actualiza la línea de Estado (línea 7) y el párrafo «Reparto de la numeración» para decir que «ir a» (FR-250 a FR-264, historias 6 y 7) ya está escrita por el integrante 3. No cambies ningún otro requisito ni escenario. Dime qué líneas cambiaste.

**Uso de la respuesta:** Se ajustó la sección de «ir a» (salida recordada abierta, NFR-251, cita de §6.1) y su estado.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude (Claude Code)

/speckit-implement Ejecuta SOLO las Fases 1 y 2 de specs/004-linea-tiempo/tasks.md (ya actualizado: sin marcador de pergamino), en este orden: T001, T005, T006, T007, T008, T009, T010 y T069. T002, T003 y T004 son del integrante 2 («Coordinar»): no las implementes. Reglas: lee la constitución. Pruebas primero: escribe cada prueba, comprueba que falla y luego implementa hasta que pase. Todo código nuevo con type hints y docstring breve. Sin copy, bisect, heapq, collections, dict ni set como índice, ni sorted(). Logic no importa Data ni Service; Estructuras no importa ninguna capa. No modifiques archivos de otros integrantes ni de la primera entrega, salvo DTO/ConfiguracionDTO.py (T069: la constante CHECKPOINT_POR_DEFECTO y el campo checkpoint_cada, al final y con valor por defecto). Marca con [X] en tasks.md solo las tareas que completes. Al terminar la fase 2 corre python tests/correr_pruebas.py (en Windows, con PYTHONIOENCODING=utf-8) y reporta cuántas pasan. Haz un commit por fase: «feat(004): ayudantes de prueba» y «feat(004): búsqueda binaria, línea de tiempo en Lógica y DTOs». Para y reporta antes de la Fase 3.

**Uso de la respuesta:** Se implementaron las fases 1 y 2 de la spec 004 (búsqueda binaria, línea de tiempo en Lógica y DTOs).

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude (Claude Code)

/speckit-implement Ejecuta SOLO la lectura de argumentos de T037 y T050 de specs/004-linea-tiempo/tasks.md; el cableado a los servicios queda para después. No marques T037 ni T050 como completas.

1. DTO/ConfiguracionDTO.py: después de checkpoint_cada (T069) agrega el campo hasta: int | None = None, al final y con valor por defecto (el integrante 2 agregará verificar y forzar detrás).
2. UIController/LectorArgumentos.py: agrega --checkpoint-cada (entero ≥ 1) y --hasta (entero ≥ 0). --hasta solo se acepta junto con --replay; sin valor, con un valor que no es entero o negativo, o sin --replay, es un error de uso (código 2, igual que las demás banderas inválidas). --replay sin --hasta sigue reproduciendo la partida completa, como en la primera parte. Un --checkpoint-cada inválido también es error de uso (código 2).
3. Pruebas en un archivo nuevo (por ejemplo tests/test_banderas_linea_tiempo.py), citando FR-410 y FR-415; no modifiques los archivos de prueba del integrante 2. Reglas: pruebas primero, type hints y docstring en todo lo nuevo, solo bibliotecas permitidas, sin tocar nada más. Corre python tests/correr_pruebas.py y reporta. Un solo commit: «feat(004): banderas --checkpoint-cada y --hasta (lectura de argumentos)». No hagas push: lo hago yo al revisar el reporte.

**Uso de la respuesta:** Se agregaron --checkpoint-cada y --hasta (campos y lectura de argumentos) para que Derek agregue sus banderas detrás.

-----------------------------------------------------------------------------------------------------------------------

**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code (consulta por el puente, solo lectura)

Revision de codigo, SOLO LECTURA. Hace git fetch. Metodo nuevo Motor.avanzar_hasta(t) de la integrante 3 en origin/kris (Logic/motorJuego.py, T012) y sus pruebas tests/test_linea_tiempo_motor.py. Usa git show origin/kris:<archivo>.
Responde con evidencia de codigo (archivo:linea):
1. ColaEventos.ver_siguiente: descarta los eventos cancelados del tope igual que obtener_siguiente? Si devolviera un cancelado, el metodo compararia el tiempo del cancelado y despues obtener_siguiente sacaria OTRO evento distinto al que se activa (el codigo usa la variable evento de ver_siguiente, no lo que devuelve obtener_siguiente). Decime si ese caso puede pasar.
2. Compara con avanzar_hasta_jugador (P1): el manejo del evento del jugador (Evento_pendiente = None, reloj, retorno) es igual? Alguna diferencia de comportamiento?
3. El Motor aparte de la linea de tiempo: tiene historial None? RutasHaciaJugador._registrar_descarte y Mazmorra.observador_puertas (de origin/Marco) funcionan si el historial es None, o fallarian con un cazador?
4. Orden de eventos con el mismo tiempo: respeta el desempate por secuencia de la cola?
5. Las tres precisiones de FR-402: los cancelados no cuentan, si la partida termino en t el estado es el final, y no hay eventos con retraso 0.
Salida: lo que esta bien y lo que hay que cambiar, con propuesta minima.

**Uso de la respuesta:** consulta `1a1d6e7281b` (15:54), respuesta en `.claude-bridge/outbox/1a1d6e7281b.txt`. No se pudo revisar el método: a esa hora `origin/kris` (`d743186`) no tenía `avanzar_hasta` ni `tests/test_linea_tiempo_motor.py`, y T011 y T012 de la integrante 3 seguían sin marcar. Revisó el código del que va a depender: `ver_siguiente` descarta los cancelados igual que `obtener_siguiente`, así que el caso de la pregunta 1 no puede pasar (igual propone usar lo que devuelve `obtener_siguiente`); el método nuevo debe hacer lo mismo que `avanzar_hasta_jugador` al llegar el turno del jugador, incluido `_cerrar_intervalo()`; el historial del motor nunca es `None` (`RutasHaciaJugador` y el aviso de puertas lo comprueban, pero el rearme de trampas y el cierre de puertas de `Logic/Mazmorra.py` no, así que el motor aparte no debe ponerlo en `None`); el desempate por secuencia se respeta si los eventos se sacan uno por uno. Sobre FR-402 señaló que la suposición «no hay eventos con retraso 0» no se cumple del todo: `SalidaDTO.cierre_automatico` y `ObjetoDTO.duracion` no se validan como mayores que 0. Dejó una propuesta mínima de `avanzar_hasta` y una prueba más (cancelado en la raíz con tiempo ≤ `t` seguido de uno válido con tiempo > `t`). Se le pasa a la integrante 3 para comparar cuando suba el código; lo de la validación de retrasos, al integrante 2 (Data). No modificó nada (3 acciones bloqueadas por permisos).

-----------------------------------------------------------------------------------------------------------------------

**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

/speckit.implement Fase 7 de specs/001-terreno-cazador/tasks.md (T042 a T051).

Primero registrá en PROMPTS_LLM.md la consulta del puente 1a1d6e7281b (revisión de avanzar_hasta de la
integrante 3; respuesta en C:\Users\Eli\.claude-bridge\outbox\1a1d6e7281b.txt).

Bench (Logic/BenchRutas.py, corre sin vista, Principio V):
- Las mediciones planificadas en plan.md y research.md: un cazador frente a muchos, rango pequeño (200)
  frente a grande, búsqueda compartida frente a individual, reutilizar frente a recalcular con puertas
  estables e inestables, cuadrícula de 1000 salas con 30 cazadores (NFR-101, SC-104), SC-105 (10× la
  cripta no más que duplica el tiempo de decisión) y la agenda de eventos con la carga nueva (§5.6).
- Usá _cuadricula_con_costos(lado, azar) y semillas fijas: los resultados deben ser reproducibles.
- Quitá el skip de H3-8 cuando --bench exista.

Documentación:
- research.md: cada decisión con su medición y si cambió respecto al plan. En R4 va la evidencia de
  FR-114 anotada en T046 (12 partidas, ~11 000 decisiones, reutilización > 90 %, pruebas de mutación).
- DECISIONES.md: completá §5.1, §5.2 y §5.6 con el antes (Documento de Decisiones de P1) y el después,
  con las cifras del bench. No toques la entrada de la diferencia verificación/motor ni las secciones
  de los integrantes 2 y 3.
- Tabla de trazabilidad del Apéndice B (T047) y el checklist de la spec: marcá solo lo que quede cubierto.
  H3-7 sigue con skip hasta que exista la 003.

Reglas: constitución v1.2.0, sin cambios a código de P1 fuera de la tabla del plan, un commit por tarea,
suite en verde con uv run, PROMPTS_LLM.md, no hagas push.
Al terminar: tabla de mediciones (con la máquina y la semilla), qué decisiones cambiaron y qué quedó abierto.

**Uso de la respuesta:** se creó `Logic/BenchRutas.py` con siete mediciones (cola de prioridad, un cazador frente a muchos, `rango`, invalidación con puertas estables e inestables, ciclo con 10, 30 y 100 cazadores en 1 024 salas, agenda con la carga nueva incluidos sus dos límites, e historial) y `BenchLogica.medir()` las incluye (T043, T044). Las mediciones con cazadores comparan cada decisión con `paso_desde_cero`, y H3-8 corre sin `skip` (T042). Dos mediciones se corrigieron después de la primera corrida. En la de `rango`, el jugador siempre en el centro daba «NO cumple» en SC-105 por los costos alrededor del centro, no por la búsqueda; ahora se promedian 400 posiciones. La agenda con costos ponía los eventos nuevos antes que los pendientes, lo que favorecía al array; ahora la carga es como la del juego. Tabla de `--bench` en `specs/001-terreno-cazador/bench-2026-11-13.txt` (Ryzen 5 3600X, `SEMILLA = 2026`). Con 30 cazadores en 1 024 salas, el peor ciclo es de 5,4 a 7,9 ms; SC-105 da 1,68 y 1,09 veces. Ninguna decisión del plan cambió; solo dos mediciones. Se completaron `research.md` (T046), `DECISIONES.md` §5.1, §5.2 y §5.6 (T046), la tabla del Apéndice B (T047) y el checklist (solo «X»). T048 quedó parcial (`--replay`; faltan `--hasta` y `--verificar` de las specs 004 y 003). T049: sin coincidencias nuevas. Suite: 482 OK (skipped=1, H3-7) y 32/32 scripts. Sin push.

-----------------------------------------------------------------------------------------------------------------------

**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

Antes del push:
1. research.md (R3 y la agenda): que muestren las dos mediciones de cada cambio de método (SC-105:
   jugador en el centro 2,78× y promedio de 400 posiciones 1,09×; agenda: la carga anterior y la nueva),
   con la causa y su evidencia (12 salas resueltas contra 4) y por qué la versión nueva mide mejor lo que
   pide SC-105. Que no parezca que se ajustó la medición para que pase.
2. La fila de P1 con 500 enemigos: medila en el último commit anterior a la feature 001 (usá un git
   worktree aparte, sin tocar la rama). Compará con la medición actual en la misma máquina. Si la 001 la
   empeoró, decime cuánto y por qué antes de cambiar nada. Si ya fallaba, anotalo así en DECISIONES.md.
3. plan.md: la fila de BenchLogica.medir() con 2 líneas y el motivo del import dentro de la función.
Commits aparte, suite en verde con uv run, PROMPTS_LLM.md, no hagas push.

**Uso de la respuesta:** (1) En `research.md`, R3 y R6 muestran las dos mediciones de cada cambio de método, con la causa y la evidencia. En R3, el tiempo por sala resuelta es de 3,6 a 4,4 µs con los dos métodos, así que el 2,78× venía de las 12 salas resueltas contra 4. El método nuevo empeora la razón de 100 a 1 024 salas (de 0,76 a 1,68) por los bordes de la cuadrícula chica. En la agenda, con la carga anterior y 10 000 eventos, el array solo corría el 0,5 % de los pendientes (46) por evento; con la nueva corre el 69 % (6 926). Con las dos cargas gana el montículo. (2) La fila de 500 enemigos se midió en `83d15c5` (último commit anterior a la 001) con un `git worktree` aparte, ya borrado. Sola da lo mismo en los dos árboles (peor 11,7 a 16,2 ms antes y 12,3 a 17,0 ms ahora). En el `--bench` completo, antes dio 17,4, 20,7 y 16,5 ms y ahora 24,3, 25,0 y 24,0 ms. Con el mismo `BenchDatos` antes, el `Logic` de antes y el de ahora dan lo mismo, así que la diferencia no viene de la 001. El peor ciclo es un ciclo normal más una pasada de generación 2 del recolector de basura (10 a 20 ms); sin el recolector baja a 7 a 12 ms. Ya fallaba antes de la 001, y quedó anotado así en `DECISIONES.md` §5.6. (3) La fila de `BenchLogica.medir()` del `plan.md` ahora dice 2 líneas y explica el import circular. Suite: 482 OK (skipped=1) y 32/32 scripts. Sin push.

-----------------------------------------------------------------------------------------------------------------------

**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code (spec-kit)

/speckit-analyze

**Uso de la respuesta:** análisis de solo lectura de `specs/001-terreno-cazador` después de la fase 7. Cubre las 54 tareas y los 32 requisitos (23 FR, 3 NFR y 6 SC), todos con al menos una tarea, y la constitución v1.2.0. Hallazgos:
- C1 (Principio IX): la tabla del Apéndice B nombraba archivos de prueba (módulos), un error introducido en T047.
- C2 (Principio X): H3-7 tiene su prueba con `skip` hasta que exista `--verificar` (spec 003).
- G1: T048 cubre solo `--replay`, aunque el quickstart §6 prometía también `--hasta` y `--verificar`.
- G2: faltan las pruebas de interfaz de H4 (T041, integrante 3).
- I1: el plan decía «cerca y lejos»; se midieron dos escenarios de puertas inestables.
- I2: el bench usa 1 024 salas, no 1 000.
- I3: T044 decía «una línea».
- I4: T043 no reflejaba los cambios de método de `medir_rango` y `medir_invalidacion`.
- U1: varias tareas citaban FR-105, 107, 112, 113, 120 y 123 solo dentro de nombres de prueba.

Sin duplicaciones ni ambigüedades. Lo que se aplicó está en la entrada siguiente.

-----------------------------------------------------------------------------------------------------------------------

**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

Aplicá los hallazgos del analyze, sin cambios de código:
1. spec(001): C1, quitá los nombres de archivo de la tabla del Apéndice B (spec.md:416-422).
2. plan(001): I1 (los dos escenarios de puertas inestables, remitiendo a research.md R4) e
   I2 ("1 024 salas (32 × 32), al menos 1 000").
3. tasks(001): I3 (T044 con 2 líneas), I4 (nota en T043 que remita a research.md R3 y R4) y
   U1 (citar FR-105, 107, 112, 113, 120 y 123 en el texto de T008, T018 y T019).
4. docs(001): G1, en quickstart.md §6 aclarar que hoy solo se cubre --replay; --replay … --hasta y
   --verificar llegan con las specs 004 y 003.
C2: H3-7 se queda en la 001 con su skip (es de FR-118); no la muevas.
Un commit por punto, suite en verde con uv run, registrá el analyze en PROMPTS_LLM.md, no hagas push.

**Uso de la respuesta:** se hicieron cuatro commits, sin cambios de código:
- `spec(001)` (C1): la tabla del Apéndice B solo nombra las funciones de prueba.
- `plan(001)` (I1, I2): la fila de puertas inestables describe los dos escenarios y remite a `research.md` R4. Donde el plan dice 1 000 salas ahora dice «1 024 salas (32 × 32), al menos 1 000», con una nota de que las cuadrículas son cuadradas.
- `tasks(001)` (I3, I4, U1): T044 dice 2 líneas y por qué el import va dentro de la función. T043 tiene una nota que remite a `research.md` R3 y R4. T008, T018 y T019 citan sus FR en el texto.
- `docs(001)` (G1): el quickstart §6 dice que hoy solo se cubre `--replay`.

H3-7 se queda en la 001 con su `skip` (C2). Suite: 482 OK (skipped=1) y 32/32 scripts. Sin push.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

Extendé FR-122 con dos validaciones nuevas (pedidas por el integrante 2, motivadas por la suposición
de la spec 004 de que no hay eventos con retraso 0):
1. spec(001):
   - FR-122: SalidaDTO.cierre_automatico (si viene) y ObjetoDTO.duracion deben ser enteros >= 1, sin bool.
     cierre_automatico inválido es error del esqueleto: la partida no inicia, tampoco con --forzar
     (003 FR-323). duracion inválida rechaza la ficha como el rango del cazador (la sala queda como
     contenido no disponible). Citá la suposición de la 004 como motivo.
   - EfectoFichaDTO queda fuera: convertir duraciones <= 0 en None es comportamiento de P1 y no programa eventos.
   - Escenarios nuevos H2-20 (cierre_automatico 0, -5, "10" o true: no inicia) y H2-21 (duracion inválida en
     la ficha de un objeto: la sala queda sin contenido, el error nombra ficha y campo). En la trazabilidad.
2. tasks(001): una tarea para el integrante 2 (validación en Data) y una tuya para las pruebas de H2-20 y
   H2-21, que quedan con skipTest y el motivo hasta que esté la del integrante 2.
3. Las pruebas con skip, en su propio commit.
Suite en verde con uv run, PROMPTS_LLM.md, no hagas push.

**Uso de la respuesta:** se hicieron tres commits:
- `spec(001)`: FR-122 tiene un punto nuevo con las dos validaciones y cita la suposición de la 004. Un `cierre_automatico` inválido impide iniciar, también con `--forzar` (003 FR-323). Una `duracion` inválida rechaza la ficha como un `rango` inválido: la sala queda sin contenido, o la partida no inicia si es la sala inicial. `EfectoFichaDTO` queda fuera. Se agregaron los escenarios H2-20 y H2-21, el caso borde y las dos filas de la trazabilidad.
- `tasks(001)`: T055 (integrante 2, validación en Data con `es_entero`) y T056 (integrante 1, pruebas de H2-20 y H2-21 con `skipTest` hasta T055), con sus dependencias y el grafo.
- `test(001)`: `test_h2_20_…` y `test_h2_21_…` en `tests/test_terreno_cazador.py`, y `FuenteConObjetoInvalido` en `tests/ayudas_terreno.py`. Sin el skip, las dos fallan donde falta la validación («ErrorDatos not raised» y «mensaje None»). La parte de `--forzar` de H2-20 queda para cuando exista la spec 003.

Suite: 484 OK (skipped=3: H3-7, H2-20, H2-21) y 32/32 scripts. Sin push.

-----------------------------------------------------------------------------------------------------------------------

**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

Sí: plan(001), agregá a contracts/contrato-datos.md, sección "Validación (FR-122)", las dos reglas nuevas
(cierre_automatico y ObjetoDTO.duracion, entero >= 1 sin bool; esqueleto → no inicia, también con --forzar;
ficha → rechaza la ficha, y en la sala inicial no inicia), el formato del mensaje de error (sala y dirección,
o ficha y campo, como los demás de FR-122) y que EfectoFichaDTO queda fuera. Con su entrada en PROMPTS_LLM.md.
No hagas push.

**Uso de la respuesta:** un commit `plan(001)` en `contracts/contrato-datos.md`, sección «Validación (FR-122)»:
- La tabla tiene dos filas nuevas: `cierre_automatico` de `SalidaDTO` y `duracion` de `ObjetoDTO`, válidos si vienen como entero ≥ 1 (un `bool` no cuenta), con su contexto mínimo. Un párrafo explica que los pidió el integrante 2 (T055, H2-20 y H2-21) por la suposición de la 004, que `null` o ausente sigue siendo válido y que `EfectoFichaDTO` queda fuera.
- El efecto ahora distingue tres casos: esqueleto (no inicia, tampoco con `--forzar`, 003 FR-323), ficha de la sala inicial (no inicia) y ficha de otra sala (la sala queda sin contenido).
- El mensaje usa el mismo formato que los demás de FR-122: sala y dirección, o ficha y campo, más el valor recibido.

Suite: 484 OK (skipped=3) y 32/32 scripts. Sin push.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude

Durante el día le pedí a Claude que revisara y me guiara con la coordinación de mis specs y del plan. Prompts principales, textuales:
- «Ok perfecto, antes de pasar entonces con el paso 1 de corregir la spec 003, mira lo que me dijo kristel, te adjunto tambien el .zip de la rama ella y el de marco (aunque creo que la rama de marco no hubo cambios pero revisa igual)», con el mensaje de Kristel sobre el mapa en `PartidaGuardadaDTO`, NFR-203, el marcador del pergamino, FR-217, T053/T054, «ir a» y las banderas.
- «ok, antes de hacer el paso D, marco me mando lo siguiente, analiza el txt y mensaje», con la revisión cruzada completa de Marco de las specs 002 y 003 (ALTA, MEDIA y BAJA).
- «Listo ya le mande el mensaje a kristel, te adjunto lo que me dijo claude code y el zip. pero despues de que analices eso, marco me mando esto, analiza», con la segunda revisión de Marco (FR-304 y el motor, cierre automático, caras).
- «mira la respuesta de claude code y el .zip», después de cada prompt de Claude Code (correcciones de las specs 002 y 003, plan de la 003 y su ajuste).
- «ok pero antes de seguir, todo lo que hemos hecho es correcto? hemos aplicado lo que nos ha dicho marco y kristel? podemos seguir con tranquilidad?»
- «Quiero que analices todo esto y me digas si puedo jalar lo de ambos o no. Y luego que me digas el orden de como seguir de acuerdo a esto. Te paso los .zip de sus ramas.», con los mensajes de Kristel (contrato de la 004 sin marcador, banderas en 1b53bc9, T053, FR-217) y de Marco (DECISIONES.md, revisión del plan de la 003, `cierre_automatico` y `duracion`).
- «ok antes de este paso, mira lo que me mando marco», con su confirmación de FR-122 para `cierre_automatico` y `duracion` (T055).

**Uso de la respuesta:** Claude revisó las ramas de Marco y Kristel (460 OK y 31/31 con la de Kristel), comprobó contra el código de la primera parte (`Mazmorra._igualar_caras`, `abrir_puerta`, `CierrePuerta`, `EventoPorg.__lt__`, la victoria en `motorJuego`) y contra el PDF (§3.3, §3.5, §5.3, §6.1, §7.3, Apéndice B) cada punto de las revisiones, propuso las decisiones (estado recordado por cara, excepción de FR-217, NFR-203, FR-323, la cara que pide `llave_salida`, «sin llave: no se puede abrir»), redactó los prompts para Claude Code y los mensajes para el equipo, y revisó cada resultado de Claude Code en el zip antes de cada commit (que no tocara la parte de Kristel, que no renumerara, la cobertura de los FR y la constitución). En la noche, Claude simuló el merge de las dos ramas (523 OK y 32/32), indicó el orden (primero Kristel, después Marco), preparó el `PROMPTS_LLM.md` resuelto del conflicto, comprobó contra los documentos cada punto de la revisión del plan de Marco y redactó los dos prompts de corrección de la 003 que están en la entrada siguiente. Las decisiones las tomé yo y las acordé con Marco y Kristel.

-----------------------------------------------------------------------------------------------------------------------

**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

Corrección de la spec y del plan de la feature 003-resolubilidad (integrante 2) según la revisión del plan que hizo el integrante 1 (Marco). Antes de editar, leé: .specify/memory/constitution.md; specs/003-resolubilidad/spec.md completa; specs/003-resolubilidad/plan.md, research.md, data-model.md, quickstart.md y contracts/ (los dos); DECISIONES.md de la raíz (la entrada de Marco «Diferencia conocida entre la verificación y el motor de P1», para que el texto coincida); y el código real que se nombra abajo: Service/ServicioPartida.py (método fuente()), Service/ErroresServicio.py, Service/ServicioGuardado.py y Service/ServicioReplay.py (cómo definen ErrorCarga y ErrorReplay), Service/ServicioBench.py, Logic/BenchLogica.py y Logic/BenchRutas.py (cómo la 001 conecta su bench), Data/AlmacenCatalogo.py, y UIController/LectorArgumentos.py y DTO/ConfiguracionDTO.py (las banderas --checkpoint-cada y --hasta del integrante 3 ya existen, commit 1b53bc9).

Son dos entregas separadas, porque la spec se commitea antes que el plan (Principio IX): primero editás SOLO spec.md (parte A), después SOLO los archivos del plan (parte B). No escribas código. No hagas commit: los hago yo.

PARTE A — spec.md

A1. «Lado seguro» solo vale para la regla de FR-304. Hoy la spec dice «nunca aprueba una que el motor no deje ganar» en la Sesión 2026-11-13 de Clarificaciones (alrededor de la línea 111) y en el caso borde de la diferencia con el motor (alrededor de la línea 357). Eso es falso en general por el caso borde «Cierre automático en una puerta con llaves distintas por cara» (alrededor de la línea 388; Marco lo llama «punto 4a»): ahí la verificación supone que una puerta abierta sigue abierta, pero el motor la cierra en las dos caras y la cara de vuelta pide otra llave, así que la verificación puede aprobar una cripta que el motor no deja ganar. Corregí los dos lugares para que «lado seguro» quede limitado a la regla de la puerta de salida (FR-304, FR-322), y agregá a la sección «Suposiciones» ese caso como supuesto de §3.5 y decisión del grupo, diciendo explícitamente en qué dirección va la diferencia (la verificación puede decir «resoluble» y el jugador quedar encerrado) y por qué se acepta (§3.5 pide verificar con las llaves y las puertas, no simular el reloj ni los cierres). Si ese caso borde ya dice algo distinto, alinealo con esto.

A2. FR-310 y los ciclos (decisión del grupo). Aclará en FR-310 que «la puerta que bloquea» a una llave es UNA sola, elegida de forma determinista: entre las puertas por las que se llega a la zona donde está la llave, la del nivel más bajo (la que se cruzaría primero, contando puertas cerradas desde la región alcanzable) y, si empatan, la de menor sala de origen y luego menor dirección (la misma regla de FR-306). Los ciclos y las llaves dependientes se forman solo con esas puertas. Escribilo en lenguaje del dominio (sin nombrar estructuras ni clases), como decisión del grupo. Agregá como caso borde y como escenario nuevo al final de la historia 2 el ejemplo de Marco: la llave A está en una zona a la que se llega por dos puertas del mismo nivel, d1 que pide B y d2 que pide A; la llave B está detrás de una puerta que pide B. Resultado esperado: se señala el ciclo {B}, y A se lista como dependiente de B (A no aparece en un ciclo propio aunque d2 la pida, porque la puerta que la bloquea es la que elige la regla). Usá números de sala y direcciones concretos para que el desempate quede claro y que d1 gane el desempate. Ajustá la frase «Cada llave no obtenible que forma parte de un ciclo DEBE aparecer en al menos un ciclo señalado» para que «forma parte de un ciclo» se entienda con esa definición.

A3. FR-309 y las ubicaciones repetidas (decisión del grupo): si una llave tiene dos o más ubicaciones idénticas (misma sala y misma instancia de enemigo, o las dos sin enemigo), el reporte la indica una sola vez. Las ubicaciones distintas se siguen listando todas en orden determinista. Agregalo a FR-309, como caso borde y a un escenario que ya trate varias ubicaciones (o uno nuevo si no hay).

A4. --forzar con otros modos (decisión del grupo): con --replay, con --bench o al cargar una partida guardada, --forzar no tiene efecto (esos modos no verifican, FR-301), igual que con --verificar (H3-9): el resultado y el código de salida son los mismos que sin --forzar, y no es un error de argumentos. Agregalo a FR-312 o FR-314 y a los casos borde, junto al de --verificar con --forzar.

A5. Cripta inexistente (decisión del grupo): --verificar con una cripta que no existe (el API responde que no existe o el paquete local no la trae con --offline) termina con código 1 (la verificación no concluyó), con un mensaje con contexto, sin caerse. --forzar no cambia eso, porque sin esqueleto no hay partida. Agregalo a FR-314 y a los casos borde, y comprobá que no contradice FR-320.

A6. Agregá en Clarificaciones una sesión nueva «Sesión 2026-11-13 (revisión del plan por el integrante 1)» con una pregunta y respuesta por cada punto de A1 a A5, en el mismo formato que las anteriores. Actualizá la tabla de trazabilidad si agregaste escenarios. No cambies ningún otro requisito.

PARTE B — plan.md, research.md, data-model.md, quickstart.md y contracts/

B1. «Lado seguro»: corregí plan.md (alrededor de la línea 87) y research.md (alrededor de las líneas 466 y 467) igual que en A1, y nombrá el caso del cierre automático con llaves distintas por cara como límite conocido en la otra dirección.

B2. R6 (ciclos): dejá la definición operativa citando la nueva redacción de FR-310 (decisión del grupo) y explicá por qué se descartó la otra opción de Marco (preferir, entre puertas del mismo nivel, la que pide la propia llave): solo arregla los ciclos de una llave; si d2 pidiera C y C estuviera detrás de una puerta que pide A, el problema seguiría. Agregá el ejemplo de Marco a las comprobaciones con la spec.

B3. R6 (dependientes): el cálculo de dependientes tiene que ser iterativo, sin recursión, porque con una cadena de 1 000 llaves la recursión llega al límite de Python (1 000 por defecto). Describí cómo (por ejemplo, seguir la arista guardando el camino en un array y asignar la llave del ciclo al volver por ese array) y mantené la complejidad O(K).

B4. R7 (generador no resoluble): hoy dice que desde la mitad la llave c se ubica en la columna c+1; eso genera K/2 ciclos de una llave, no «un ciclo y una cadena larga». Cambialo para que se mueva SOLO la llave de la columna de la mitad (queda detrás de su propia puerta: un ciclo de una llave), y las llaves siguientes quedan como una cadena de dependientes de ella. Revisá que B3 mida lo que dice medir.

B5. R7 (dónde vive el bench): la alternativa ingenua y las mediciones van en Logic, siguiendo el patrón de la 001 (Logic/BenchRutas.py llamado desde Logic/BenchLogica.medir(), que Service/ServicioBench.py ya usa). Mirá el código real para decidir el nombre y la conexión, y actualizá el árbol de archivos, la tabla de cambios y la trazabilidad de plan.md. Si eso obliga a tocar un archivo del integrante 1 (por ejemplo BenchLogica.py), listalo en la tabla de coordinación con el integrante 1.

B6. Principio VIII: agregá a R7 mediciones de las alternativas descartadas de R3 y R4 que se puedan medir con sentido: al menos la búsqueda lineal de ids de R3 (en vez del índice ordenado y compactado) y la frontera en una sola lista de R4 (en vez de agrupada por llave), cada una con su fila Bn, sus tamaños y qué resultado se espera. Si alguna no tiene sentido medirla, justificalo en una línea. En R3 y R4 cambiá «Medición prevista» para que nombre esas filas.

B7. Una sola condición para --offline (Marco, MEDIA): contracts/contrato-llaves.md (alrededor de las líneas 96 y 97) dice que ServicioResolubilidad vuelve a mirar config.offline para decidir si usa el almacén de llaves. Cambialo: el almacén de llaves se elige en el mismo if donde ServicioPartida.fuente() elige FuenteOffline o FuenteRed (offline → sin almacén; red → AlmacenLlaves), y ServicioResolubilidad lo recibe ya decidido, sin mirar config.offline. Actualizá plan.md, research.md y data-model.md donde corresponda, y la tabla de coordinación con el integrante 3, porque ServicioPartida es su archivo.

B8. ErrorPartidaNoIniciada: data-model.md dice que se define en Service/ServicioResolubilidad.py y plan.md lo pone en Service/ErroresServicio.py. Unificalo con el patrón que ya existe (ErrorCarga en ServicioGuardado.py, ErrorReplay en ServicioReplay.py): se define en Service/ServicioResolubilidad.py, y ErroresServicio.py solo lo importa y lo agrega a ERRORES_ESPERADOS. Comprobá que no se forma un import circular.

B9. research.md (alrededor de la línea 91): al justificar que la validación de FR-321 vive en Data, citá como precedente 001 FR-122 (la validación de costos iguales en las dos caras ya vive en Data, en GestorEsqueleto, aunque la constitución diga «Data solo conexión y formato»).

B10. Tabla de trazabilidad de plan.md: FR-319 tiene que mencionar también AlmacenCatalogo (los datos que ya persistía la primera parte), además de GestorLlaves y AlmacenLlaves. En la spec no se nombran clases: este cambio va solo en el plan.

B11. Reflejá en el plan las decisiones nuevas de la parte A: la deduplicación de ubicaciones idénticas (dónde se hace y su complejidad, en data-model.md y en el contrato del reporte), --forzar sin efecto con --replay, --bench y al cargar una partida (contrato del reporte, sección de banderas, y quickstart), y la cripta inexistente con código 1 (contrato y quickstart).

B12. Banderas del integrante 3: ya están en su commit 1b53bc9 (checkpoint_cada con valor por defecto 20 y después hasta en ConfiguracionDTO; --checkpoint-cada y --hasta en LectorArgumentos). Actualizá la sección de coordinación de plan.md para que diga que eso ya está hecho y que verificar y forzar van detrás de hasta. No cambies nada más de esa sección.

Restricciones: constitución v1.2.0. Solo editás archivos dentro de specs/003-resolubilidad/. No toques DECISIONES.md, PROMPTS_LLM.md, ni archivos de otras features o de otros integrantes; si algo de su código tiene que cambiar, va como coordinación en el plan. Todo en español. Al final: (1) la lista de archivos que cambiaste en la parte A y en la parte B por separado, (2) un resumen de cada punto A1–A6 y B1–B12 con dónde quedó, y (3) cualquier contradicción que encuentres entre la spec y el plan, o cualquier punto donde no estés seguro. No hagas commit.

Segundo prompt, en el mismo chat:

Revisé tus cambios: la parte A (spec.md) queda como está y ya la commiteé. En la parte B hay tres ajustes. Solo tocás research.md, plan.md, data-model.md, quickstart.md y contracts/ dentro de specs/003-resolubilidad/; spec.md no se toca.

1. Conexión del bench: no modifiques Logic/BenchLogica.py (es del integrante 1 y su feature 001 ya está cerrada). Logic/BenchResolubilidad.py se queda en Logic, con la alternativa ingenua y las variantes de B5 y B6, y puede seguir reutilizando _cronometrar, _mejor_y_mediana y SEMILLA de BenchLogica (importarlos no modifica ese archivo). Lo que cambia es dónde se engancha: Service/ServicioBench.py (integrante 2) agrega BenchResolubilidad.medir a su lista por defecto, después de BenchLogica.medir, igual que ya importa BenchLogica desde Logic. Comprobá que no se forma un import circular. Actualizá R7, el árbol de archivos, la tabla de cambios (ServicioBench.py MODIFICADO por el integrante 2; BenchLogica.py sin cambios y fuera de la coordinación), la trazabilidad de NFR-301 a NFR-304 y cualquier otra mención.

2. Generador con filas = 1: en R7, la prueba de que la detección es iterativa usa cripta_en_cuadricula con filas = 1 y 3 000 columnas, pero el generador pone la única entrada a sala_salida «desde la fila 1», que no existe con una sola fila. Cambiá esa prueba a filas = 2 y 3 000 columnas (6 000 salas, cadena de unas 1 500 llaves), o definí qué hace el generador con una sola fila; elegí lo más simple y dejalo escrito donde se describe el generador y en R10.

3. Tiempo de --bench: con 10 000 dientes, la lista única de B6 son unos 5·10⁷ pasos (varios segundos por repetición), y B2 y la búsqueda lineal de B5 en 10 000 salas también son cuadráticas. Fijá en R7: B6 con 100, 1 000 y 3 000 dientes (el factor de crecimiento se sigue viendo entre 100 y 1 000); en el tamaño mayor, las alternativas cuadráticas (B2, la lineal de B5 y la lista única de B6) se miden con una sola repetición y una nota que lo diga. Ajustá las tablas de plan.md y research.md que nombran esos tamaños.

No cambies nada más. Al final: la lista de archivos que tocaste, qué quedó en cada punto, y si encontraste otra mención de BenchLogica.py como archivo a modificar. No hagas commit.

**Uso de la respuesta:** dos commits en `specs/003-resolubilidad/`. `spec(003)`: «lado seguro» solo en la regla de la puerta de salida y el cierre automático con llaves distintas por cara como suposición (dirección contraria); FR-310 con una sola puerta que bloquea a cada llave (decisión del grupo) y el escenario H2-13 con el ejemplo de Marco; FR-309 sin repetir ubicaciones idénticas (H1-12); `--forzar` sin efecto con `--replay`, `--bench` y al cargar; cripta inexistente con código 1; sesión nueva de Clarificaciones. `plan(003)`: dependientes iterativos (R6), generador no resoluble con una sola llave movida y `filas ≥ 2` (R7), bench en `Logic/BenchResolubilidad.py` enganchado en `Service/ServicioBench.py` sin tocar `BenchLogica.py`, mediciones B5 y B6 de las alternativas de R3 y R4 (B6 hasta 3 000 dientes, las cuadráticas con una repetición en el tamaño mayor), una sola condición para `--offline` en `ServicioPartida.fuente()`, `ErrorPartidaNoIniciada` definido en `ServicioResolubilidad`, precedente de 001 FR-122 y FR-319 con `AlmacenCatalogo`. Revisé el resultado contra el zip antes de cada commit.

-----------------------------------------------------------------------------------------------------------------------
**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

/speckit-tasks Tareas de la feature 003-resolubilidad (integrante 2), a partir de specs/003-resolubilidad/spec.md, plan.md, research.md, data-model.md, quickstart.md y contracts/ (versión de los commits c2fb219 y del plan(003) siguiente, con la revisión del integrante 1). Usá como modelo de formato specs/004-linea-tiempo/tasks.md y specs/001-terreno-cazador/tasks.md: mismas secciones «Formato», «Reglas para todas las tareas (constitución v1.2.0)», «Responsable», dependencias, ejecución en paralelo y estrategia. Todo en español.

1. Responsable: integrante 2. Las tareas que tocan archivos de otro integrante, según la tabla de cambios y la sección «Coordinación» del plan (del integrante 3: ServicioPartida —parámetro datos=None y el if de fuente() que elige también el almacén de llaves con almacen_llaves()—, ContextoPartida, ErroresServicio —solo importar ErrorPartidaNoIniciada y agregarlo a ERRORES_ESPERADOS—, ControladorBackend y la vista; del integrante 1: lo que el plan diga, si dice algo), van marcadas «(coordinar con el integrante 3)» o «(coordinar con el integrante 1)», con el cambio exacto que se le pide, y no las implementa el integrante 2 sin su visto bueno. Logic/BenchLogica.py NO se modifica (el bench se engancha en Service/ServicioBench.py, que es del integrante 2).
2. Pruebas primero (Principio X): una prueba por escenario de la spec (H1-1 a H1-12, H2-1 a H2-13, H3-1 a H3-9 y H4-1 a H4-5) y por caso del Apéndice B, escrita antes del código, que falle primero y que cite su escenario y su FR en el nombre del método (por ejemplo test_h2_13_fr310_puerta_que_bloquea). Además, pruebas para lo que la spec decidió sin escenario: --forzar sin efecto con --replay, --bench y al cargar una partida (FR-312), --verificar con una cripta inexistente → código 1 (FR-314), y la cadena de más de 1 000 dependientes sin RecursionError (research R6/R7, cripta_en_cuadricula con filas = 2 y 3 000 columnas). Usá los archivos de prueba que define el plan.
3. Orden de la ruta de desarrollo del plan: contrato de llaves (UbicacionLlaveDTO, FuenteDatos/FuenteJson/FuenteRed/FuenteOffline, AlmacenLlaves, GestorLlaves, validación de FR-321 en Data) → Logic (GrafoLlaves con las ubicaciones idénticas una sola vez, RecorridoLlaves con la fase hacia afuera según la regla de FR-310, CiclosLlaves iterativo, VerificadorResolubilidad) → ServicioResolubilidad (con ErrorPartidaNoIniciada) → --verificar (sin vista) y --forzar con los códigos 0, 3 y 1 → bench (Logic/BenchResolubilidad.py con B1 a B6 y los generadores de cuadrícula y peine, enganchado en Service/ServicioBench.py) → documentación. Cada tarea cita los FR que atiende.
4. Banderas: --checkpoint-cada y --hasta del integrante 3 ya están en origin/derek (commit 1b53bc9). Las tareas de verificar y forzar en DTO/ConfiguracionDTO.py y UIController/LectorArgumentos.py van detrás de hasta, sin tocar las banderas de ella; --verificar en el mismo grupo excluyente que --replay y --bench. main.py: la rama --verificar sobre la versión con --hasta.
5. Avisos a los otros integrantes como tareas explícitas: al terminar --verificar (y --verificar --offline), avisar al integrante 1 para que quite el skip de H3-7 y cierre su T048 de la 001; y avisar al integrante 3 cuando esté ServicioResolubilidad y el DTO del reporte, para que muestre el reporte antes de la primera acción (FR-313).
6. Incluí una tarea para regenerar paquete/ con llaves.json (y los costos y rangos de la Parte II) cuando el API publique las criptas nuevas, avisando a los tres y en un commit propio (hallazgo H-3), y una tarea de verificación con --verificar --offline cuando el paquete esté regenerado.
7. Cierre: --bench (B1 a B6 del plan, con las alternativas cuadráticas en el tamaño mayor con una sola repetición), la sección «Resolubilidad» (§5.4) de DECISIONES.md en la sección del integrante 2 (el archivo ya existe en la raíz, con secciones por integrante), incluyendo el límite conocido del cierre automático con llaves distintas por cara (la verificación puede decir «resoluble» y el jugador quedar encerrado); correr tests/correr_pruebas.py y el replay de ejemplo sin regresiones; y registrar los prompts en PROMPTS_LLM.md (Principio XI).

Fuera de esta feature (no las incluyas como tareas de la 003, solo nombralas en una nota de dependencias si hace falta): T055 de specs/001-terreno-cazador/tasks.md (validación de cierre_automatico y duracion en Data) y T071 de specs/004-linea-tiempo/tasks.md (BitacoraReplayIO.leer ignora las líneas que empiezan con «#»).

Solo escribí specs/003-resolubilidad/tasks.md; no escribas código ni modifiques ningún otro archivo. Al final decime cuántas tareas hay por fase, cuáles son de coordinación y si algún FR, NFR, escenario o caso del Apéndice B quedó sin tarea. No hagas commit.

**Uso de la respuesta:** `specs/003-resolubilidad/tasks.md` con 69 tareas (T001 a T069) en 10 fases: preparación, contrato de llaves, historias 1 a 4, paquete de la Parte II, bench B1 a B6 y cierre. Las pruebas van primero y citan su escenario y su FR; las tareas que tocan archivos de los integrantes 1 y 3 están marcadas para coordinar; T055 de la 001 y T071 de la 004 quedan fuera de la feature. Al final hay una tabla de cobertura. Lo revisé contra la spec y el plan antes del analyze.

-----------------------------------------------------------------------------------------------------------------------

**Fecha:** Viernes 13 de noviembre 2026

**Herramienta:** Claude Code

/speckit-analyze Análisis de consistencia de la feature 003-resolubilidad (integrante 2): specs/003-resolubilidad/spec.md (commit c2fb219), plan.md, research.md, data-model.md, quickstart.md y contracts/ (commit 7e685f4), y el tasks.md nuevo (todavía sin commit). Contra la constitución .specify/memory/constitution.md v1.2.0. Es solo lectura: no modifiques ningún archivo.

Además de lo que el análisis revisa siempre (duplicados, ambigüedades, requisitos sin tareas, tareas sin requisito, contradicciones con la constitución), comprobá en particular:

1. Que cada FR-301 a FR-323, NFR-301 a NFR-304, SC-301 a SC-308, escenario (H1-1 a H1-12, H2-1 a H2-13, H3-1 a H3-9, H4-1 a H4-5) y caso del Apéndice B tenga al menos una prueba y una tarea, y que el FR que cita cada prueba en su nombre sea el que la spec asigna a ese escenario en la tabla de trazabilidad.
2. Que las pruebas vayan antes que el código que prueban en el orden de las tareas y del grafo de dependencias (Principio X), y que ninguna tarea dependa de otra posterior sin decirlo.
3. Que las tareas marcadas «(coordinar con el integrante 3)» o «(coordinar con el integrante 1)» coincidan exactamente con la tabla de cambios y la sección «Coordinación» del plan, y que ninguna tarea sin esa marca toque un archivo de otro integrante (Logic/Mazmorra.py, Logic/BenchLogica.py, Service/ServicioPartida.py, Service/ContextoPartida.py, Service/ErroresServicio.py, UIController/ControladorBackend.py, UIController/ControladorPygame.py, View/).
4. Que las decisiones de la revisión del integrante 1 estén iguales en spec, plan y tareas: «lado seguro» solo en la regla de la puerta de salida; el cierre automático con llaves distintas por cara como límite conocido; la regla de FR-310 (nivel, sala de origen, dirección; varias ubicaciones); dependientes sin recursión; ubicaciones idénticas una sola vez; --forzar sin efecto con --replay, --bench y al cargar; cripta inexistente con código 1; una sola condición para --offline en ServicioPartida.fuente(); ErrorPartidaNoIniciada definido en ServicioResolubilidad; el bench enganchado en ServicioBench sin tocar BenchLogica; generador con filas ≥ 2; B6 hasta 3 000 dientes y las cuadráticas con una sola repetición en el tamaño mayor.
5. Referencias a tareas de otras features: el tasks.md nombra T055 de la 001 y T071 de la 004, y la 003 tiene su propio T055 (la vista). Señalá cualquier lugar donde la referencia pueda confundirse.
6. T069 dice registrar los prompts «en la sección del integrante 2» de PROMPTS_LLM.md: comprobá en el archivo real si existe esa sección o si las entradas van al final en orden cronológico.
7. Comandos de las tareas (uv run, python tests/correr_pruebas.py, python -m ...): que existan y coincidan con README.md y quickstart.md.

Entregá el informe con la tabla de hallazgos (ID, categoría, severidad CRÍTICA/ALTA/MEDIA/BAJA, ubicación con archivo y línea, resumen, recomendación), la tabla de cobertura y las métricas. No propongas ni apliques ediciones: solo el informe.

**Uso de la respuesta:** informe de solo lectura: 0 hallazgos críticos, 1 alto (la salida de `--verificar` con «→» en una consola cp1252 de Windows), 8 medios y 9 bajos; cobertura del 100 % de FR, NFR, SC, escenarios y casos del Apéndice B. Comprobé cada hallazgo contra los archivos y el enunciado, y los corregí con los prompts de la entrada siguiente.

-----------------------------------------------------------------------------------------------------------------------

**Fecha:** Sábado 14 de noviembre 2026

**Herramienta:** Claude Code

Cuatro prompts en el mismo chat del analyze.

Primero:

Aplicá las correcciones del análisis, en dos partes separadas. Primero la parte A, que toca solo spec.md, porque la commiteo antes que las demás (Principio IX). Después la parte B, que toca tasks.md y, en tres detalles, plan.md, research.md y quickstart.md. No escribas código. No hagas commit. No renumeres ninguna tarea: si hace falta algo nuevo, va dentro de una tarea existente.

PARTE A — spec.md

A1 (S1). En FR-323, el paréntesis que dice qué errores de 001 FR-122 cuentan: agregá «o una salida con un cierre_automatico que no es un entero ≥ 1» (001 FR-122 lo incluye desde el commit a725e31 del integrante 1, escenario H2-20 de la 001). Revisá si otro lugar de la spec enumera esos errores (casos borde, Suposiciones, H3-8 o H4-5) y alinealo igual, sin cambiar nada más.

A2 (T1). Alineá el texto de los escenarios con la tabla de cobertura de la spec: H2-6 agrega FR-308 a sus FR citados (la puerta 4–5 con C está en la frontera bloqueada), y H4-4 agrega FR-313 (al cargar y en --replay no se muestra reporte). No cambies la tabla.

PARTE B — tasks.md (y tres detalles del plan)

B1 (U1, ALTA). En una consola de Windows con la salida redirigida (por ejemplo, en un subprocess), print del carácter «→» lanza UnicodeEncodeError con cp1252, y --verificar no debe caerse (FR-314). T050: en la rama --verificar de main.py, antes de escribir, configurar la salida estándar en UTF-8 (sys.stdout.reconfigure(encoding="utf-8") solo si la salida tiene reconfigure, porque las pruebas que capturan la salida con StringIO o redirect_stdout no lo tienen; solo en esa rama, sin cambiar los otros modos). T046: agregar test_fr314_verificar_utf8_sin_pythonioencoding, que corre --verificar en otro proceso sin PYTHONIOENCODING, con una cripta no resoluble con ciclo (el texto tiene «→»), y lee la salida como UTF-8: código 3 y el «→» intacto. Las pruebas en otro proceso (SC-303, SC-308) leen la salida como UTF-8.

B2 (I1). T069: las entradas de PROMPTS_LLM.md van al final del archivo, en orden cronológico, con el formato que ya usa el archivo (Fecha, Herramienta, el prompt textual, Uso de la respuesta y la línea de guiones). El archivo no tiene secciones por integrante. Incluí también el prompt de /speckit-tasks, el de /speckit-analyze y este.

B3 (I2). En «Fuera de esta feature», T071 de la 004: copiá su redacción. BitacoraReplayIO.leer ignora, en la sección de acciones, las líneas de comentario «# ir a <sala>», sin confundirlas con el encabezado #CRIPTA-REPLAY ni con #ACCIONES.

B4 (I3). Calificá cada número de tarea que pueda confundirse con otra feature: «T055 (vista)» para la propia; «T055 de la 001» y «T048 de la 001» para las del integrante 1 (en T051, T058 y la nota de dependencias); «T071 de la 004». Revisá el archivo completo, también el grafo y la tabla de cobertura.

B5 (O1, O3). T029 es la prueba de recursión: se escribe antes que el generador y falla primero, y T030 la hace pasar. Corregí «T030 (generador) bloquea T029» en «Entre fases» y el grafo (T028, T029 ─► T030). Alineá además el grafo con «Entre fases»: T008 bloquea T011, no T009; la historia 2 sale de la fase 3, y el servicio de las fases 3 y 4.

B6 (O2). T001 usa UbicacionLlaveDTO (ubic y FuenteConLlaves). Declarar que T001 depende de T006 y que paquete_temporal escribe el formato del contrato de llaves (no espera a T013). Reflejalo en «Entre fases» y en el grafo.

B7 (S1). En T045 agregar test_fr323_fr314_cierre_automatico_invalido_codigo_1: un esqueleto con cierre_automatico 0 → --verificar termina con código 1, con el error con contexto (sala, dirección y campo) y sin veredicto. Depende de T055 de la 001 (validación en Data del integrante 2), que se hace antes que esta feature. En T036, lo mismo al iniciar: no inicia ni con --forzar. Actualizá la tabla de cobertura y la nota de «Fuera de esta feature», que hoy dice que no hace falta prueba.

B8 (A1). NFR-301 y SC-306 piden medir «la cripta publicada más grande» cuando exista. En T062 y T063: si el paquete de la Parte II ya está regenerado (T057), Service/ServicioBench.py (integrante 2) agrega una fila que mide la verificación de la cripta con más salas del paquete. La cripta se elige por cantidad de salas, sin nombrar ids (Principio VI). Se lee con FuenteOffline y se mide con VerificadorResolubilidad (Service orquesta Data y Logic; BenchResolubilidad no lee Data). Si el paquete no trae llaves.json, la fila no se agrega y la nota lo dice. Mientras tanto vale la sintética de 1 000 salas. Agregá la prueba correspondiente a T059, con un paquete temporal, y actualizá la tabla de NFR y SC.

B9 (T1). Agregá a los nombres de las pruebas los FR de la tabla de la spec: test_h2_6_fr307_fr308_fr309_fr321_…, test_h4_4_fr301_fr313_… y test_h2_13_fr306_fr307_fr308_fr310_puerta_que_bloquea. Actualizá la tabla de cobertura de tasks.md.

B10 (T2). En T036, las dos pruebas de verificar (cripta inexistente y costo inválido) son de la historia 3: anotalo en la tarea con «(historia 3)».

B11 (C1). En T064 agregar que DECISIONES.md deje escrita la interpretación del Principio I. Comprobar que la sala de una ubicación existe (FR-321) es integridad de los datos y va en Data, con el precedente de 001 FR-122.

B12 (X2). En las Reglas o en T068, nombrar que en Windows correr_pruebas.py se corre con PYTHONIOENCODING=utf-8, como dice el README. En T052, aclarar que el paso 8 del quickstart §2 necesita red.

B13 (D1, F1, F2, en el plan). research.md R10: H1-12 queda solo en test_resolubilidad_reporte.py. En T031, aclarar en el docstring que puerta_que_encierra[s] es «la puerta que bloquea» de FR-310. plan.md, «Escala»: mencionar que la prueba de recursión usa una cripta de 6 000 salas y unas 1 500 dependientes, por encima de la escala de las mediciones.

No cambies nada más. Al final: la lista de archivos de la parte A y de la parte B por separado, qué quedó en cada punto y si encontraste algo que contradiga lo anterior. No hagas commit.

Segundo:

Tres cambios más, por las respuestas de los integrantes 1 y 3 del 14/11. Van en la parte B (tasks.md y plan.md); spec.md no se toca. No escribas código, no renumeres tareas y no hagas commit.

E1. Confirmaciones. Marcá como hechas T002 («confirmado por el integrante 3 el 14/11: el contrato del reporte de 7e685f4 queda tal cual») y T003 («confirmado por el integrante 1 el 14/11: usar Mazmorra.cargar_esqueleto y salida sobre una instancia aparte, sin motor; avisará antes de cambiar _igualar_caras o lo que hace cargar_esqueleto al combinar caras»). Usá «- [x]», como en los tasks.md de la 001 y la 004. Quitá de las dependencias y del grafo los bloqueos que ya no aplican (T002 ya no bloquea T007).

E2. Quién escribe los cambios en los archivos del integrante 3. El integrante 3 aceptó el 14/11 que el integrante 2 escriba T037 (ServicioPartida), T038 (ContextoPartida), T040 (ErroresServicio), T049 y T054 (ControladorBackend), con pruebas, sobre la versión de la rama del integrante 3. Ella los revisa antes del merge. Condiciones: ContextoPartida.resolubilidad va después de linea, los métodos nuevos de ControladorBackend van al final de la clase y quien suba segundo hace el merge. T055 (vista) sigue siendo del integrante 3. Cambiá esas cinco tareas de «Pedir…» a «Escribir… (acordado con el integrante 3 el 14/11; ella lo revisa antes del merge)», manteniendo la marca «(coordinar con el integrante 3)». Agregá al inicio de la fase 5 un paso explícito: antes de T037, hacer merge de origin/kris para trabajar sobre su versión de ServicioPartida (iniciar_partida con los grabadores y el punto 0), ContextoPartida (linea como último campo) y ControladorBackend, y correr todas las pruebas. Actualizá en el mismo sentido «Responsable», las dependencias, el grafo, la estrategia y «Commits sugeridos»: esos cambios los commitea el integrante 2 y los revisa el integrante 3. En plan.md, ajustá la tabla de cambios o la sección «Coordinación con el integrante 3» para decir quién los escribe.

E3. Dependencia de la 001 en el bench. Logic/BenchResolubilidad.py reutiliza _cronometrar, _mejor_y_mediana y SEMILLA, que son privadas de Logic/BenchLogica.py (integrante 1, feature 001). El integrante 1 confirmó el 14/11 que no les cambia el nombre ni la firma sin avisar. Dejalo escrito en plan.md («Coordinación con el integrante 1» o una sección de dependencias), en research.md R7 y en T060 de tasks.md: «dependencia de la 001: si cambia, el integrante 1 avisa antes».

Al final: los archivos que tocaste y qué quedó en cada punto. No hagas commit.

Tercero:

Decisión sobre la contradicción de B8: se queda B8 y se corrige la spec. El motivo es que el enunciado, en la tabla de §6.1, pone el límite de 200 ms de la verificación de resolubilidad sobre «la cripta publicada más grande». Si se quitara B8, ese requisito quedaría sin medir. Sigue habiendo dos partes: la A solo en spec.md y la B en los demás archivos. No escribas código, no renumeres tareas y no hagas commit.

PARTE A — spec.md

A3. En FR-301, cambiá la frase de --bench para que diga que --bench mide la verificación sobre criptas sintéticas deterministas (NFR-304) y, además, si el paquete local de --offline trae criptas con llaves.json, sobre la cripta del paquete con más salas, elegida por cantidad de salas, sin nombrar ids (Principio VI) y leída sin red. Debe seguir diciendo que no inicia partidas, no crea partida.log y no pasa por la verificación previa a una partida.

A4. En NFR-301 y SC-306, «la cripta publicada más grande» se mide así: la cripta con más salas del paquete local, leída sin red (§6.1). «Mientras no esté publicada» pasa a ser «mientras el paquete local no traiga criptas con llaves.json»; en ese caso vale la cripta sintética de 1 000 salas con 100 llaves encadenadas (decisión del grupo).

A5. Agregá en Clarificaciones una sesión «Sesión 2026-11-14 (análisis de consistencia)» con dos preguntas y respuestas:
- qué es «la cripta publicada más grande» y cómo la mide --bench (A3 y A4, con la cita de §6.1);
- que el paréntesis de FR-323 incluye cierre_automatico desde 001 FR-122 (a725e31).
No cambies nada más de la spec.

PARTE B — plan.md, research.md, data-model.md, quickstart.md, contracts/ y tasks.md

B14. Alineá con A3 y A4 todo lo que hoy diga que --bench solo mide criptas sintéticas o que no verifica una cripta publicada: research R7 (pasa de «descartado» a «medida aparte»; la generación sintética sigue siendo la base de B1 a B6), R8, la fila de --bench del contrato del reporte, quickstart §4 y la fila de Service/ServicioBench.py en la tabla de cambios de plan.md. La medición de la cripta del paquete vive en Service/ServicioBench.py (integrante 2): Service orquesta FuenteOffline, GestorEsqueleto, GestorLlaves sin almacén y VerificadorResolubilidad, y Logic/BenchResolubilidad no lee Data. Comprobá que T059, T062 y T063 de tasks.md digan lo mismo.

B15. quickstart.md §1: agregá que en Windows correr_pruebas.py se corre con PYTHONIOENCODING=utf-8, como dice el README.

B16. plan.md, «Coordinación con el integrante 3», punto 1: el contrato del reporte quedó confirmado por el integrante 3 el 14/11, sin cambios (T002).

Al final: los archivos de la parte A y de la parte B por separado, qué quedó en cada punto y si queda algún lugar que diga que --bench solo mide criptas sintéticas. No hagas commit.

Cuarto:

Última corrección, por la frase que señalaste. En la parte A, en spec.md, FR-313: cambiá «Sin vista, el único modo que verifica es `--verificar`, que escribe el resultado en la salida estándar (FR-314); `--replay` y `--bench` no verifican (FR-301).» por «Sin vista, el único modo que muestra el resultado de la verificación es `--verificar`, que lo escribe en la salida estándar (FR-314); `--replay` no verifica y `--bench` solo mide cuánto tarda la verificación, sin mostrar veredictos ni iniciar partidas (FR-301).»

En la parte B, alineá con esa frase la fila V de la tabla de la constitución en plan.md (línea 79) y quickstart.md §2 (línea 57). No toques checklists/requirements.md: queda como registro del 11/11.

No cambies nada más, no escribas código y no hagas commit. Al final: las líneas que cambiaste.

**Uso de la respuesta:** dos commits. `spec(003)`: FR-323 incluye `cierre_automatico` (001 FR-122, `a725e31`); H2-6 cita FR-308 y H4-4 cita FR-313; FR-301, NFR-301 y SC-306 dicen que `--bench` mide, además de las criptas sintéticas, la cripta con más salas del paquete local, leída sin red (§6.1: «la cripta publicada más grande»); FR-313 aclara que `--bench` solo mide el tiempo; sesión de Clarificaciones del 14/11. `tasks(003)`: `tasks.md` corregido (salida UTF-8 en `--verificar`, PROMPTS al final, referencias a tareas de otras features calificadas, orden de T029 y T030, dependencia de T001, prueba de `cierre_automatico`, fila de la cripta del paquete en `ServicioBench`, nombres de pruebas con los FR de la tabla, T002 y T003 confirmados, T037, T038, T040, T049 y T054 escritos por el integrante 2 sobre `origin/kris` y revisados por el integrante 3) y el plan alineado (dependencia de `_cronometrar`, `_mejor_y_mediana` y `SEMILLA` de la 001, quién escribe los cambios en los archivos del integrante 3, el bench y `quickstart.md`). En el tercer prompt resolví a favor del enunciado una contradicción que mi segundo pedido había creado con FR-301. Revisé cada resultado en el zip antes de los commits.

-----------------------------------------------------------------------------------------------------------------------
