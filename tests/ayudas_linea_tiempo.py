"""
Ayudantes de prueba de la feature 004 (línea de tiempo). No es un archivo de pruebas.

- partida_de_prueba: una partida con el paquete offline y carpetas temporales (reutiliza _crear de test_servicios).
- jugar: ejecuta N acciones deterministas mirando solo el EstadoJuegoDTO (reutiliza _elegir_accion).
- resumen_vivo: el resumen del estado vivo, para compararlo con el que arma la línea de tiempo.

Para pruebas de Lógica pura se reutilizan motor_con y poner_enemigo de tests/ayudas_terreno.py.
"""
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))

from test_servicios import ID_CRIPTA, _correr, _crear, _elegir_accion  # noqa: E402,F401  (_correr se reexporta)
from Data.FuenteOffline import FuenteOffline  # noqa: E402
from DTO.ConfiguracionDTO import ConfiguracionDTO  # noqa: E402
from DTO.EstadoJuegoDTO import EstadoJuegoDTO  # noqa: E402
from Service.ArmadorEstado import ArmadorEstado  # noqa: E402
from Service.ContextoPartida import ContextoPartida  # noqa: E402
from Service.ServicioAccionJugador import ServicioAccionJugador  # noqa: E402
from Service.ServicioPartida import ServicioPartida  # noqa: E402


def partida_de_prueba(carpeta: str, semilla: int = 2026, k: int | None = None) -> tuple[ServicioPartida, ContextoPartida]:
    """Una partida nueva con el paquete offline y carpetas temporales: (servicio_partida, contexto).

    Si se indica k, se pasa como `checkpoint_cada` a la configuración (el campo existe desde T069);
    sin k se usa el valor por defecto de la configuración."""
    if k is None:
        partida, _servicio_acciones, contexto = _crear(carpeta, semilla=semilla)
        return partida, contexto
    config = ConfiguracionDTO(offline=True, cache_size=25, checkpoint_cada=k)
    fuente = FuenteOffline(str(RAIZ / "paquete"))
    partida = ServicioPartida(config, fuente=fuente, carpeta_cache=os.path.join(carpeta, "cache"),
                              carpeta_logs=os.path.join(carpeta, "logs"))
    return partida, partida.iniciar_partida(ID_CRIPTA, "Ana", semilla=semilla)


def jugar(contexto: ContextoPartida, cantidad: int) -> EstadoJuegoDTO:
    """Ejecuta hasta `cantidad` acciones deterministas (según la semilla) y devuelve el estado final.

    Se detiene antes si la partida termina. Las acciones rechazadas también cuentan como intento."""
    servicio = ServicioAccionJugador()
    estado = ArmadorEstado().armar_estado(contexto)
    x = contexto.semilla * 2654435761 % (1 << 32)
    for _ in range(cantidad):
        if estado.terminado:
            break
        x = (x * 1103515245 + 12345) % (1 << 32)             # congruencial lineal: no usa el azar del motor
        estado = servicio.ejecutar(contexto, _elegir_accion(estado, x))
    return estado


def resumen_vivo(contexto: ContextoPartida):
    """El resumen (ResumenHistoriaDTO) del estado vivo: sin cursor del inventario ni mensajes (FR-406).

    `reloj` es el reloj del motor e `instante_pedido` es ese mismo valor. Importa el DTO al llamarse
    porque lo crea T009, después de este archivo."""
    from DTO.ResumenHistoriaDTO import ResumenHistoriaDTO
    estado = ArmadorEstado().armar_estado(contexto)
    return ResumenHistoriaDTO(
        reloj=estado.reloj,
        sala_id=estado.sala.id,
        sala_nombre=estado.sala.nombre,
        jugador=estado.jugador,
        inventario=[objeto.id for objeto in estado.inventario.objetos],
        arma_equipada=estado.inventario.arma_equipada,
        armadura_equipada=estado.inventario.armadura_equipada,
        efectos=list(estado.efectos),
        enemigos=list(estado.enemigos),
        mapa_conocido=None,
        terminada_antes=False,
        instante_pedido=estado.reloj,
    )
