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

from test_servicios import ID_CRIPTA, ID_PERGAMINO, _correr, _crear, _elegir_accion  # noqa: E402,F401  (se reexportan)
from Data.FuenteOffline import FuenteOffline  # noqa: E402
from DTO.AccionDTO import AccionDTO  # noqa: E402
from DTO.ConfiguracionDTO import ConfiguracionDTO  # noqa: E402
from DTO.EstadoJuegoDTO import EstadoJuegoDTO  # noqa: E402
from DTO.FichaEnemigoDTO import FichaEnemigoDTO  # noqa: E402
from DTO.SalaDTO import EnemigoEnSalaDTO  # noqa: E402
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


class FuenteConCazador(FuenteReforzada):
    """Como FuenteReforzada, pero la sala 4 (Osario profundo) trae además un cazador de rango enorme.

    El paquete offline no trae ningún cazador. Este lo persigue por todo el pasillo 4-3-2-1 en cuanto el jugador
    entra a la sala 4, así que usa la búsqueda compartida de RutasHaciaJugador (T070)."""

    ID_CAZADOR = "ent_cazador_prueba"
    SALA_CAZADOR = 4

    def obtener_contenido(self, id_cripta, ids_salas):
        contenidos = super().obtener_contenido(id_cripta, ids_salas)
        for contenido in contenidos:
            if contenido.sala == self.SALA_CAZADOR:
                contenido.enemigos.append(EnemigoEnSalaDTO("e-cazador", self.ID_CAZADOR, 40))
        return contenidos

    def obtener_catalogo(self, ids):
        ids = list(ids)
        resto = [i for i in ids if i != self.ID_CAZADOR]
        fichas = super().obtener_catalogo(resto) if resto else []
        if self.ID_CAZADOR in ids:
            fichas.append(FichaEnemigoDTO(id=self.ID_CAZADOR, nombre="Cazador de prueba", vida_max=40, ataque=3,
                                          defensa=1, velocidad=100, comportamiento="cazador", suelta=[],
                                          rango=100000))
        return fichas


def dar_pergaminos(contexto: ContextoPartida, cantidad: int) -> None:
    """Pone `cantidad` pergaminos en el inventario por fuera de los servicios (como test_servicios._crear).

    Se hace al empezar: se vuelve a tomar el punto de control 0, para que la línea ya los tenga (si no, un
    estado reconstruido a partir del punto 0 no los traería)."""
    from Service.ServicioLineaTiempo import ServicioLineaTiempo
    from Service.SincronizadorUsos import SincronizadorUsos
    for _ in range(cantidad):
        contexto.inventario.recoger(contexto.resolvedor.ficha(ID_PERGAMINO))
    SincronizadorUsos().sincronizar(contexto)
    if contexto.linea is not None:
        contexto.linea.puntos.clear()
        ServicioLineaTiempo.tomar_punto(contexto)


def partida_de_prueba(carpeta: str, semilla: int = 2026, k: int | None = None,
                      reforzado: bool = True, fuente_clase=None) -> tuple[ServicioPartida, ContextoPartida]:
    """Una partida nueva con el paquete offline y carpetas temporales: (servicio_partida, contexto).

    `k` se pasa como `checkpoint_cada` (sin k se usa el valor por defecto de la configuración).
    `reforzado` (por defecto sí) usa FuenteReforzada para que la partida dure cientos de acciones;
    `fuente_clase` pone otra fuente (por ejemplo FuenteConCazador)."""
    kwargs = {} if k is None else {"checkpoint_cada": k}
    config = ConfiguracionDTO(offline=True, cache_size=25, **kwargs)
    clase = fuente_clase or (FuenteReforzada if reforzado else FuenteOffline)
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
