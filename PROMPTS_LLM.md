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

**Uso de la respuesta:** se generó `tests/test_logica.py` (60 pruebas con `unittest`) para la capa `Logic/`. Las pruebas detectaron 6 errores (campo `dano` en vez de `danio` en trampas, desempaquetado de DTOs como tuplas, turno extra con poción de velocidad, salas sin esqueleto cargado y daño negativo que curaba) e imports inconsistentes. Se corrigieron con cambios mínimos.


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