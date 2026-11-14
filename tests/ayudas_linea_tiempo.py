"""
Ayudantes de prueba de la feature 004 (línea de tiempo). No es un archivo de pruebas.

- partida_de_prueba: una partida con el paquete offline y carpetas temporales (reutiliza _crear de test_servicios).
- jugar: ejecuta N acciones deterministas mirando solo el EstadoJuegoDTO (reutiliza _elegir_accion).
- resumen_vivo: el resumen del estado vivo, para compararlo con el que arma la línea de tiempo.

Para pruebas de Lógica pura se reutilizan motor_con y poner_enemigo de tests/ayudas_terreno.py.
"""
import os
import sys
from dataclasses import replace
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))

from test_servicios import ID_CRIPTA, _correr, _crear, _elegir_accion  # noqa: E402,F401  (_correr se reexporta)
from Data.FuenteOffline import FuenteOffline  # noqa: E402
from DTO.AccionDTO import AccionDTO  # noqa: E402
from DTO.ConfiguracionDTO import ConfiguracionDTO  # noqa: E402
from DTO.EstadoJuegoDTO import EstadoJuegoDTO  # noqa: E402
from Service.ArmadorEstado import ArmadorEstado  # noqa: E402
from Service.ContextoPartida import ContextoPartida  # noqa: E402
from Service.ServicioAccionJugador import ServicioAccionJugador  # noqa: E402,F401
from Service.ServicioPartida import ServicioPartida  # noqa: E402


class FuenteReforzada(FuenteOffline):
    """El paquete offline, pero con un jugador fuerte desde la cripta (vida y ataque altos).

    Por qué: con las semillas 1 a 30 el jugador de la cripta-01 muere en menos de 10 acciones (se midió
    con las acciones deterministas de `jugar`), así que ninguna semilla sirve para una partida de 200
    acciones o más. Reforzarlo DESPUÉS de iniciar la partida no vale: el punto de control 0 ya se habría
    tomado con el jugador débil. Reforzarlo en la cripta que entrega la fuente sí: `Jugador(cripta)` nace
    fuerte y la línea lo guarda así desde el punto 0."""

    VIDA = 5000
    ATAQUE = 12

    def obtener_datos_generales(self, id_cripta: str):
        cripta = super().obtener_datos_generales(id_cripta)
        return replace(cripta, jugador_vida_max=self.VIDA, jugador_ataque=self.ATAQUE)


def partida_de_prueba(carpeta: str, semilla: int = 2026, k: int | None = None,
                      reforzado: bool = True) -> tuple[ServicioPartida, ContextoPartida]:
    """Una partida nueva con el paquete offline y carpetas temporales: (servicio_partida, contexto).

    `k` se pasa como `checkpoint_cada` (sin k se usa el valor por defecto de la configuración).
    `reforzado` (por defecto sí) usa FuenteReforzada para que la partida dure cientos de acciones."""
    kwargs = {} if k is None else {"checkpoint_cada": k}
    config = ConfiguracionDTO(offline=True, cache_size=25, **kwargs)
    clase = FuenteReforzada if reforzado else FuenteOffline
    fuente = clase(str(RAIZ / "paquete"))
    partida = ServicioPartida(config, fuente=fuente, carpeta_cache=os.path.join(carpeta, "cache"),
                              carpeta_logs=os.path.join(carpeta, "logs"))
    return partida, partida.iniciar_partida(ID_CRIPTA, "Ana", semilla=semilla)


def jugar(contexto: ContextoPartida, cantidad: int, estado: EstadoJuegoDTO | None = None,
          al_decidir=None) -> EstadoJuegoDTO:
    """Hace hasta `cantidad` intentos de acción deterministas (según la semilla) y devuelve el estado final.

    Si la partida tiene línea (`contexto.linea`), pasa por ServicioLineaTiempo.ejecutar, así la línea se alimenta
    como en la partida real; si no, por ServicioAccionJugador. Se detiene
    antes si la partida termina. Las acciones rechazadas también cuentan como intento. No lee pergaminos
    (la acción `retroceder` se cambia por `esperar`: el pergamino es de la fase 4).
    `al_decidir(estado)`, si se da, se llama antes de cada intento (por ejemplo, para fotografiar el estado vivo)."""
    if getattr(contexto, "linea", None) is None:
        servicio = ServicioAccionJugador()
    else:
        from Service.ServicioLineaTiempo import ServicioLineaTiempo
        servicio = ServicioLineaTiempo()
    if estado is None:
        estado = ArmadorEstado().armar_estado(contexto)
    x = (contexto.semilla * 2654435761 + contexto.jugador.acciones * 40503 + contexto.motor.reloj) % (1 << 32)
    for _ in range(cantidad):
        if estado.terminado:
            break
        x = (x * 1103515245 + 12345) % (1 << 32)             # congruencial lineal: no usa el azar del motor
        accion = _elegir_accion(estado, x)
        if accion.tipo == "retroceder":
            accion = AccionDTO("esperar")
        if al_decidir is not None:
            al_decidir(estado)
        estado = servicio.ejecutar(contexto, accion)
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
