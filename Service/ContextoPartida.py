"""
ContextoPartida (Servicios, Integrante 3): todo lo que está "vivo" en una partida.

ServicioPartida lo crea y se lo pasa a los demás servicios (acción del jugador, inventario, replay...).
Solo agrupa referencias; no tiene lógica. No es un DTO: guarda objetos vivos de Datos y de Lógica.

    cripta, nombre_jugador, semilla     datos con que se creó la partida
    fuente, resolvedor                  Datos: de dónde sale la información y la caché del catálogo
    esqueleto, contenido                Datos: grafo de salas y carga/precarga del contenido
    mazmorra, jugador, inventario, motor   Lógica: el juego en sí
    mensajes                            los últimos 20 mensajes (BufferCircular, §4.8)
    bitacora                            BitacoraReplayIO de esta partida, o None (por ejemplo al reproducir un replay)
    criterio_vista                      criterio de la vista del inventario: None (orden real), "peso", "valor" o "nombre"
"""
from dataclasses import dataclass

from Data.BitacoraReplayIO import BitacoraReplayIO
from Data.FuenteDatos import FuenteDatos
from Data.GestorContenido import GestorContenido
from Data.GestorEsqueleto import GestorEsqueleto
from Data.ResolvedorCatalogo import ResolvedorCatalogo
from DTO.CriptaDTO import CriptaDTO
from Estructuras.BufferCircular import BufferCircular
from Logic.Inventario import Inventario
from Logic.Mazmorra import Mazmorra
from Logic.jugador import Jugador
from Logic.motorJuego import Motor


@dataclass
class ContextoPartida:
    cripta: CriptaDTO
    nombre_jugador: str
    semilla: int
    fuente: FuenteDatos
    resolvedor: ResolvedorCatalogo
    esqueleto: GestorEsqueleto
    contenido: GestorContenido
    mazmorra: Mazmorra
    jugador: Jugador
    inventario: Inventario
    motor: Motor
    mensajes: BufferCircular
    bitacora: BitacoraReplayIO | None = None
    criterio_vista: str | None = None