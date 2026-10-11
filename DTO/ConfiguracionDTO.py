"""
ConfiguracionDTO (Integrante 2, acordado con Integrante 3): las opciones con que se arrancó el
programa, ya leídas y validadas por UIController/LectorArgumentos.py.

Servicios lo recibe y decide con él, sin leer sys.argv:
    offline     True -> FuenteOffline (lee el paquete en disco; no cuenta solicitudes)
    cache_size  tope de fichas del catálogo en memoria: ResolvedorCatalogo.crear(fuente, cache_size)
    replay      ruta del log a reproducir (--replay partida.log), o None
    bench       True -> correr las mediciones de --bench
    ayuda       True -> mostrar cómo se usa el programa y terminar

Regla de los DTOs: solo transportan datos.
"""
from dataclasses import dataclass

# Valor por defecto de --cache-size que fija el enunciado (§4.4). Una prueba verifica que coincida
# con el de Data/CacheCatalogo.py (este DTO no importa la capa de Datos).
CACHE_SIZE_POR_DEFECTO = 25


@dataclass(frozen=True)
class ConfiguracionDTO:
    offline: bool = False
    cache_size: int = CACHE_SIZE_POR_DEFECTO
    replay: str | None = None
    bench: bool = False
    ayuda: bool = False